# Standard library imports
import asyncio
import json
import logging
import os
import sys
import threading
import time
import traceback
from collections import defaultdict
from datetime import datetime

# Third-party imports
import psutil
import requests
from quart import Quart, request, jsonify
import redis.asyncio as redis_async

# LangChain / LangGraph ecosystem
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.redis import AsyncRedisSaver

# Internal / project-specific imports
from agent_builders.chatflow_builder import build_chatflow
from config.config_setup import ChatFlowConfig
from config.setting import settings
from data.simulated_data_lt_simplified import (
    agent_data,
    knowledge,
    knowledge_main_flow,
    chatflow_design,
    global_configs,
    intentions,
)
from common.logger import setup_logger
from models.async_notification_manager import AsyncNotificationManager
from models.persistence_manager import ModelPersistenceManager

# ASGI server imports (Hypercorn)
from hypercorn.config import Config
from hypercorn.asyncio import serve

logger = setup_logger('ai_service', category='ai_service', console_output=True)

# TODO: Start the app
app = Quart(__name__)

PHP_CALLBACK_URL = settings.PHP_CALLBACK_URL  # PHP回调地址

# TODO 创建全局动态模型管理器
class DynamicModelManager:
    def __init__(self):
        self.models = {}  # {model_id: model_data}
        self.activating_model = {}
        self.model_usage = defaultdict(int)  # 模型使用计数
        self.model_last_used = {}  # 模型最后使用时间
        self.model_tasks = defaultdict(set)  # 模型关联的任务
        self.model_created_time = {}  # 🎯 记录模型创建时间
        self.lock = threading.RLock()
        self.ttl_config = {"default_ttl": 1440, "refresh_on_read": False}

        # 🎯 持久化管理器
        self.persistence_manager = ModelPersistenceManager()
        # 异步通知管理器
        self.notification_manager = AsyncNotificationManager(max_workers=5)

        # 资源配置
        self.max_models = 50
        self.max_memory_mb = 4096  # 🎯 新增：最大内存限制 2GB
        self.model_timeout = 3600
        self.cleanup_interval = 300
        self.model_memory_estimate = 100  # 🎯 每个模型预估内存占用(MB)

        # Version tracking for cancellation (per model_id)
        self._init_versions: dict[str, int] = {}
        self._init_locks: dict[str, asyncio.Lock] = {}

        # 🎯 激活队列：全局串行，同一时间只跑 1 个真正的 initialize
        self._activation_job_queue: asyncio.Queue | None = None
        self._pending_jobs: dict[str, dict] = {}  # model_id -> job
        self._queue_order: list[str] = []  # 等待中的 model_id 顺序（不含正在跑的）
        self._current_job_model_id: str | None = None
        self._queue_async_lock = None  # asyncio.Lock，在事件循环内懒创建
        # again / 作废入队后递增，worker 跳过 Queue 里残留的旧 job
        self._activation_gen: dict[str, int] = {}

    def start_cleanup_task(self):
        """启动后台清理线程"""
        async def cleanup_worker():
            while True:
                await asyncio.sleep(self.cleanup_interval)
                try:
                    # 🎯 先检查是否需要紧急清理
                    emergency_result = await self.check_and_cleanup_if_needed()
                    if emergency_result.get('cleaned', False):
                        logger.debug(f"🔄 紧急清理完成: {emergency_result}")

                    # 🎯 然后进行常规清理
                    normal_result = await self.cleanup_idle_models()  # 正常清理
                    if normal_result['removed_count'] > 0:
                        logger.debug(f"🔄 常规清理完成: 移除了 {normal_result['removed_count']} 个模型")

                except Exception as e:
                    logger.error(f"清理线程异常: {str(e)}")

        asyncio.create_task(cleanup_worker())

    def start_activation_queue_worker(self):
        """启动激活队列 worker：同一时间只执行一个 initialize_model"""
        if self._activation_job_queue is not None:
            return
        self._activation_job_queue = asyncio.Queue()
        self._queue_async_lock = asyncio.Lock()

        async def activation_worker():
            logger.info("🚀 激活队列 worker 已启动（并发=1）")
            while True:
                job = await self._activation_job_queue.get()
                model_id = job['model_id']
                should_run = False
                waiting_count = 0
                try:
                    # 与 enqueue 共用锁，避免位次/通知竞态
                    async with self._queue_async_lock:
                        # again 后 Queue 里可能残留旧 job，按 generation 丢弃
                        if job.get('gen', 0) != self._activation_gen.get(model_id, 0):
                            logger.info(f"⏭️ 跳过已作废的排队激活: {model_id} (gen={job.get('gen')})")
                        else:
                            should_run = True
                            self._current_job_model_id = model_id
                            if model_id in self._queue_order:
                                self._queue_order.remove(model_id)
                            self._pending_jobs.pop(model_id, None)

                            waiting_count = len(self._queue_order)
                            message = (
                                f"轮到您了，正在激活模型（后方还有 {waiting_count} 个等待）"
                                if waiting_count else "轮到您了，正在激活模型"
                            )
                            self._notify_php_model_activating(
                                model_id,
                                reason=message,
                                queue_position=1,
                                waiting_count=0,
                                message=message,
                            )
                            self._broadcast_queue_positions()

                    if not should_run:
                        continue

                    logger.info(f"🔄 队列开始执行激活: {model_id}，后方等待 {waiting_count}")
                    await self.initialize_model(
                        model_id,
                        job.get('config_data'),
                        job.get('task_id'),
                        job.get('expire_time'),
                    )
                except asyncio.CancelledError:
                    # initialize_model 已回调 PHP；不可让 CancelledError 杀死 worker，否则整队永久卡住
                    logger.warning(f"⚠️ 队列激活被取消: {model_id}，worker 继续消费后续任务")
                except Exception as e:
                    logger.error(f"❌ 队列激活失败 {model_id}: {str(e)}")
                finally:
                    async with self._queue_async_lock:
                        if self._current_job_model_id == model_id:
                            self._current_job_model_id = None
                        if should_run:
                            self._broadcast_queue_positions()
                    self._activation_job_queue.task_done()

        asyncio.create_task(activation_worker())

    def _get_queue_snapshot(self, model_id: str) -> tuple[int, int]:
        """返回 (queue_position, waiting_count)。position 从 1 起；waiting_count=前方人数。"""
        if self._current_job_model_id == model_id:
            return 1, 0
        try:
            idx = self._queue_order.index(model_id)
        except ValueError:
            return 0, 0
        # 有正在跑的任务时，队列第 0 个排第 2
        offset = 1 if self._current_job_model_id else 0
        position = idx + 1 + offset
        return position, position - 1

    @staticmethod
    def _queue_message(position: int, waiting_count: int, status: str = 'queued') -> str:
        if status == 'activating':
            return "正在激活模型，请稍候"
        if waiting_count <= 0:
            return "已排队，即将开始激活"
        return f"前方还有 {waiting_count} 个模型在排队，您排第 {position} 位"

    def _broadcast_queue_positions(self):
        """前方任务变化后，通知仍在排队的模型更新位次"""
        for mid in list(self._queue_order):
            position, waiting_count = self._get_queue_snapshot(mid)
            if position <= 0:
                continue
            message = self._queue_message(position, waiting_count, 'queued')
            self._notify_php_model_queued(mid, position, waiting_count, message)

    async def enqueue_initialize(self, model_id, config_data=None, task_id=None, expire_time=None) -> dict:
        """
        将激活请求入队，立即返回排队信息。
        同一 model_id 已在队列或正在激活时不重复入队，直接返回当前位次。
        """
        # 懒启动：防止 before_serving 未触发时队列不可用
        if self._activation_job_queue is None or self._queue_async_lock is None:
            with self.lock:
                if self._activation_job_queue is None or self._queue_async_lock is None:
                    self.start_activation_queue_worker()

        async with self._queue_async_lock:
            # 已激活成功（含服务重启恢复的 recovered）：直接延期/复用
            with self.lock:
                existing = self.models.get(model_id)
                if (
                    existing
                    and 'instance' in existing
                    and existing.get('status') in ('active', 'recovered')
                ):
                    if expire_time:
                        existing['expire_time'] = expire_time
                    if task_id:
                        self.model_tasks[model_id].add(task_id)
                        self.model_usage[model_id] = self.model_usage.get(model_id, 0) + 1
                    self._notify_php_model_activated(model_id)
                    return {
                        'success': True,
                        'queued': False,
                        'already_active': True,
                        'queue_position': 0,
                        'waiting_count': 0,
                        'message': f'模型 {model_id} 已激活',
                        'model_id': model_id,
                        'status': 'activated',
                    }

            # 正在执行该模型
            if self._current_job_model_id == model_id:
                message = self._queue_message(1, 0, 'activating')
                return {
                    'success': True,
                    'queued': True,
                    'queue_position': 1,
                    'waiting_count': 0,
                    'message': message,
                    'model_id': model_id,
                    'status': 'activating',
                }

            # 已在等待队列：更新配置，返回当前位次
            if model_id in self._pending_jobs:
                job = self._pending_jobs[model_id]
                job['config_data'] = config_data or job.get('config_data')
                job['task_id'] = task_id if task_id is not None else job.get('task_id')
                job['expire_time'] = expire_time if expire_time is not None else job.get('expire_time')
                position, waiting_count = self._get_queue_snapshot(model_id)
                message = self._queue_message(position, waiting_count, 'queued')
                self._notify_php_model_queued(model_id, position, waiting_count, message)
                return {
                    'success': True,
                    'queued': True,
                    'queue_position': position,
                    'waiting_count': waiting_count,
                    'message': message,
                    'model_id': model_id,
                    'status': 'queued',
                }

            # 新入队
            job = {
                'model_id': model_id,
                'config_data': config_data or {},
                'task_id': task_id,
                'expire_time': expire_time,
                'gen': self._activation_gen.get(model_id, 0),
            }
            self._pending_jobs[model_id] = job
            self._queue_order.append(model_id)
            # 锁内用 put_nowait，避免 await 让出执行权导致竞态
            self._activation_job_queue.put_nowait(job)

            position, waiting_count = self._get_queue_snapshot(model_id)
            message = self._queue_message(position, waiting_count, 'queued')
            # 队首且当前无人在跑：worker 马上会发 activating，跳过 queued 回调避免文案闪一下又被覆盖
            if not (position == 1 and self._current_job_model_id is None):
                self._notify_php_model_queued(model_id, position, waiting_count, message)
            logger.info(f"📥 模型入队: {model_id}, 位次={position}, 前方等待={waiting_count}")
            return {
                'success': True,
                'queued': True,
                'queue_position': position,
                'waiting_count': waiting_count,
                'message': message,
                'model_id': model_id,
                'status': 'queued',
            }

    @staticmethod
    def _notify_php_model_activated(model_id):
        """异步通知PHP模型激活"""
        try:
            payload = {
                'model_id': model_id,
                'status': 'activated',
                'timestamp': datetime.now().isoformat()
            }
            thread = threading.Thread(
                target=lambda: requests.post(f"{PHP_CALLBACK_URL}", json=payload, timeout=3),
                daemon=True
            )
            thread.start()
            logger.info(f"📤 异步通知PHP模型激活: {model_id}")
        except Exception as e:
            logger.error(f"❌ 异步通知PHP模型激活失败: {str(e)}")

    @staticmethod
    def _notify_php_model_activation_failed(model_id, error_msg):
        """通知PHP模型激活失败（异步，不阻塞激活队列）"""
        try:
            payload = {
                'model_id': model_id,
                'status': 'sleep',  # 回退到休眠状态
                'timestamp': datetime.now().isoformat(),
                'reason': f'activation_failed: {error_msg}'
            }
            thread = threading.Thread(
                target=lambda: requests.post(f"{PHP_CALLBACK_URL}", json=payload, timeout=3),
                daemon=True
            )
            thread.start()
            logger.info(f"📤 通知PHP模型激活失败: {model_id}, 原因: {error_msg}")
        except Exception as e:
            logger.error(f"❌ 通知PHP模型激活失败失败: {str(e)}")

    def _notify_php_model_sleep(self, model_id):
        """异步通知PHP模型休眠"""
        payload = {
            'model_id': model_id,
            'status': 'sleep',
            'timestamp': datetime.now().isoformat(),
            'reason': 'no_active_tasks_or_expired'
        }
        self.notification_manager.add_notification(
            f"{PHP_CALLBACK_URL}",
            payload,
            "model_sleep"
        )

    @staticmethod
    def notify_php_task_pause(task_id, model_id, reason):
        """异步通知PHP暂停任务"""
        try:
            payload = {
                'task_id': task_id,
                'model_id': model_id,
                'status': 'pause_task',
                'reason': reason,
                'timestamp': datetime.now().isoformat()
            }
            # 使用异步线程
            thread = threading.Thread(
                target=lambda: requests.post(f"{PHP_CALLBACK_URL}", json=payload, timeout=3),
                daemon=True
            )
            thread.start()
            logger.warning(f"📤 异步通知PHP暂停任务: {task_id}, 原因: {reason}")
        except Exception as e:
            logger.error(f"❌ 异步通知PHP暂停任务失败: {str(e)}")

    @staticmethod
    def _notify_php_model_queued(model_id, queue_position, waiting_count, message):
        """通知PHP模型已入队/位次更新"""
        try:
            payload = {
                'model_id': model_id,
                'status': 'queued',
                'queue_position': queue_position,
                'waiting_count': waiting_count,
                'message': message,
                'timestamp': datetime.now().isoformat(),
            }
            thread = threading.Thread(
                target=lambda: requests.post(f"{PHP_CALLBACK_URL}", json=payload, timeout=3),
                daemon=True
            )
            thread.start()
            logger.info(f"📤 通知PHP模型排队: {model_id}, 位次={queue_position}, 前方={waiting_count}")
        except Exception as e:
            logger.error(f"❌ 通知PHP模型排队失败: {str(e)}")

    @staticmethod
    def _notify_php_model_activating(model_id, reason, queue_position=1, waiting_count=0, message=None):
        """异步通知PHP模型正在激活（已出队开始执行）"""
        try:
            payload = {
                'model_id': model_id,
                'status': 'activating',
                'reason': reason,
                'queue_position': queue_position,
                'waiting_count': waiting_count,
                'message': message or reason,
                'timestamp': datetime.now().isoformat()
            }
            thread = threading.Thread(
                target=lambda: requests.post(f"{PHP_CALLBACK_URL}", json=payload, timeout=3),
                daemon=True
            )
            thread.start()
            logger.info(f"📤 异步通知PHP模型激活中: {model_id}")
        except Exception as e:
            logger.error(f"❌ 异步通知PHP模型激活失败: {str(e)}")

    async def recover_models_on_startup(self):
        """服务启动时恢复模型 - 简化版本"""
        logger.info("🔄 开始恢复持久化的模型...")

        # 加载模型配置
        model_configs = self.persistence_manager.load_model_configs()
        recovered_count = 0
        expired_count = 0

        for model_id, config_data in model_configs.items():
            try:
                # 检查模型是否过期
                current_time = time.time()
                expire_time = config_data.get('expire_time', 0)

                if current_time > expire_time:
                    logger.info(f"🗑️ 跳过过期模型并删除配置: {model_id}")
                    self.persistence_manager.delete_model_config(model_id)
                    expired_count += 1
                    continue

                # 重新初始化模型
                chatflow_config = self._build_chatflow_config(config_data.get('config', {}))

                redis_client = redis_async.Redis(
                    # 异步Redis
                    # get redis server url from env (for Docker) first, if not, get it from settings
                    host=os.getenv("REDIS_SERVER", settings.REDIS_SERVER),
                    password=settings.REDIS_PASSWORD,
                    port=int(settings.REDIS_PORT),
                    db=settings.REDIS_DB,  # Redis Search requires index be built on database 0
                    decode_responses=False,
                    # Let Redis reserve the binary data, instead converting it to Python strings
                    max_connections=50
                )
                redis_checkpointer = AsyncRedisSaver(redis_client=redis_client, ttl=self.ttl_config)
                await redis_checkpointer.setup()  # Async setup
                chatflow, milvus_client = await build_chatflow(chatflow_config, redis_checkpointer=redis_checkpointer)
                logger.info("✅ build_chatflow completed!")
                # 恢复模型数据
                self.models[model_id] = {
                    'instance': chatflow,
                    'config': config_data.get('config', {}),
                    'created_time': config_data.get('created_time', datetime.now()),
                    'expire_time': expire_time,
                    'memory_usage': config_data.get('memory_usage', 0),
                    'status': 'recovered',
                    'version': 0,
                }

                # 恢复使用统计（重置为0，因为服务重启）
                self.model_usage[model_id] = 0
                self.model_last_used[model_id] = config_data.get('last_used', datetime.now())
                self.model_created_time[model_id] = config_data.get('created_time', datetime.now())

                recovered_count += 1
                logger.info(f"✅ 恢复模型成功: {model_id}")

            except Exception as e:
                logger.error(f"❌ 恢复模型失败 {model_id}: {str(e)}")
                continue

        logger.info(f"🎉 模型恢复完成: 成功 {recovered_count} 个, 过期 {expired_count} 个")

    @staticmethod
    async def _safe_close_client(client):
        """Safely close a client, handling both sync and async close methods"""
        if not client:
            return
        try:
            # Prefer aclose for async clients
            if hasattr(client, 'aclose') and callable(client.aclose):
                result = client.aclose()
                if asyncio.iscoroutine(result):
                    await result
            # Fallback to close (which might also be async)
            elif hasattr(client, 'close') and callable(client.close):
                result = client.close()
                if asyncio.iscoroutine(result):
                    await result
        except Exception as e:
            # Log at debug level to avoid spam; these are best-effort cleanups
            logger.debug(f"⚠️ 关闭客户端警告: {type(client).__name__}: {e}")

    async def initialize_model(self, model_id, config_data=None, task_id=None, expire_time=None):
        """
        动态初始化模型，支持:
        - 重复请求时取消前一次请求 (version cancellation)
        - 3分钟冷却期防止频繁重初始化 (cooldown)
        - 线程安全的共享状态管理
        """
        # ============================================================
        # 🎯 STEP 0: Cooldown Check (protected by sync lock)
        # ============================================================
        with self.lock:
            # 如果请求距离上一次在3分钟内，直接报错
            now = time.time()
            if model_id in self.activating_model:
                elapsed = now - self.activating_model[model_id]
                if elapsed < 180:  # 3分钟内
                    error_msg = f"模型 {model_id} 正在激活中（已进行 {elapsed:.1f} 秒），拒绝重复激活"
                    logger.info(error_msg)
                    self._notify_php_model_activating(model_id, error_msg)
                    raise Exception(error_msg)
                else:
                    # 超时，允许重新激活，删除旧记录
                    logger.info(f"模型 {model_id} 激活超时（{elapsed:.1f} 秒），重新激活")
                    del self.activating_model[model_id]
            # 记录新激活的开始时间
            self.activating_model[model_id] = now

        # ============================================================
        # 🎯 STEP 1: Per-Model Async Lock (serialize init for this model_id)
        # ============================================================
        if model_id not in self._init_locks:
            self._init_locks[model_id] = asyncio.Lock()

        async with self._init_locks[model_id]:
            # 🎯 Increment version: newer request supersedes older
            current_version = self._init_versions.get(model_id, 0) + 1
            self._init_versions[model_id] = current_version

            # 🎯 Clean up any partial state from previous attempt
            await self._cleanup_partial_init(model_id)

            # --------------------------------------------------------
            # 🎯 STEP 2: Quick Checks (protected by sync lock)
            # --------------------------------------------------------
            with self.lock:
                # 检查是否已达模型上限
                if len(self.models) >= self.max_models:
                    # 尝试清理空闲模型
                    await self.cleanup_idle_models(force_reason='count_exceed')
                    if len(self.models) >= self.max_models:
                        error_msg = f"模型数量已达上限 {self.max_models}，无法创建新模型"
                        self._notify_php_model_activation_failed(model_id, error_msg)
                        raise Exception(error_msg)

                # 如果模型已存在，增加使用计数
                if model_id in self.models and 'instance' in self.models[model_id]:
                    self.model_usage[model_id] += 1
                    if task_id:
                        self.model_tasks[model_id].add(task_id)
                    if expire_time:
                        self.models[model_id]['expire_time'] = expire_time
                    logger.info(f"模型 {model_id} 已存在，增加使用计数: {self.model_usage[model_id]}")
                    # 通知PHP模型激活
                    self._notify_php_model_activated(model_id)
                    return True

                # 🎯 Mark as 'initializing' (temporary state)
                self.models[model_id] = {
                    'status': 'initializing',
                    'version': current_version,
                    'created_time': datetime.now(),  # ✅ Required by get_model_status()
                    'expire_time': expire_time or (time.time() + 14 * 24 * 3600),  # ✅ Safe default
                    'memory_usage': 0,  # ✅ Placeholder, won't break stats
                    'config': config_data or {},  # ✅ Already available at this point
                }

            # --------------------------------------------------------
            # 🎯 STEP 3: Heavy Work (NO LOCKS HELD - allows concurrency)
            # --------------------------------------------------------
            redis_client = milvus_client = None
            try:
                logger.info(f"开始动态初始化模型: {model_id}(v{current_version})")

                # 构建配置
                chatflow_config = self._build_chatflow_config(config_data)

                redis_client = redis_async.Redis(  # 异步Redis
                    host=settings.REDIS_SERVER,
                    password=settings.REDIS_PASSWORD,
                    port=int(settings.REDIS_PORT),
                    db=settings.REDIS_DB,  # Redis Search requires index be built on database 0
                    decode_responses=False,
                    # Let Redis reserve the binary data, instead converting it to Python strings
                    max_connections=50
                )
                redis_checkpointer = AsyncRedisSaver(redis_client=redis_client, ttl=self.ttl_config)
                await redis_checkpointer.setup()  # Async setup

                chatflow, milvus_client = await build_chatflow(chatflow_config, redis_checkpointer=redis_checkpointer)

                # --------------------------------------------------------
                # 🎯 STEP 4: Post-Execution Version Check (cancellation point)
                # --------------------------------------------------------
                with self.lock:
                    existing = self.models.get(model_id)

                    # Case 1: Version mismatch + still initializing → safe to clean up
                    if existing and existing.get('status') == 'initializing' and existing.get(
                            'version') != current_version:
                        logger.info(f"⏭️ {model_id} v{current_version} 已被取代，跳过提交")
                        # Cleanup local resources (milvus_client, redis_client are in scope)
                        for client in [milvus_client, redis_client]:
                            if client:
                                try:
                                    await self._safe_close_client(client)
                                    logger.debug(f"🧹 模型 {model_id} 清理 {type(client).__name__}")
                                except Exception as cleanup_err:
                                    logger.debug(f"⚠️ 忽略清理错误: {cleanup_err}")
                        self.models.pop(model_id, None)
                        return True

                    # Case 2: Newer request already committed → just cleanup local resources, don't touch dict
                    elif existing and existing.get('status') == 'active':
                        logger.debug(f"⏭️ {model_id} v{current_version}: 新请求已提交，仅清理本地资源")
                        for client in [milvus_client, redis_client]:
                            if client:
                                try:
                                    await self._safe_close_client(client)
                                except Exception as cleanup_err:
                                    logger.debug(f"⚠️ 忽略清理错误: {cleanup_err}")
                        return True  # Newer request already handled it

                # --------------------------------------------------------
                # 🎯 STEP 5: Commit Successful Initialization
                # --------------------------------------------------------
                # 存储模型实例
                current_time = datetime.now()
                with self.lock:
                    self.models[model_id] = {
                        'instance': chatflow,
                        'milvus_client': milvus_client,
                        'redis_client': redis_client,
                        'config': config_data or {},
                        'created_time': current_time,
                        'expire_time': expire_time or (time.time() + 14 * 24 * 3600),
                        'memory_usage': self._get_memory_usage(),
                        'status': 'active',
                        'version': current_version
                    }
                    self.model_usage[model_id] = 0  # 🎯 修改：新模型初始计数为0
                    self.model_last_used[model_id] = current_time
                    self.model_created_time[model_id] = current_time

                    if task_id:
                        self.model_tasks[model_id].add(task_id)
                        self.model_usage[model_id] += 1  # 🎯 如果有task_id，才增加计数

                    logger.info(f"模型 {model_id} 动态初始化成功，当前模型总数: {len(self.models)}")

                # 🎯 持久化模型配置
                model_persist_data = {
                    'config': config_data or {},
                    'created_time': current_time,
                    'expire_time': expire_time or (time.time() + 14 * 24 * 3600),
                    'memory_usage': self._get_memory_usage(),
                    'status': 'active',
                    'last_used': current_time
                }
                self.persistence_manager.save_model_config(model_id, model_persist_data)

                # 通知PHP模型激活
                self._notify_php_model_activated(model_id)
                return True

            # --------------------------------------------------------
            # 🎯 STEP 6: Error Handling & Cleanup
            # --------------------------------------------------------
            except asyncio.CancelledError:
                # 协程被取消（通常是gateway读超时后断开连接，Hypercorn取消本协程）。
                # CancelledError继承自BaseException，不会被下面的except Exception捕获，
                # 若不在此回调PHP，前端将永远卡在"激活中"。
                logger.warning(f"模型 {model_id} 初始化被取消(v{current_version})，回调PHP激活失败")
                for client in [milvus_client, redis_client]:
                    if client:
                        try:
                            await self._safe_close_client(client)
                            logger.debug(f"🧹 模型 {model_id} 取消清理 {type(client).__name__}")
                        except Exception as cleanup_err:
                            logger.warning(f"⚠️ 模型 {model_id} 取消清理客户端失败: {cleanup_err}")
                await self._cleanup_partial_init(model_id)
                with self.lock:
                    self.model_usage.pop(model_id, None)
                    self.model_last_used.pop(model_id, None)
                    self.model_tasks.pop(model_id, None)
                    self.model_created_time.pop(model_id, None)
                self._notify_php_model_activation_failed(model_id, "初始化被取消(客户端断开/超时)")
                raise
            except Exception as e:
                logger.error(f"模型 {model_id} 动态初始化失败(v{current_version}): {str(e)}")
                # 🎯 CRITICAL: Clean up local client variables that may have been created
                for client in [milvus_client, redis_client]:  # These are local vars from try block
                    if client:
                        try:
                            await self._safe_close_client(client)
                            logger.debug(f"🧹 模型 {model_id} 异常清理 {type(client).__name__}")
                        except Exception as cleanup_err:
                            logger.warning(f"⚠️ 模型 {model_id} 异常清理客户端失败: {cleanup_err}")

                # 🎯 FIX: Remove nested async lock — we're already holding _init_locks[model_id]!
                # _cleanup_partial_init only uses self.lock (threading.RLock), which is safe here
                await self._cleanup_partial_init(model_id)

                # Clean up tracking dicts (original logic)
                with self.lock:
                    self.model_usage.pop(model_id, None)
                    self.model_last_used.pop(model_id, None)
                    self.model_tasks.pop(model_id, None)
                    self.model_created_time.pop(model_id, None)
                # 通知PHP激活失败
                self._notify_php_model_activation_failed(model_id, str(e))
                raise

            finally:
                # 无论成功或失败，删除激活标记
                if model_id in self.activating_model:
                    del self.activating_model[model_id]
                    logger.info(f"模型 {model_id} 删除激活标记")

    async def _cleanup_partial_init(self, model_id: str):
        """Clean up partial state if initialization was interrupted"""
        with self.lock:
            if model_id in self.models and self.models[model_id].get('status') == 'initializing':
                model_data = self.models[model_id]
                # Close external connections safely
                for client_name in ['milvus_client', 'redis_client']:
                    client = model_data.get(client_name)
                    if client:
                        try:
                            await self._safe_close_client(client)
                            logger.debug(f"🧹 模型 {model_id} 清除 {client_name} ")
                        except Exception as e:
                            logger.warning(f"⚠️ 模型 {model_id} 清除 {client_name}失败: {e}")
                # Remove temporary state
                self.models.pop(model_id, None)
                logger.info(f"🗑️ 模型 {model_id} 启动中状态清除")

    def get_model(self, model_id, task_id=None):
        """获取模型实例，更新使用时间"""
        with self.lock:
            if model_id in self.models:
                model_data = self.models[model_id]

                # 🎯 跳过initializing模型：尚未构建完成，没有instance键，
                # 直接访问会KeyError；返回None让上层走兜底模型逻辑
                if model_data.get('status') == 'initializing':
                    logger.info(f"模型 {model_id} 正在初始化中，暂不可用")
                    return None

                # 检查模型是否过期
                if self._check_model_expired(model_id):
                    logger.warning(f"模型 {model_id} 已过期")
                    # 通知PHP模型休眠    这步和下面的 暂停并重新激活重复 notify_php_task_pause
                    # self._notify_php_model_sleep(model_id)
                    return None

                self.model_last_used[model_id] = datetime.now()
                self.model_usage[model_id] += 1
                if task_id and task_id not in self.model_tasks[model_id]:
                    self.model_tasks[model_id].add(task_id)
                return self.models[model_id]['instance']
            return None

    def _check_model_expired(self, model_id):
        """检查模型是否过期"""
        if model_id in self.models:
            model_data = self.models[model_id]
            current_time = time.time()
            if current_time > model_data['expire_time']:
                return True
        return False

    def extend_model_expire_time(self, model_id, expire_time):
        """延长模型过期时间"""
        with self.lock:
            if model_id in self.models:
                self.models[model_id]['expire_time'] = expire_time
                logger.info(f"模型 {model_id} 过期时间已延长至: {expire_time}")
                return True
            return False

    def release_model(self, model_id, task_id=None):
        """释放模型使用计数"""
        with self.lock:
            if model_id in self.model_usage:
                self.model_usage[model_id] = max(0, self.model_usage[model_id] - 1)

                # 如果指定了task_id，从任务列表中移除
                if task_id and task_id in self.model_tasks[model_id]:
                    self.model_tasks[model_id].remove(task_id)

                logger.info(f"释放模型 {model_id} 使用计数，当前: {self.model_usage[model_id]}")

    async def destroy_model(self, model_id, force=False):
        """销毁模型实例"""
        # Step 1: 锁内检查并立即移除模型，避免await期间get_model返回正在关闭的实例
        with self.lock:
            if model_id not in self.models:
                return True

            # 检查是否还有任务在使用
            if not force and self.model_usage.get(model_id, 0) > 0:
                logger.warning(f"模型 {model_id} 仍有 {self.model_usage[model_id]} 个任务在使用，无法销毁")
                return False

            model_data = self.models.pop(model_id)  # 立即移除，get_model此后返回None
            milvus_client = model_data.get('milvus_client')
            redis_client = model_data.get('redis_client')

            # 同步清理追踪字典（与原逻辑一致，不涉及await）
            if model_id in self.model_usage:
                del self.model_usage[model_id]
            if model_id in self.model_last_used:
                del self.model_last_used[model_id]
            if model_id in self.model_tasks:
                del self.model_tasks[model_id]
            self._init_versions.pop(model_id, None)
            self._init_locks.pop(model_id, None)

        # Step 2: 锁外await关闭客户端，不阻塞其他协程，避免持锁await的竞态
        if milvus_client:
            try:
                await self._safe_close_client(milvus_client)
                logger.info(f"✅ Milvus client closed for model {model_id}")
            except Exception as e:
                logger.error(f"❌ Failed to close Milvus client for {model_id}: {e}")
        if redis_client:
            try:
                await self._safe_close_client(redis_client)
                logger.info(f"✅ Redis client closed for model {model_id}")
            except Exception as e:
                logger.error(f"❌ Failed to close Redis client for {model_id}: {e}")

        # Step 3: 持久化删除与PHP回调（同步操作，无需持锁）
        try:
            self.persistence_manager.delete_model_config(model_id)
            logger.info(f"模型 {model_id} 已销毁，剩余模型数: {len(self.models)}")
            # 通知PHP模型休眠
            self._notify_php_model_sleep(model_id)
            return True
        except Exception as e:
            logger.error(f"销毁模型 {model_id} 失败: {str(e)}")
            return False

    async def again_model(self, model_id):
        """重启模型实例：作废排队中的旧任务，再销毁内存实例"""
        # 作废 Queue 中残留 job，避免 again 后仍用旧配置激活
        if self._queue_async_lock is not None:
            async with self._queue_async_lock:
                self._activation_gen[model_id] = self._activation_gen.get(model_id, 0) + 1
                self._pending_jobs.pop(model_id, None)
                if model_id in self._queue_order:
                    self._queue_order.remove(model_id)
                self._broadcast_queue_positions()

        # 🎯 Step 1: Extract model data under lock (minimize lock hold time)
        with self.lock:
            if model_id not in self.models:
                return True

            # 检查是否还有任务在使用
            print(self.model_usage[model_id])

            # Copy data before releasing lock (safe for async cleanup)
            model_data = self.models[model_id].copy()

        # 🎯 Step 2: Cleanup external resources OUTSIDE lock (allows await)
        for client_name in ['milvus_client', 'redis_client']:
            client = model_data.get(client_name)
            if client:
                try:
                    await self._safe_close_client(client)
                    logger.debug(f"🧹 模型 {model_id} 清理 {client_name}")
                except Exception as e:
                    logger.warning(f"⚠️ 模型 {model_id} 清理 {client_name} 失败: {e}")

        try:
            with self.lock:
                self.models.pop(model_id, None)
                self.model_usage.pop(model_id, None)
                self.model_last_used.pop(model_id, None)
                self.model_tasks.pop(model_id, None)
                self.model_created_time.pop(model_id, None)
                self.persistence_manager.delete_model_config(model_id)
                # 🎯 Also prune version tracking
                self._init_versions.pop(model_id, None)
                self._init_locks.pop(model_id, None)
            logger.info(f"模型 {model_id} 已销毁，剩余模型数: {len(self.models)}")
            return True

        except Exception as e:
            logger.error(f"销毁模型 {model_id} 失败: {str(e)}")
            return False

    async def cleanup_idle_models(self, force_reason=None):
        """智能清理空闲模型
        Args:
            force_reason: 强制清理原因 - 'count_exceed', 'memory_exceed', 'manual'
        """
        with self.lock:
            current_time = datetime.now()
            current_timestamp = time.time()  # 🎯 获取当前时间戳用于过期检查
            current_memory = self._get_memory_usage()
            total_models = len(self.models)

            # 🎯 收集统计信息（跳过initializing状态的模型，其追踪字典尚未填充，直接访问会KeyError）
            active_models = [m for m in self.models
                             if self.models[m].get('status') != 'initializing' and self.model_usage.get(m, 0) > 0]
            idle_models_list = [m for m in self.models
                                if self.models[m].get('status') != 'initializing' and self.model_usage.get(m, 0) == 0]
            stats = {
                'total_models': total_models,
                'active_models': len(active_models),
                'idle_models': len(idle_models_list),
                'current_memory_mb': current_memory,
                'max_memory_mb': self.max_memory_mb,
                'max_models': self.max_models,
                'force_reason': force_reason
            }

            logger.info(f"📊 清理前状态: 模型总数={stats['total_models']}, "
                                 f"活跃={stats['active_models']}, 空闲={stats['idle_models']}, "
                                 f"内存={stats['current_memory_mb']:.1f}MB")

            # 🎯 按创建时间排序的空闲模型列表（最老的在前）
            idle_models = []
            for model_id in self.models:
                model_data = self.models[model_id]
                # 🎯 跳过initializing模型：追踪字典未填充，且不应被清理
                if model_data.get('status') == 'initializing':
                    continue
                if self.model_usage.get(model_id, 0) == 0:  # 只考虑空闲模型
                    idle_time = (current_time - self.model_last_used.get(model_id, current_time)).total_seconds()
                    created_time = self.model_created_time.get(model_id, current_time)

                    # 🎯 检查是否绝对过期
                    expired = current_timestamp > model_data['expire_time']

                    idle_models.append({
                        'model_id': model_id,
                        'created_time': created_time,
                        'idle_time': idle_time,
                        'last_used': self.model_last_used.get(model_id, current_time),
                        'expired': expired,  # 🎯 新增：是否已过期
                        'expire_time': model_data['expire_time'],
                        'expire_in_hours': max(0, (model_data['expire_time'] - current_timestamp) / 3600)
                    })

            # 按创建时间排序（最老的在前）
            idle_models.sort(key=lambda x: x['created_time'])

            models_to_remove = []
            removal_reason = "normal_timeout"

            # 🎯 智能清理决策
            if force_reason == 'count_exceed':
                # 模型数量超限：清理最老的空闲模型，直到数量达标
                target_count = max(1, self.max_models - 5)  # 清理到比上限少5个，留出缓冲
                excess_count = total_models - target_count

                if excess_count > 0 and idle_models:
                    models_to_remove = idle_models[:min(excess_count, len(idle_models))]
                    removal_reason = f"count_exceed_{excess_count}_over"

            elif force_reason == 'memory_exceed':
                # 内存超限：清理最老的空闲模型，直到内存达标
                target_memory = self.max_memory_mb * 0.8  # 清理到80%的内存使用
                excess_memory = current_memory - target_memory

                if excess_memory > 0 and idle_models:
                    # 预估清理效果：每个模型约释放100MB
                    models_needed = min(len(idle_models), int(excess_memory / self.model_memory_estimate) + 1)
                    models_to_remove = idle_models[:models_needed]
                    removal_reason = f"memory_exceed_{excess_memory:.0f}MB_over"

            elif force_reason == 'manual':
                # 🎯 手动清理：清理所有超时空闲模型和已过期模型
                for model_info in idle_models:
                    if model_info['idle_time'] > self.model_timeout and model_info['expired']:
                        models_to_remove.append(model_info)
                removal_reason = "manual_cleanup"

            else:
                # 🎯 正常清理：清理超时空闲模型和已过期模型
                for model_info in idle_models:
                    if model_info['idle_time'] > self.model_timeout and model_info['expired']:
                        models_to_remove.append(model_info)
                removal_reason = "normal_expired"

            # 🎯 执行清理
            removed_count = 0
            for model_info in models_to_remove:
                model_id = model_info['model_id']
                if await self.destroy_model(model_id, force=True):
                    removed_count += 1
                    if model_info['expired']:
                        expired_status = "已过期"
                    else:
                        expire_hours = model_info.get('expire_in_hours', 0)
                        if expire_hours > 24:
                            expired_status = f"未过期(还有{expire_hours / 24:.1f}天)"
                        elif expire_hours > 1:
                            expired_status = f"未过期(还有{expire_hours:.1f}小时)"
                        else:
                            expired_status = f"未过期(还有{expire_hours * 60:.0f}分钟)"

                    logger.info(f"🧹 清理模型: {model_id}, "
                                         f"创建时间: {model_info['created_time'].strftime('%Y-%m-%d %H:%M:%S')}, "
                                         f"空闲: {model_info['idle_time']:.0f}秒, "
                                         f"过期状态: {expired_status}, "
                                         f"原因: {removal_reason}")

            for model_id in list(self._init_versions.keys()):
                if model_id not in self.models:
                    self._init_versions.pop(model_id, None)
                    self._init_locks.pop(model_id, None)

            # 🎯 清理后统计
            if removed_count > 0:
                after_memory = self._get_memory_usage()
                memory_saved = current_memory - after_memory
                logger.info(f"✅ 清理完成: 移除了 {removed_count} 个模型, "
                                     f"释放内存: {memory_saved:.1f}MB, "
                                     f"剩余模型: {len(self.models)}")

                # 🎯 记录清理效果数据（用于优化配置）
                self._record_cleanup_stats({
                    'before_memory': current_memory,
                    'after_memory': after_memory,
                    'memory_saved': memory_saved,
                    'models_removed': removed_count,
                    'reason': removal_reason,
                    'timestamp': datetime.now().isoformat()
                })

            return {
                'removed_count': removed_count,
                'reason': removal_reason,
                'stats_before': stats,
                'stats_after': {
                    'total_models': len(self.models),
                    'current_memory_mb': self._get_memory_usage()
                }
            }

    async def check_and_cleanup_if_needed(self):
        """检查并触发必要的清理 - 🎯 确保这个方法被正确调用"""
        current_memory = self._get_memory_usage()
        total_models = len(self.models)

        force_reason = None

        # 🎯 内存超限检查
        if current_memory > self.max_memory_mb:
            logger.warning(f"🚨 内存超限: {current_memory:.1f}MB > {self.max_memory_mb}MB")
            force_reason = 'memory_exceed'

        # 🎯 模型数量超限检查
        elif total_models > self.max_models:
            logger.warning(f"⚠️ 模型数量超限: {total_models} > {self.max_models}")
            force_reason = 'count_exceed'

        if force_reason:
            return await self.cleanup_idle_models(force_reason=force_reason)

        return {'cleaned': False, 'reason': 'not_needed'}

    @staticmethod
    def _record_cleanup_stats(stats):
        """记录清理统计信息，用于优化配置"""
        # 这里可以存储到文件或数据库，用于分析内存使用模式
        logger.debug(f"📈 清理统计: {json.dumps(stats, default=str)}")

    @staticmethod
    def _build_chatflow_config(config_data):
        print(f"模型配置数据：{str(config_data)[:800]}......")
        # 检查配置数据是否完整
        required_keys = [
            'agent_data',
            'intentions',
            'knowledge',
            'chatflow_design',
            'knowledge_main_flow',
            'global_configs'
        ]

        # 检查config_data是否存在且包含所有必需字段
        has_all_required = (
                config_data and
                isinstance(config_data, dict) and
                all(key in config_data for key in required_keys)
        )

        if has_all_required:
            # 可以添加更详细的检查，比如值是否不为空
            # 检查值是否有效（非None且不是空字符串/列表/字典）
            values_valid = all(
                config_data.get(key) not in (None, '', [], {})
                for key in required_keys
            )

            if not values_valid:
                # 记录哪些字段有问题
                missing_or_empty = [
                    key for key in required_keys
                    if config_data.get(key) in (None, '', [], {})
                ]
                print(f"警告: 以下配置字段为空或无效: {missing_or_empty}")
                # 可以选择回退到默认配置或抛出异常
                # return None  # 或抛出异常

            print("使用自定义配置数据")
            print(f"配置字段: {list(config_data.keys())}")

            # 测试先用默认的 到时候改成实际的
            chatflow_config = ChatFlowConfig.from_files(
                config_data.get('agent_data'),
                config_data.get('knowledge'),
                config_data.get('knowledge_main_flow'),
                config_data.get('chatflow_design'),
                config_data.get('global_configs'),
                config_data.get('intentions'),
            )

        else:
            # 如果配置不完整，记录缺失的字段
            if config_data and isinstance(config_data, dict):
                missing_keys = [key for key in required_keys if key not in config_data]
                print(f"配置数据不完整，缺失字段: {missing_keys}")
                print(f"已有字段: {list(config_data.keys())}")
            else:
                print("配置数据为空或不是字典类型")

            print("回退到使用默认路径配置")

            # 使用默认路径配置
            chatflow_config = ChatFlowConfig.from_files(
                agent_data,
                knowledge,
                knowledge_main_flow,
                chatflow_design,
                global_configs,
                intentions
            )

        return chatflow_config

    def get_model_status(self, model_id=None):
        """获取模型状态 - 修复JSON序列化问题"""
        with self.lock:
            current_memory = self._get_memory_usage()
            if model_id:
                if model_id in self.models:
                    model_data = self.models[model_id]
                    # 🎯 修复：将 set 转换为 list 以便 JSON 序列化
                    associated_tasks = list(self.model_tasks.get(model_id, set()))

                    return {
                        'model_id': model_id,
                        'status': 'active',
                        'created_time': model_data.get('created_time', datetime.now()).isoformat(),
                        'last_used': self.model_last_used.get(model_id, datetime.now()).isoformat(),
                        'usage_count': self.model_usage.get(model_id, 0),
                        'associated_tasks': associated_tasks,  # 🎯 使用 list 而不是 set
                        'memory_usage': model_data.get('memory_usage', 0),
                        'version': model_data.get('version')  # Expose version for testing/monitoring
                    }
                else:
                    return {'model_id': model_id, 'status': 'not_found'}
            else:
                # 全局状态 - 增强信息
                idle_models = [m for m in self.models if self.model_usage.get(m, 0) == 0]
                active_models = [m for m in self.models if self.model_usage.get(m, 0) > 0]

                # 计算内存使用统计
                total_estimated_memory = len(self.models) * self.model_memory_estimate

                # 🎯 修复：构建可序列化的模型状态字典
                models_status = {}
                for model_id, data in self.models.items():
                    # 🎯 修复：将 set 转换为 list
                    associated_tasks_list = list(self.model_tasks.get(model_id, set()))
                    last_used = self.model_last_used.get(model_id, data.get('created_time', datetime.now()))
                    usage_count = self.model_usage.get(model_id, 0)

                    models_status[model_id] = {
                        'created_time': data.get('created_time', datetime.now()).isoformat(),
                        'last_used': last_used.isoformat(),
                        'usage_count': usage_count,
                        'associated_tasks': associated_tasks_list,  # 🎯 使用 list
                        'status': 'active' if usage_count > 0 else 'idle',
                        'idle_seconds': (datetime.now() - last_used).total_seconds(),
                        'version': data.get('version')
                    }

                return {
                    'total_models': len(self.models),
                    'active_models': len(active_models),
                    'idle_models': len(idle_models),
                    'current_memory_mb': current_memory,
                    'max_memory_mb': self.max_memory_mb,
                    'max_models': self.max_models,
                    'memory_usage_percent': (current_memory / self.max_memory_mb) * 100,
                    'model_usage_percent': (len(self.models) / self.max_models) * 100,
                    'estimated_model_memory_mb': total_estimated_memory,
                    'models': models_status  # 🎯 使用修复后的字典
                }

    @staticmethod
    def _get_memory_usage():
        """获取内存使用情况"""
        process = psutil.Process(os.getpid())
        return process.memory_info().rss / 1024 / 1024  # MB

    async def check_memory_usage(self):
        """检查内存使用情况，防止内存泄漏"""
        current_memory = self._get_memory_usage()
        # 这里可以保留作为独立的内存检查，但清理逻辑已经集成到智能清理中
        if current_memory > 1024:  # 超过1GB
            logger.warning(f"⚠️ 内存使用较高: {current_memory:.1f}MB")
            # 触发智能清理
            await self.check_and_cleanup_if_needed()

        return current_memory

    # 🎯 新增：磁盘监控方法
    def check_disk_usage(self):
        """检查磁盘使用情况，防止磁盘爆满"""
        disk_info = self.persistence_manager.get_disk_usage()
        if disk_info and disk_info.get('usage_percent', 0) > 90:
            logger.warning(f"⚠️ 磁盘使用率过高: {disk_info['usage_percent']:.1f}%")
            return False
        return True

    # 🎯 新增：手动备份接口
    def create_manual_backup(self):
        """手动创建备份"""
        return self.persistence_manager.create_manual_backup()

model_manager = DynamicModelManager()

def get_detailed_error():
    """获取详细的错误信息"""
    # 获取当前异常信息
    exc_type, exc_value, exc_traceback = sys.exc_info()

    # 获取调用栈信息
    stack_summary = traceback.extract_tb(exc_traceback)

    # 获取最近的错误位置
    if stack_summary:
        frame = stack_summary[-1]  # 最近的错误位置
        filename = frame.filename
        lineno = frame.lineno
        function = frame.name
        code = frame.line

        return {
            'error_type': exc_type.__name__,
            'error_message': str(exc_value),
            'file': filename,
            'line': lineno,
            'function': function,
            'code': code,
            'full_traceback': traceback.format_exc()
        }
    return None

# TODO: Services
# 🎯 启动时恢复模型（简化版）
@app.before_serving
async def startup():
    await model_manager.recover_models_on_startup()  # now awaited properly
    model_manager.start_cleanup_task() # clean work
    model_manager.start_activation_queue_worker()  # 激活串行队列

@app.route('/health', methods=['GET'])
def health_check():
    """健康检查 - 增强版本"""
    status = model_manager.get_model_status()

    health_status = 'healthy'
    warnings = []

    # 🎯 健康检查逻辑
    if status['memory_usage_percent'] > 90:
        health_status = 'warning'
        warnings.append(f"内存使用率过高: {status['memory_usage_percent']:.1f}%")

    if status['model_usage_percent'] > 90:
        health_status = 'warning'
        warnings.append(f"模型数量接近上限: {status['model_usage_percent']:.1f}%")

    return jsonify({
        'status': health_status,
        'service': 'dynamic_ai_service',
        'timestamp': datetime.now().isoformat(),
        'model_stats': status,
        'warnings': warnings,
        'memory_usage': status['current_memory_mb']
    })

@app.route('/model/initialize', methods=['POST'])
async def initialize_model():
    """初始化模型接口 - 入队后立即返回排队信息，真正激活由后台串行执行"""
    data = await request.get_json(silent=True)
    if not data:
        return jsonify({"error": "无效JSON"}), 400
    model_id = data.get('model_id')
    config_data = data.get('config', {})
    task_id = data.get('task_id', None)
    expire_time = data.get('expire_time')  # 需要添加这行
    if not model_id:
        return jsonify({
            'success': False,
            'message': 'model_id 参数不能为空'
        }), 400

    try:
        result = await model_manager.enqueue_initialize(model_id, config_data, task_id, expire_time)
        return jsonify({
            'success': result.get('success', True),
            'message': result.get('message', f'模型 {model_id} 已提交激活'),
            'model_id': model_id,
            'task_id': task_id,
            'queued': result.get('queued', True),
            'queue_position': result.get('queue_position', 0),
            'waiting_count': result.get('waiting_count', 0),
            'status': result.get('status', 'queued'),
            'already_active': result.get('already_active', False),
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'模型 {model_id} 初始化异常: {str(e)}'
        }), 500

@app.route('/model/extend', methods=['POST'])
async def extend_model():
    """延长模型过期时间接口"""
    data = await request.get_json(silent=True)
    if not data:
        return jsonify({"error": "无效JSON"}), 400
    model_id = data.get('model_id')
    expire_time = data.get('expire_time')

    if not model_id or not expire_time:
        return jsonify({
            'success': False,
            'message': 'model_id 和 expire_time 参数不能为空'
        }), 400

    if model_manager.extend_model_expire_time(model_id, expire_time):
        return jsonify({
            'success': True,
            'message': f'模型 {model_id} 过期时间延长成功',
            'model_id': model_id
        })
    else:
        return jsonify({
            'success': False,
            'message': f'模型 {model_id} 未找到，延长失败'
        }), 404

@app.route('/model/generate', methods=['POST'])
async def generate_response():
    """生成话术接口  加兜底模型逻辑 ，任务id里包含一个model_id 和兜底的model_id 失败的话用兜底在判断一遍"""
    data = await request.get_json(silent=True)
    if not data:
        return jsonify({"error": "无效JSON"}), 400
    print(data, '生成话术请求参数')
    model_id = data.get('model_id')
    backstop_model = data.get('backstop_model')
    user_input = data.get('user_input', '')
    call_id = data.get('call_id', 'unknown')
    task_id = data.get('task_id')

    if not model_id:
        return jsonify({
            'success': False,
            'message': 'model_id 参数不能为空'
        }), 400
    # 🎯 记录实际使用的模型ID
    actual_used_model = model_id
    # 获取模型实例
    # 先禁用 测试参数 相关 用假的
    chatflow = model_manager.get_model(model_id, task_id)
    print(chatflow, '临时chatflow')
    if not chatflow:
        # 不存在使用兜底模型，虽然model_id 和backstop_model可能是一个不影响，多判断一次的事儿
        actual_used_model = backstop_model  # 🎯 更新实际使用的模型
        chatflow = model_manager.get_model(backstop_model, task_id)

    if not chatflow:
        # 模型未找到或已过期，通知PHP暂停任务
        if task_id:
            model_manager.notify_php_task_pause(task_id, model_id, "model_not_found_or_expired")

        return jsonify({
            'success': False,
            'message': f'模型 {model_id} 和兜底模型 {backstop_model} 都未找到或已过期',
            'error_code': 'MODEL_NOT_FOUND'
        }), 404

    try:
        # 配置
        conv_config = {"configurable": {"thread_id": f"call_{call_id}"}}
        # print(state, '生成话术的请求参数')
        state = await chatflow.ainvoke({"messages": [HumanMessage(content=user_input)]}, config=conv_config)
        print(state, 'state---结果')

        # 提取AI回复 - metadata 中与最后一条的 reply_round 相同的所有条目
        current_round_metadata = state["metadata"][-1] # 获取最后一条的 reply_round
        print(json.dumps(current_round_metadata, indent=4, ensure_ascii=False), '输出metadata')
        # 创建输出内容
        output = {
            'success': True,
            # 当前回复的话术内容
            'content': current_round_metadata.get("content", []),
            'end_call': current_round_metadata.get("end_call", False),
            'reply_round': current_round_metadata.get("reply_round", 0),
            'token_used': current_round_metadata.get("token_used", 0),
            'total_token_used': current_round_metadata.get("total_token_used", 0),
            # 历史记录 - 同一回复轮(reply_round) 历史记录是一样的，都是最后一轮的
            'conversation_history_detail': state["metadata"],
            'call_id': call_id,
            'model_id': actual_used_model,
            'timestamp': datetime.now().isoformat()
        }
        print(json.dumps(output, indent=4, ensure_ascii=False), '输出结果')
        return jsonify(output)

    except Exception as e:
        error_info = get_detailed_error()
        if error_info:
            print(f"错误类型: {error_info['error_type']}")
            print(f"错误信息: {error_info['error_message']}")
            print(f"文件: {error_info['file']}")
            print(f"行号: {error_info['line']}")
            print(f"函数: {error_info['function']}")
            print(f"代码: {error_info['code']}")
            print("完整堆栈:")
            print(error_info['full_traceback'])
        logger.error(f"生成话术失败 - 模型: {actual_used_model}, 呼叫: {call_id}, 错误: {str(e)}，完整堆栈：{error_info['full_traceback']}")
        return jsonify({
            'success': False,
            'message': f'话术生成失败: {str(e)}'
        }), 500
    finally:
        # 释放模型使用计数
        if task_id:
            model_manager.release_model(actual_used_model, task_id)

@app.route('/model/again', methods=['POST'])
async def again_model():
    """销毁模型接口"""
    data = await request.get_json(silent=True)
    if not data:
        return jsonify({"error": "无效JSON"}), 400
    model_id = data.get('model_id')
    
    if not model_id:
        return jsonify({
            'success': False,
            'message': 'model_id 参数不能为空'
        }), 400

    if await model_manager.again_model(model_id):
        return jsonify({
            'success': True,
            'message': f'模型 {model_id} 销毁成功'
        })
    
    else:
        return jsonify({
            'success': False,
            'message': f'模型 {model_id} 销毁失败，可能仍有任务在使用'
        }), 400

@app.route('/model/destroy', methods=['POST'])
async def destroy_model():
    """销毁模型接口"""
    data = await request.get_json(silent=True)
    if not data:
        return jsonify({"error": "无效JSON"}), 400
    model_id = data.get('model_id')
    task_id = data.get('task_id')
    force = data.get('force', False)
    
    if not model_id:
        return jsonify({
            'success': False,
            'message': 'model_id 参数不能为空'
        }), 400

    if await model_manager.destroy_model(model_id, force):
        return jsonify({
            'success': True,
            'message': f'模型 {model_id} 销毁成功'
        })
    else:
        return jsonify({
            'success': False,
            'message': f'模型 {model_id} 销毁失败，可能仍有任务在使用'
        }), 400

@app.route('/model/status', methods=['GET'])
def get_model_status():
    """获取模型状态"""
    model_id = request.args.get('model_id')
    status = model_manager.get_model_status(model_id)
    return jsonify(status)

@app.route('/model/cleanup', methods=['POST'])
async def cleanup_models():
    """手动触发清理空闲模型 - 🎯 修复这里"""
    data = await request.get_json(silent=True)
    if not data:
        return jsonify({"error": "无效JSON"}), 400
    force = data.get('force', False)

    # 🎯 根据force参数决定清理策略
    if force:
        result = await model_manager.cleanup_idle_models(force_reason='manual')
    else:
        result = await model_manager.cleanup_idle_models()  # 正常清理

    status = model_manager.get_model_status()
    return jsonify({
        'success': True,
        'message': '空闲模型清理完成',
        'cleanup_result': result,  # 🎯 返回清理详情
        'current_stats': {
            'total_models': status['total_models'],
            'active_models': status['active_models'],
            'current_memory_mb': status['current_memory_mb']
        }
    })

@app.route('/model/persistence/backup', methods=['POST'])
def create_manual_backup():
    """手动创建持久化数据备份"""
    try:
        if model_manager.create_manual_backup():
            return jsonify({
                'success': True,
                'message': '手动备份创建成功'
            })
        else:
            return jsonify({
                'success': False,
                'message': '手动备份创建失败'
            }), 500
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'创建备份异常: {str(e)}'
        }), 500

@app.route('/model/persistence/status', methods=['GET'])
def get_persistence_status():
    """获取持久化状态"""
    try:
        disk_info = model_manager.persistence_manager.get_disk_usage()
        models_count = len([f for f in os.listdir(model_manager.persistence_manager.models_dir)
                            if f.endswith('.json')])
        backups_count = len([f for f in os.listdir(model_manager.persistence_manager.backup_dir)
                             if f.endswith('.json')])

        return jsonify({
            'success': True,
            'persistence_path': model_manager.persistence_manager.base_path,
            'models_persisted': models_count,
            'backups_count': backups_count,
            'disk_usage': disk_info,
            'warnings': ['磁盘使用率过高'] if disk_info.get('usage_percent', 0) > 90 else []
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取持久化状态失败: {str(e)}'
        }), 500

# TODO: Start the service
def start_dynamic_service(port=5002):
    """启动动态模型服务 - 调试版本"""
    logging.getLogger("hypercorn").setLevel(logging.INFO)
    hypercorn_logger = logging.getLogger("hypercorn.access")

    logger.info(f"启动动态AI模型服务，端口: {port}")
    logger.info("服务特点: 动态模型管理，按需创建，自动清理")

    config = Config()
    config.bind = [f"0.0.0.0:{port}"]
    config.accesslog = hypercorn_logger
    config.backlog = 1024
    config.timeout_keep_alive = 30
    config.startup_timeout = 720.0
    config.shutdown_timeout = 30.0
    config.use_reloader = False
    config.lifespan = "off"  # ✅ CRITICAL: disable ASGI lifespan

    logger.info(f"Hypercorn 配置:")
    logger.info(f"  - 端口: {port}")
    logger.info(f"  - 启动超时: {config.startup_timeout}s")
    logger.info(f"  - Lifespan: {config.lifespan}")

    try:
        asyncio.run(serve(app, config))
    except Exception as e:
        logger.error(f"服务启动失败: {e}")
        import traceback
        traceback.print_exc()
        raise

if __name__ == '__main__':
    start_dynamic_service()