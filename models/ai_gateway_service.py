# ai_gateway_service.py
# AI网关服务 - 负责Lua脚本与AI模型服务之间的通信协调
import os
import json
import time
import threading
import tempfile
import subprocess
from datetime import datetime
from collections import defaultdict
import requests
import redis
from flask import Flask, request, jsonify
from config.setting import settings
from common.logger import setup_logger
from functionals.matchers import KeywordMatcher
from pydub import AudioSegment
from pydub.silence import detect_nonsilent

app = Flask(__name__)
logger = setup_logger('ai_gateway', category='gateway', console_output=True)

# 服务配置
#Get model service url from env first (for Docker), if not, get from settings
AI_MODEL_SERVICE_URL = os.getenv("AI_MODEL_SERVICE_URL", settings.AI_MODEL_SERVICE_URL)
GATEWAY_VERSION = "1.0.0"

# Redis连接
redis_pool = redis.ConnectionPool(
    #get redis server url from env (for Docker) first, if not, get it from settings
    host=os.getenv("REDIS_SERVER", settings.REDIS_SERVER),
    password=settings.REDIS_PASSWORD,
    port=settings.REDIS_PORT,
    db=settings.REDIS_DB,
    decode_responses=True,
    max_connections=50,
    socket_timeout=10,          # 增加socket超时时间
    socket_connect_timeout=5,   # 连接超时
    retry_on_timeout=True,      # 超时重试
    health_check_interval=30,   # 健康检查间隔
)
redis_client = redis.Redis(connection_pool=redis_pool)


class GatewayManager:
    """网关管理器"""

    def __init__(self):
        # 🎯 直接使用可序列化的数据结构
        self.stats = {
            'total_calls': 0,
            'successful_calls': 0,
            'failed_calls': 0,
            'active_tasks': []  # 直接使用列表而不是 set
        }
        self.task_model_map = {}
        self.model_tasks = defaultdict(list)  # 使用列表而不是 set

        # 🎯 内部使用 set 用于快速查找（不暴露给 JSON）
        self._active_tasks_set = set()
        self._model_tasks_set = defaultdict(set)

    def record_call(self, success=True):
        """记录呼叫统计"""
        self.stats['total_calls'] += 1
        if success:
            self.stats['successful_calls'] += 1
        else:
            self.stats['failed_calls'] += 1

    def bind_task_to_model(self, task_id, model_id):
        if task_id in self.task_model_map:
            existing_model_id = self.task_model_map[task_id]
            if existing_model_id != model_id:
                logger.warning(f"任务 {task_id} 从模型 {existing_model_id} 切换到 {model_id}")
                self.unbind_task(task_id)

        # 🎯 同时更新内部 set 和外部列表
        self._active_tasks_set.add(task_id)
        if task_id not in self.stats['active_tasks']:
            self.stats['active_tasks'].append(task_id)

        self._model_tasks_set[model_id].add(task_id)
        if task_id not in self.model_tasks[model_id]:
            self.model_tasks[model_id].append(task_id)

        self.task_model_map[task_id] = model_id
        logger.info(f"🔗 任务绑定到模型 - 任务: {task_id}, 模型: {model_id}")

    def unbind_task(self, task_id):
        # 🎯 同时更新内部 set 和外部列表
        if task_id in self._active_tasks_set:
            self._active_tasks_set.remove(task_id)
        if task_id in self.stats['active_tasks']:
            self.stats['active_tasks'].remove(task_id)

        if task_id in self.task_model_map:
            model_id = self.task_model_map[task_id]
            del self.task_model_map[task_id]

            if model_id in self._model_tasks_set and task_id in self._model_tasks_set[model_id]:
                self._model_tasks_set[model_id].remove(task_id)
            if model_id in self.model_tasks and task_id in self.model_tasks[model_id]:
                self.model_tasks[model_id].remove(task_id)

    # 🎯 不再需要特殊的序列化方法
    # 因为所有数据结构已经是可序列化的

# 全局网关管理器
gateway_manager = GatewayManager()


def async_initialize_model(model_id, config_data, expire_time):
    """异步初始化模型"""

    def initialize_task():
        try:
            payload = {
                'model_id': model_id,
                'config': config_data or {},
                'expire_time': expire_time
            }

            logger.info(f"🔄 开始异步初始化模型: {model_id}")
            response = requests.post(
                f"{AI_MODEL_SERVICE_URL}/model/initialize",
                json=payload,
                timeout=600  # 初始化可能较慢
            )

            if response.status_code == 200:
                result = response.json()
                if result['success']:
                    logger.info(f"✅ 异步模型初始化成功: {model_id}")
                else:
                    logger.error(f"❌ 异步模型初始化失败: {model_id}, 错误: {result.get('message')}")
            else:
                logger.error(f"❌ 异步模型初始化HTTP错误: {model_id}, 状态码: {response.status_code}")

        except Exception as e:
            logger.error(f"🚨 异步模型初始化异常: {model_id}, 错误: {str(e)}")

    # 启动异步线程
    thread = threading.Thread(target=initialize_task, daemon=True, name=f"AsyncInit-{model_id}")
    thread.start()
    logger.info(f"🚀 提交异步模型初始化任务: {model_id}")


def call_model_service(model_id, backstop_model, user_input, call_id, task_id):
    """调用AI模型服务生成话术，返回(响应内容, 历史, 详细历史, 实际使用的模型ID, 结束标志, 其他配置)"""
    try:
        payload = {
            'model_id': model_id,
            'backstop_model': backstop_model,
            'user_input': user_input,
            'call_id': call_id,
            'task_id': task_id
        }

        start_time = time.time()
        response = requests.post(
            f"{AI_MODEL_SERVICE_URL}/model/generate",
            json=payload,
            timeout=60
        )
        response_time = (time.time() - start_time) * 1000  # 毫秒

        if response.status_code == 200:
            result = response.json()
            print(result, '')
            if result['success']:
                logger.info(f"🎯 AI响应成功 - 任务: {task_id}, 呼叫: {call_id}, 耗时: {response_time:.1f}ms")
                gateway_manager.record_call(success=True)

                # 🎯 提取新的数据结构
                content_list = result['content']  # 现在是列表结构
                real_model_id = result.get('model_id', model_id)
                end_call = result.get('end_call', False)
                conversation_history_detail = result.get('conversation_history_detail', [])

                return content_list, conversation_history_detail, real_model_id, end_call
            else:
                logger.error(f"❌ AI服务业务错误: {result.get('message')}")
        elif response.status_code == 404:
            logger.error(f"🔍 模型未找到 - 模型: {model_id}, 任务: {task_id}")
            gateway_manager.record_call(success=False)
        else:
            logger.error(f"❌ AI服务HTTP错误: {response.status_code}")

    except requests.exceptions.RequestException as e:
        logger.error(f"🔌 调用AI模型服务失败: {str(e)}")
        gateway_manager.record_call(success=False)
        error_detail = {
            'main_model': model_id,
            'backstop_model': backstop_model,
            'error': str(e),
            'call_id': call_id,
            'task_id': task_id
        }
        logger.error(f"🚨 所有模型都不可用: {json.dumps(error_detail)}")

    # 默认返回兜底模型
    default_response = [{
        'dialog_id': 'default',
        # 'content': "喂，我这边好像信号不太好，还是听不见您那边的声音，要么我先挂了，之后再联系您，再见",
        'content': "",
        'variate': {}
    }]
    # 这个 正式使用 按True 报错直接挂断
    return default_response, [], backstop_model, True


import re
def calculate_tts_duration(text, speed=1.0):
    """
    计算TTS语音时长
    支持格式：
    - [p500] 停顿500毫秒
    - <break time="500ms"/> SSML停顿标签
    - 其他SSML标签会被忽略（只计算文本内容）
    """
    print(text, '计算TTS语音时长')
    if not text:
        return 0

    # 1. 处理 [p数字] 格式的停顿
    pause_pattern = r'\[p(\d+)\]'
    pauses = re.findall(pause_pattern, text)
    total_pause_time = sum(int(pause) / 1000 for pause in pauses)

    # 2. 处理 <break time="500ms"/> 格式的SSML停顿
    ssml_break_pattern = r'<break\s+time="(\d+)ms"\s*/?>'
    ssml_pauses = re.findall(ssml_break_pattern, text, re.IGNORECASE)
    total_pause_time += sum(int(pause) / 1000 for pause in ssml_pauses)

    print(f"停顿标记: {pauses + ssml_pauses}, 总停顿: {total_pause_time}秒")

    # 3. 移除所有标签，只保留纯文本
    # 移除 [p数字] 标签
    text = re.sub(pause_pattern, '', text)
    # 移除所有XML/HTML标签（包括<break>、<speak>等）
    text = re.sub(r'<[^>]+>', '', text)
    # 移除空白字符（可选）
    text = text.strip()

    if not text:  # 如果只有停顿没有文本
        return max(0.5, round(total_pause_time, 2))

    # 统计字符类型
    chinese_chars = len([c for c in text if '\u4e00' <= c <= '\u9fff'])
    english_letters = len([c for c in text if 'a' <= c.lower() <= 'z'])
    numbers = len([c for c in text if c.isdigit()])

    # 标点符号
    chinese_punctuation = len([c for c in text if c in '，。！？；：'])
    english_punctuation = len([c for c in text if c in ',.!?;:'])

    print(f"清理后文本: {text}")
    print(f"文本长度: {len(text)} 字符")
    print(f"中文: {chinese_chars}字")
    print(f"英文: {english_letters}字母")
    print(f"数字: {numbers}个")
    print(f"中文标点: {chinese_punctuation}个")
    print(f"英文标点: {english_punctuation}个")

    # 经验公式（可根据实际TTS引擎调整）
    # 不同语言/字符的朗读速度
    chinese_time = chinese_chars * 0.26  # 每个中文字约0.22秒
    english_time = english_letters * 0.18  # 每个英文字母约0.18秒
    number_time = numbers * 0.15  # 每个数字约0.15秒
    punctuation_time = chinese_punctuation * 0.15 + english_punctuation * 0.08

    # 基础朗读时长
    speech_duration = chinese_time + english_time + number_time + punctuation_time

    # 加上停顿标记的时间（停顿不受语速影响）
    total_duration = (speech_duration / speed) + total_pause_time

    print(f"{chinese_time:.1f}秒 中文")
    print(f"{english_time:.1f}秒 英文")
    print(f"{number_time:.1f}秒 数字")
    print(f"{punctuation_time:.1f}秒 标点")
    print(f"{speech_duration:.1f}秒 总朗读时长")
    print(f"语速系数: {speed}")
    print(f"加上停顿后总时长: {total_duration:.1f}秒")

    return max(1.0, round(total_duration, 2))


def calculate_final_timeout(tts_duration, config_wait_time, ai_wait_time):
    """
    计算最终的ASR超时时间
    优先级：AI返回wait_time > 配置not_answer_wait_seconds > TTS计算超时
    """
    # 基础保障： 缓冲时间
    tts_based_timeout = 2 * 1000  # 毫秒

    # 使用配置的等待时间（如果存在）
    config_based_timeout = config_wait_time * 1000 if config_wait_time > 0 else tts_based_timeout

    # AI返回的wait_time有最高优先级
    if ai_wait_time and float(ai_wait_time) > 0:
        final_timeout = float(ai_wait_time) * 1000
        logger.info(f"🎯 使用AI返回的等待时间: {final_timeout}ms")
    else:
        final_timeout = max(tts_based_timeout, config_based_timeout)
        logger.info(f"🎯 使用计算超时时间: {final_timeout}ms")
    tts_duration = final_timeout + tts_duration * 1000  # TTS时长 + 最终的时间
    return int(final_timeout), int(tts_duration)


def process_ai_content(task_id, original_number, content_list, user_input, model_id):
    """处理AI返回的content字典，生成混合播放内容"""
    phone_key = f"{settings.REDIS_PRE}:task:phone:{task_id}"
    phone_info_str = redis_client.hget(phone_key, original_number)
    phone_info = json.loads(phone_info_str) if phone_info_str else {}
    logger.info(f"phone_key:{phone_key} --original_number:{original_number} -- phone_info_str: {phone_info_str} --phone_info:{phone_info} ")
    try:
        final_content_list = []
        mixed_list = []

        for content_data in content_list:
            # 🎯 创建处理后的数据，保留所有原始字段
            processed_data = {}

            # 🎯 如果content_data是字典，直接复制所有原始字段
            if isinstance(content_data, dict):
                processed_data = content_data.copy()
            else:
                # 如果不是字典，创建一个包含原始内容的基本结构
                processed_data = {'text': str(content_data)}

            final_text = ''
            # 🎯 提取基础信息
            dialog_id = processed_data.get('dialog_id', 'unknown')
            raw_content = processed_data.get('text', '')
            variate_data = processed_data.get('variate', {})
            other_config = processed_data.get('other_config', {})

            # 🎯 从Redis获取对话配置数据
            dialogs_key = f"{settings.REDIS_PRE}:robot:{model_id}:dialogs"
            logger.warning(f'对话配置KEY-> {dialogs_key}')
            dialogs_data_str = redis_client.hget(dialogs_key, dialog_id)
            dialogs_data = json.loads(dialogs_data_str) if dialogs_data_str else {}

            # 🎯 如果没有配置数据，使用简单TTS降级处理
            if not dialogs_data:
                logger.warning(f"⚠️ 未找到对话配置数据: dialog_id={dialog_id}, model_id={model_id}")
                # 🎯 即使没有配置数据，也要处理变量
                if contains_variables(raw_content):
                    raw_content = replace_variables_in_text(raw_content, variate_data, user_input, phone_info)
                mixed_dict = create_simple_tts_content(raw_content, other_config)  # 生成返回值
                final_text = raw_content  # 真实话术 替换了变量之后的
            else:
                # 🎯 获取对话的根节点和子节点
                dialog_info = dialogs_data.get('info', {})
                dialog_child = dialogs_data.get('child', [])
                print(dialogs_data, 'dialog_data')

                # 🎯 构建混合播放内容
                mixed_dict = {
                    'playback_type': 'mixed',
                    'content': [],
                    'total_duration': 0,
                    'allow_bargein': True,
                    'dialog_id': dialog_id,
                    'other_config': other_config,
                }

                # 🎯 处理子节点（分段播放）
                if dialog_child:
                    # 按sort字段排序
                    sorted_child = sorted(dialog_child, key=lambda x: x.get('sort', 0))

                    # 🎯 构建最终文本，用于计算总时长
                    final_text_parts = []

                    for segment in sorted_child:
                        # 🎯 处理每个子节点
                        segment_content = process_segment_content(
                            segment, variate_data, user_input, phone_info, is_root=False
                        )
                        if segment_content:
                            mixed_dict['content'].append(segment_content)
                            mixed_dict['total_duration'] += segment_content.get('duration', 0)

                            # 🎯 收集文本部分，用于构建最终文本
                            if segment_content['type'] == 'tts':
                                # TTS 片段的文本已替换变量
                                final_text_parts.append(segment_content['value'])
                            elif segment_content['type'] == 'audio':
                                # 音频片段取原始的 voice_content（不含变量）
                                audio_text = segment.get('voice_content', '')
                                if audio_text:
                                    final_text_parts.append(audio_text)

                    # 🎯 构建最终TTS文本
                    if final_text_parts:
                        final_text = ''.join(final_text_parts)
                    else:
                        # 使用根节点的voice_content或原始文本
                        final_text = dialog_info.get('voice_content', raw_content)
                        # 处理变量
                        if contains_variables(final_text):
                            final_text = replace_variables_in_text(final_text, variate_data, user_input, phone_info)
                else:
                    # 🎯 没有子节点，处理根节点
                    root_voice_content = dialog_info.get('voice_content', raw_content)

                    if contains_variables(root_voice_content):
                        # 🎯 根节点包含变量，需要替换
                        processed_text = replace_variables_in_text(root_voice_content, variate_data, user_input,
                                                                   phone_info)

                        # 创建TTS内容
                        tts_duration = calculate_tts_duration(processed_text)
                        mixed_dict['content'].append({
                            'type': 'tts',
                            'value': processed_text,
                            'duration': tts_duration,
                            'segment_type': 'text_with_variables'
                        })
                        mixed_dict['total_duration'] += tts_duration

                        # 🎯 更新final_text为处理后的文本
                        final_text = processed_text
                    else:
                        # 🎯 根节点不包含变量，正常处理
                        root_content = process_segment_content(
                            dialog_info, variate_data, user_input, phone_info, is_root=True
                        )
                        if root_content:
                            mixed_dict['content'].append(root_content)
                            mixed_dict['total_duration'] += root_content.get('duration', 0)

                        final_text = raw_content  # 使用原始文本

                # 🎯 更新播放类型
                content_types = [item['type'] for item in mixed_dict['content']]
                if all(t == 'tts' for t in content_types):
                    mixed_dict['playback_type'] = 'tts_only'
                elif all(t == 'audio' for t in content_types):
                    mixed_dict['playback_type'] = 'audio_only'
                # 否则保持 'mixed'

            mixed_list.append(mixed_dict)  # 生成返回值

            # 🎯 将final_text添加到处理后的数据中
            processed_data['final_text'] = final_text
            final_content_list.append(processed_data)  # 🎯 这里包含了所有原始字段 + final_text

        return mixed_list, final_content_list

    except Exception as e:
        logger.error(f"❌ 处理AI内容失败: {str(e)}")
        # 降级处理
        final_content_list = []
        mixed_list = []

        for content_data in content_list:
            # 🎯 同样保留原始数据
            processed_data = {}
            if isinstance(content_data, dict):
                processed_data = content_data.copy()
            else:
                processed_data = {'text': str(content_data)}

            final_text = ''
            variate_data = content_data.get('variate', {}) if isinstance(content_data, dict) else {}
            other_config = content_data.get('other_config', {}) if isinstance(content_data, dict) else {}
            fallback_content = content_data.get('text', '系统处理中，请稍候。') if isinstance(content_data,
                                                                                            dict) else str(content_data)

            # 🎯 降级时也要处理变量
            if contains_variables(fallback_content):
                fallback_content = replace_variables_in_text(fallback_content, variate_data, user_input, phone_info)

            mixed_list.append(create_simple_tts_content(fallback_content, other_config))
            processed_data['final_text'] = fallback_content
            final_content_list.append(processed_data)

        return mixed_list, final_content_list


def process_segment_content(segment, variate_data, user_input, phone_info, is_root=False):
    """处理单个对话片段
    Args:
        segment: 对话片段数据
        variate_data: 变量配置数据
        user_input: 用户输入
        phone_info: 手机信息（自定义变量来源）
        is_root: 是否是根节点（需要提取变量）
    """
    try:
        content_type = segment.get('content_type', 1)  # 1文本，2变量
        voice_content = segment.get('voice_content', '')
        voice_content_file = segment.get('voice_content_file', '')
        duration = segment.get('duration')
        if duration is None:
            audio_duration = 0.0
        else:
            try:
                audio_duration = float(duration)
            except (ValueError, TypeError):
                audio_duration = 0.0

        # 🎯 如果有录音文件，优先使用音频
        if voice_content_file:
            audio_duration = get_audio_duration(voice_content_file, audio_duration)
            return {
                'type': 'audio',
                'value': voice_content_file,
                'duration': audio_duration,
                'segment_type': 'audio'
            }

        # 🎯 处理文本内容
        if content_type == 1:  # 纯文本
            if voice_content:
                # 🎯 如果是根节点且包含变量，需要进行变量替换
                if contains_variables(voice_content):
                    processed_text = replace_variables_in_text(voice_content, variate_data, user_input, phone_info)
                    tts_duration = calculate_tts_duration(processed_text)
                    return {
                        'type': 'tts',
                        'value': processed_text,
                        'duration': tts_duration,
                        'segment_type': 'text_with_variables'
                    }
                else:
                    # 普通文本，不需要变量替换
                    tts_duration = calculate_tts_duration(voice_content)
                    return {
                        'type': 'tts',
                        'value': voice_content,
                        'duration': tts_duration,
                        'segment_type': 'text'
                    }

        elif content_type == 2:  # 变量
            # 🎯 直接提取变量名（不需要正则匹配，因为已经是纯变量格式）
            var_name = extract_variable_name(voice_content)
            if var_name:
                var_value = process_variable(var_name, variate_data, user_input, phone_info)

                if var_value:
                    tts_duration = calculate_tts_duration(var_value)
                    return {
                        'type': 'tts',
                        'value': var_value,
                        'duration': tts_duration,
                        'segment_type': 'variable',
                        'var_name': var_name
                    }

        return None

    except Exception as e:
        logger.error(f"❌ 处理对话片段失败: {str(e)}")
        return None


def contains_variables(text):
    """检查文本是否包含变量（${变量名}格式）"""
    import re
    pattern = r'\$\{(\w+)\}'
    return bool(re.search(pattern, text))


def replace_variables_in_text(text, variate_data, user_input, phone_info):
    """替换文本中的所有变量"""
    import re
    pattern = r'\$\{(\w+)\}'

    def replace_match(match):
        var_name = match.group(1)
        var_value = process_variable(var_name, variate_data, user_input, phone_info)
        # 🎯 修改：如果变量值为空或未找到，返回空字符串而不是原变量
        return var_value if var_value else ''

    return re.sub(pattern, replace_match, text)


def extract_variable_name(text):
    """从变量格式文本中提取变量名（${变量名} -> 变量名）"""
    import re
    pattern = r'\$\{(\w+)\}'
    match = re.match(pattern, text.strip())
    return match.group(1) if match else None


def process_variable(var_name, variate_data, user_input, phone_info):
    """处理变量替换
    Args:
        var_name: 变量名（不带${}）
        variate_data: 变量配置数据，键为${变量名}
        user_input: 用户输入
        phone_info: 手机信息（自定义变量来源）
    """
    try:
        # 🎯 将变量名包装成${var_name}形式去variate_data中查找
        var_key = f"${{{var_name}}}"
        if isinstance(variate_data, dict):
            var_config = variate_data.get(var_key, {})
        elif isinstance(variate_data, list):
            # 如果是列表，可以转换为字典或按索引访问
            # 根据你的业务逻辑处理
            var_config = {}  # 或者处理列表逻辑
        else:
            var_config = {}
        content_type = var_config.get('content_type', 1)  # 1自定义变量，2动态变量
        dynamic_var_set_type = var_config.get('dynamic_var_set_type', 0)  # 0未开启，1常量赋值，2原话采集
        var_is_save = var_config.get('var_is_save', 0)  # 是否保存变量

        if content_type == 1:  # 自定义变量
            # 🎯 从phone_info获取
            var_value = find_var_value_in_phone_info(var_name, phone_info.get('variate', []), var_config)
            return var_value

        elif content_type == 2:  # 动态变量
            if dynamic_var_set_type == 1:  # 常量赋值
                return var_config.get('value', '')
            elif dynamic_var_set_type == 2:  # 原话采集
                return user_input or var_config.get('value', '')

        # 🎯 默认返回配置的值
        return var_config.get('value', '')

    except Exception as e:
        logger.error(f"❌ 处理变量失败: var_name={var_name}, error={str(e)}")
        return variate_data.get(var_key, {}).get('value', '')


def find_var_value_in_phone_info(var_name, phone_info, var_config):
    """在phone_info中查找变量值，支持多级查找策略"""
    try:
        logger.info(f"✅ phone_info: {phone_info} ---var_name:{var_name} --- var_config:{var_config}" )
        # 🎯 第一级：直接按var_name查找
        for item in phone_info:
            if item.get('var_name') == var_name:
                value = item.get('var_value', '')
                if value:  # 如果找到了有效的值
                    logger.info(f"✅ 直接找到变量值: {var_name} = {value}")
                    return value

        # 🎯 第二级：如果没找到，检查var_config中的value
        config_value = var_config.get('value', '')
        if config_value:
            # 检查config_value是否是汉字（中文字符）
            if contains_chinese(config_value):
                # 🎯 修正：将config_value当作变量名，在phone_info中查找
                logger.info(f"🔍 配置值为汉字，作为变量名查找: {config_value}")
                for item in phone_info:
                    if item.get('var_name') == config_value:
                        value = item.get('var_value', '')
                        if value:
                            logger.info(f"✅ 通过汉字变量名找到值: {config_value} = {value}")
                            return value
                logger.warning(f"⚠️ 汉字变量名未找到: {config_value}")
                return ''  # 没找到返回空

            # 检查config_value是否可以转换为大于0的数字
            try:
                config_num = float(config_value)
                if config_num > 0:
                    # 🎯 通过var_id在phone_info中查找
                    var_id = str(int(config_num))  # 转换为整数再转字符串，避免小数
                    for item in phone_info:
                        if str(item.get('var_id', '')) == var_id:
                            value = item.get('var_value', '')
                            if value:
                                logger.info(f"✅ 通过var_id找到变量值: var_id={var_id}, {var_name} = {value}")
                                return value
                    logger.warning(f"⚠️ 通过var_id未找到变量: var_id={var_id}")
                    return ''  # 没找到返回空
            except (ValueError, TypeError):
                # 如果不能转换为数字，将config_value当作变量名再次查找
                logger.info(f"🔍 配置值非数字，作为变量名查找: {config_value}")
                for item in phone_info:
                    if item.get('var_name') == config_value:
                        value = item.get('var_value', '')
                        if value:
                            logger.info(f"✅ 通过配置变量名找到值: {config_value} = {value}")
                            return value
                logger.warning(f"⚠️ 配置变量名未找到: {config_value}")
                return ''  # 没找到返回空

        # 🎯 如果所有查找都失败，返回空字符串
        logger.warning(f"⚠️ 未找到变量值: {var_name}")
        return ''

    except Exception as e:
        logger.error(f"❌ 在phone_info中查找变量失败: var_name={var_name}, error={str(e)}")
        return ''


def contains_chinese(text):
    """检查文本是否包含中文字符"""
    import re
    pattern = re.compile(r'[\u4e00-\u9fff]')
    return bool(pattern.search(str(text)))


def get_audio_duration(file_path, length):
    """获取音频文件时长"""
    try:
        # 🎯 如果有预计算的时长，直接使用
        if length and length > 0:
            return float(length)

        # 🎯 如果没有预计算的时长，根据文件路径估算
        if file_path:
            # 这里可以根据实际情况实现更精确的估算
            # 暂时返回一个估计值
            return 8.0  # 默认3秒

        return 0
    except Exception as e:
        logger.error(f"❌ 获取音频时长失败: {str(e)}")
        return length


def create_simple_tts_content(text, other_config):
    """创建简单的TTS内容（降级方案）"""
    duration = calculate_tts_duration(text)
    return {
        'playback_type': 'tts_only',
        'content': [{
            'type': 'tts',
            'value': text,
            'duration': duration
        }],
        'total_duration': duration,
        'allow_bargein': True,
        'other_config': other_config
    }


@app.route('/gateway/health', methods=['GET'])
def health_check():
    """健康检查"""
    try:
        # 检查AI模型服务状态
        model_health = requests.get(f"{AI_MODEL_SERVICE_URL}/health", timeout=5)
        model_status = model_health.json() if model_health.status_code == 200 else {'status': 'unreachable'}

        # 检查Redis连接
        redis_status = 'healthy' if redis_client.ping() else 'unhealthy'

    except Exception as e:
        model_status = {'status': f'unreachable: {str(e)}'}
        redis_status = 'unhealthy'

    return jsonify({
        'status': 'healthy',
        'service': 'ai_gateway',
        'version': GATEWAY_VERSION,
        'timestamp': datetime.now().isoformat(),
        'dependencies': {
            'ai_model_service': model_status,
            'redis': redis_status
        },
        'statistics': gateway_manager.stats
    })


@app.route('/gateway/model/start', methods=['POST'])
def start_model():
    """初始化模型接口 - 异步版本"""

    data = request.json
    model_id = data.get('model_id')
    config_data = data.get('config_data', {})
    expire_time = data.get('expire_time')
    only_delay = data.get('only_delay', False)
    is_again = data.get('is_again', False)
    if not model_id:
        return jsonify({
            'success': False,
            'message': 'model_id 参数不能为空'
        }), 400

    logger.info(f"🚀 接收模型启动请求 - 模型: {model_id}, 仅延期: {only_delay}")
    # 重新激活 先删除再激活
    # 重新激活模式：先删除再激活
    if is_again:
        logger.info(f"🔄 重新激活模式 - 先删除模型: {model_id}")
        try:
            response = requests.post(
                f"{AI_MODEL_SERVICE_URL}/model/again",
                json={
                    'model_id': model_id,
                },
                timeout=10
            )

            # 检查删除是否成功
            if response.status_code == 200 and response.json().get('success'):
                # 删除成功后，继续执行下面的逻辑
                # 但这里需要确保 only_delay=False，因为我们要重新初始化
                only_delay = False  # 强制设为False，执行完整初始化
            else:
                error_msg = response.json().get('message', '未知错误')
                # 删除失败，直接返回错误
                return jsonify({
                    'success': False,
                    'message': f'模型 {model_id} 删除失败: {error_msg}',
                    'model_id': model_id
                }), 500

        except Exception as e:

            return jsonify({
                'success': False,
                'message': f'模型 {model_id} 删除失败: {str(e)}',
            }), 500
    if only_delay:
        # 只延期模式 - 同步处理（快速）
        try:
            payload = {
                'model_id': model_id,
                'expire_time': expire_time,
                'action': 'extend_only'
            }
            response = requests.post(
                f"{AI_MODEL_SERVICE_URL}/model/extend",
                json=payload,
                timeout=10
            )
            if response.status_code == 200 and response.json().get('success'):
                return jsonify({
                    'success': True,
                    'message': f'模型 {model_id} 过期时间已延长',
                    'model_id': model_id
                })
            else:
                return jsonify({
                    'success': False,
                    'message': f'模型 {model_id} 延期失败'
                }), 500
        except Exception as e:
            return jsonify({
                'success': False,
                'message': f'模型延期请求失败: {str(e)}'
            }), 500
    else:
        # 完整初始化模式 - 异步处理
        async_initialize_model(model_id, config_data, expire_time)
        return jsonify({
            'success': True,
            'message': f'模型 {model_id} 初始化请求已提交，正在后台处理',
            'model_id': model_id,
            'async': True
        })

# 其他接口保持不变...
@app.route('/gateway/conversation', methods=['POST'])
def conversation():
    """对话接口"""
    data = request.json
    print(data, '对话接口请求数据')
    call_id = data.get('call_id')
    model_id = data.get('model_id', 'default')
    backstop_model = data.get('backstop_model', 'default')
    task_id = data.get('task_id')
    current_input = data.get('current_input', '')
    original_number = data.get('original_number', '')
    user_start_time = data.get('user_start_time', '')
    user_end_time = data.get('user_end_time', '')

    # 🆕 获取所有ASR配置参数
    not_answer_wait_seconds = data.get('not_answer_wait_seconds', 0)

    check_noise = data.get('check_noise', 0)  # 噪音检测 是不是nlp 需要用的

    if not task_id:
        return jsonify({
            'success': False,
            'message': 'task_id 参数不能为空'
        }), 400

    logger.info(f"📞 处理对话请求 - 任务: {task_id}, 呼叫: {call_id}")

    # 从Redis获取对话历史
    conversation_key = f"{settings.REDIS_PRE}:call:conversation:{call_id}"
    try:
        existing_conversation = redis_client.get(conversation_key)
    except redis.RedisError as e:
        logger.error(f"🔴 Redis连接异常: {str(e)}")
        # 🎯 降级处理：使用空的历史记录继续处理
        existing_conversation = None
    
    logger.info(f"📞ai模型请求处理开始------")


    if existing_conversation:
        conversation_data = json.loads(existing_conversation)
        actual_model_id = conversation_data.get('actual_model_id', model_id)
    else:
        actual_model_id = model_id  # 初始使用主模型
        conversation_data = {
            'call_id': call_id,
            'task_id': task_id,
            'model_id': model_id,
            'actual_model_id': actual_model_id,
            'backstop_model': backstop_model,
            'start_time': time.time(),
            'metadata': {}  # 🎯 新增详细历史存储
        }
    # 🎯 调用AI模型服务生成话术
    content_list, updated_history_detail, used_model_id, end_call = call_model_service(
        actual_model_id, backstop_model, current_input, call_id, task_id
    )
    print(content_list, 'content_list')
    print(updated_history_detail, 'updated_history_detail')
    print(used_model_id, 'used_model_id')
    print(end_call, 'end_call')

    # 🎯 更新实际使用的模型ID（如果发生了切换）
    if used_model_id != actual_model_id:
        old_model_id = actual_model_id
        actual_model_id = used_model_id
        logger.info(f"🔄 模型切换: {old_model_id} -> {actual_model_id}")

    # 🎯 处理AI返回的content字典
    mixed_list, final_list = process_ai_content(task_id, original_number, content_list, current_input, actual_model_id)
    print(final_list, '-----------final_list')
    # 更新详细历史记录（metadata）
    # 🎯 更新详细历史记录（metadata）
    if updated_history_detail:
        # 获取当前轮次的数据（最后一条）
        current_round_data = updated_history_detail[-1].copy() if updated_history_detail else {}

        # 🎯 更新当前轮次的数据
        current_round_data.update({
            'content': final_list,  # 使用处理后的final_list
            'robot_model_id': actual_model_id,
            'user_start_time': user_start_time,
            'user_end_time': user_end_time
        })

        # 获取Redis中现有的metadata
        existing_metadata = conversation_data.get('metadata', [])

        # 🆕 确保existing_metadata是列表
        if not isinstance(existing_metadata, list):
            logger.warning(f"⚠️ metadata不是列表类型，重置为空列表: {type(existing_metadata)}")
            existing_metadata = []

        # 🎯 检查是否已经有当前轮次的记录（根据reply_round判断）
        current_round_index = -1
        if current_round_data.get('reply_round'):
            for i, item in enumerate(existing_metadata):
                if item.get('reply_round') == current_round_data.get('reply_round'):
                    current_round_index = i
                    break
        else:
            # 如果没有reply_round，假设最后一条是当前轮次
            current_round_index = len(existing_metadata) - 1 if existing_metadata else -1

        if current_round_index >= 0:
            # 更新现有记录
            existing_metadata[current_round_index] = current_round_data
            logger.info(f"✅ 更新metadata第{current_round_index}条记录")
        else:
            # 添加新记录
            existing_metadata.append(current_round_data)
            logger.info(f"✅ 新增metadata第{len(existing_metadata)}条记录")

        # 更新conversation_data中的metadata
        conversation_data['metadata'] = existing_metadata
        logger.info(f"✅ metadata更新完成，现有{len(existing_metadata)}条记录")
    conversation_data['actual_model_id'] = actual_model_id
    conversation_data['last_update'] = time.time()
    conversation_data['variables_processed'] = True  # 标记变量已处理
    redis_client.setex(conversation_key, 3600, json.dumps(conversation_data))

    # 自动绑定任务到实际使用的模型
    gateway_manager.bind_task_to_model(task_id, actual_model_id)
    response = {
        'success': True,
        'action': 'speak',
        'end_call': end_call,
        'task_id': task_id,
        'model_id': actual_model_id,
        'call_id': call_id,
        'next_step': 'wait_input',
        'list': [],
    }
    for mixed_content in mixed_list:
        # 🎯 使用处理后的TTS文本来计算时长
        tts_duration = mixed_content['total_duration']
        other_config = mixed_content['other_config']
        mixed_content.pop('other_config', None)
        # 🎯 计算最终超时时间（使用final_text或mixed_content的总时长）
        ai_wait_time = other_config.get('wait_time') if other_config else None
        final_asr_timeout, final_tts_duration = calculate_final_timeout(tts_duration, not_answer_wait_seconds,
                                                                        ai_wait_time)
        # 动态ASR参数
        dynamic_params = {
            'asr_no_input_timeout': final_asr_timeout,
            'tts_duration': final_tts_duration,
            'asr_speech_timeout': 15000,
            'asr_sensitivity': 0.8,
            'tts_voice': 'xiaoyan',
            'tts_speed': 1.0,
            'barge_in_enabled': True,
            # 🆕 AI返回的动态配置（完整传递）
            'other_config': other_config
        }
        # 🎯 应用AI返回的动态参数
        if other_config:
            # 打断控制
            if 'is_break' in other_config:
                dynamic_params['barge_in_enabled'] = (other_config['is_break'] == 1)
            # no_asr 传递给Lua 目前lua只接收了还没有处理 延迟识别用户说话 0 是不开启 -1 播报结束开始识别用户说话 1-20 播报开始后几秒开始识别
            if 'no_asr' in other_config:
                dynamic_params['no_asr'] = other_config['no_asr']

        response['list'].append({
            'content': mixed_content,
            'dynamic_params': dynamic_params,
        })

    logger.info(f"✅ 对话响应生成 - 结果: {response}")
    logger.info(f"✅ 对话响应生成 - 任务: {task_id}, 呼叫: {call_id}, 结束通话: {end_call}")
    return jsonify(response)


@app.route('/gateway/destroy', methods=['POST'])
def destroy_model():
    """销毁模型"""
    data = request.json
    model_id = data.get('model_id')
    force = data.get('force', False)
    try:
        # 检查AI模型服务状态
        response = requests.post(
            f"{AI_MODEL_SERVICE_URL}/model/destroy",
            json={
                'model_id': model_id,
                'force': force,
            },
            timeout=10
        )
        if response.status_code == 200 and response.json().get('success'):
            return jsonify({
                'success': True,
                'message': f'模型 {model_id} 已删除',
                'model_id': model_id
            })
        else:
            return jsonify({
                'success': False,
                'message': f'模型 {model_id} 删除失败',
                'error': response.json().get('message')
            })


    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'模型 {model_id} 删除失败{str(e)}',
        }), 500


@app.route("/gateway/keyword_match", methods=["POST"])
def match_keywords():
    try:
        data = request.get_json(silent=True)
        if not data:
            return jsonify({"error": "无效JSON"}), 400

        keywords = data.get("keywords")
        sentence = data.get("sentence")

        # Input validation
        if not isinstance(keywords, list):
            return jsonify({"error": "关键词输入应为列表"}), 400
        if not keywords or not isinstance(sentence, str) or not sentence.strip():
            return jsonify({"matched": False})

        intention_list = [{
            "intention_id": "keyword_matching_service",
            "intention_name": "关键词匹配服务",
            "keywords": keywords
        }]
        matcher = KeywordMatcher(intention_list)
        result = matcher.analyze_sentence(sentence)
        return jsonify({"matched": bool(result)})

    except Exception as e:
        logger.error(f"关键词匹配错误: {str(e)}")
        return jsonify({"error": "关键词匹配错误"}), 500

@app.route('/gateway/audio_edges', methods=['POST'])
def trim_audio_edges():
    """
    只去除头尾的空白，保留中间的静音
    """
    try:
        data = request.get_json(silent=True)
        if not data:
            return jsonify({"error": "无效JSON"}), 400
        
        input_path = data.get("input_path")
        output_path = data.get("output_path")
        
        if not input_path or not output_path:
            return jsonify({"error": "缺少必要参数: input_path 或 output_path"}), 400
        def convert_php_path_to_container(php_path):
            """
            将 PHP 传来的宿主机路径转换为容器内路径
            """
            # 定义路径映射
            mappings = {
                '/data/gitdata/git_beta_web/call_center/static/uploads': '/app/uploads',
            }
            
            for host_path, container_path in mappings.items():
                if php_path.startswith(host_path):
                    new_path = php_path.replace(host_path, container_path, 1)
                    logger.info(f"路径映射: {php_path} -> {new_path}")
                    return new_path
            
            # 如果没有映射，返回原路径并记录警告
            logger.warning(f"路径未映射，可能无法访问: {php_path}")
            return php_path
        
        original_input_path = input_path  # 保存原始路径用于日志
        input_path = convert_php_path_to_container(input_path)
        output_path = convert_php_path_to_container(output_path)
        
        logger.info(f"原始输入路径: {original_input_path}")
        logger.info(f"转换后输入路径: {input_path}")
        logger.info(f"转换后输出路径: {output_path}")
        # 验证输入文件是否存在
        if not os.path.exists(input_path):
            return jsonify({"error": f"输入文件不存在: {input_path}"}), 400
        
        # 设置参数
        silence_thresh = data.get("silence_thresh", -40)
        min_silence_len = data.get("min_silence_len", 500)
        # 加载音频文件
        try:
            audio = AudioSegment.from_file(input_path)
        except Exception as e:
            return jsonify({"error": f"加载音频文件失败: {str(e)}"}), 400
        
        original_duration = len(audio) / 1000.0
        original_size = os.path.getsize(input_path)
        
        # 检测所有非静音部分
        non_silent_ranges = detect_nonsilent(
            audio,
            min_silence_len=min_silence_len,
            silence_thresh=silence_thresh
        )
        
        if not non_silent_ranges:
            return jsonify({
                "success": False,
                "message": "未检测到有效音频内容",
                "original_duration": original_duration
            })
        
        # 只取第一个和最后一个非静音段
        start_time = non_silent_ranges[0][0]
        end_time = non_silent_ranges[-1][1]
        
        # 裁剪音频
        trimmed_audio = audio[start_time:end_time]
        trimmed_duration = len(trimmed_audio) / 1000.0
        
        # 确保输出目录存在
        output_dir = os.path.dirname(output_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
        
        # 获取文件扩展名
        file_ext = output_path.split('.')[-1].lower()
        
        # 关键：设置优化的导出参数以减少文件大小
        export_params = {}
        
        if file_ext in ['wav', 'wave']:
            # WAV 文件：使用压缩的 PCM 格式
            export_params = {
                'format': 'wav',
                'parameters': ['-acodec', 'pcm_s16le','-ar', '16000', '-ac', '1']  # 16-bit PCM，最常用
            }
        elif file_ext == 'mp3':
            # MP3 文件：使用优化的比特率
            export_params = {
                'format': 'mp3',
                'bitrate': '64k',  # 中等质量，文件较小
                'parameters': ['-q:a', '4','-ar', '16000', '-ac', '1' ]  # VBR 质量参数（0-9，0最好）
            }
        elif file_ext in ['m4a', 'aac', 'mp4']:
            
            export_params = {
                'format': 'ipod',  # 对于 M4A 格式，使用 'ipod' 格式
                'codec': 'aac',
                'bitrate': '64k',
                'parameters': [
                    '-c:a', 'aac',
                    '-b:a', '64k',
                    '-ar', '16000',
                    '-ac', '1',
                    '-profile:a', 'aac_low'
                ]
            }
        else:
            # 其他格式使用默认参数
            export_params = {
                'format': file_ext, 
                'parameters': ['-ar', '16000', '-ac', '1']  # 设置采样率为16000Hz
            }
        
        # 保存文件
        # 特殊处理 M4A 格式
        if file_ext in ['m4a', 'aac', 'mp4']:
            # 对于 M4A 格式，使用不同的导出方式确保兼容性
            temp_wav = output_path + '.wav'
            
            # 先导出为 WAV
            trimmed_audio.export(temp_wav, format='wav')
            
            try:
                # 使用 ffmpeg 转换到 M4A
                import subprocess
                ffmpeg_cmd = [
                    'ffmpeg',
                    '-i', temp_wav,
                    '-c:a', 'aac',
                    '-b:a', '64k',
                    '-ar', '16000',
                    '-ac', '1',
                    '-profile:a', 'aac_low',
                    '-y',  # 覆盖输出文件
                    output_path
                ]
                
                result = subprocess.run(ffmpeg_cmd, capture_output=True, text=True)
                if result.returncode != 0:
                    raise Exception(f"FFmpeg 转换失败: {result.stderr}")
                    
            finally:
                # 清理临时文件
                if os.path.exists(temp_wav):
                    os.remove(temp_wav)
        else:
            # 其他格式使用 pydub 直接导出
            trimmed_audio.export(output_path, **export_params)
        
        
        # 获取输出文件信息
        output_size = os.path.getsize(output_path)
        
        # 只输出音频文件的关键参数
        logger.info(f"🎵 音频处理完成:")
        logger.info(f"  原始文件: {original_duration:.2f}s, {original_size/1024:.1f}KB")
        logger.info(f"  裁剪后文件: {trimmed_duration:.2f}s, {output_size/1024:.1f}KB")
        
        
        return jsonify({
            "success": True,
            "message": "音频裁剪成功",
            "audio_info": {
                "original_duration": round(original_duration, 2),
                "original_size_kb": round(original_size/1024, 1),
                "trimmed_duration": round(trimmed_duration, 2),
                "trimmed_size_kb": round(output_size/1024, 1),
                "sample_rate": audio.frame_rate,
                "channels": audio.channels,
                "bit_depth": audio.sample_width * 8,
                "format": file_ext,
                "export_params": export_params
            },
            "trim_info": {
                "start_time": start_time,
                "end_time": end_time,
                "non_silent_segments": len(non_silent_ranges)
            },
            "output_path": output_path
        })
        
    except Exception as e:
        logger.error(f"处理音频时出错: {str(e)}")
        
        return jsonify({"error": f"处理音频时出错: {str(e)}"}), 500
@app.route('/gateway/audio_merger', methods=['POST'])
def audio_merger():
    try:
        data = request.get_json(silent=True)
        if not data:
            return jsonify({"error": "无效JSON"}), 400
        
        input_path = data.get("input_path")
        output_path = data.get("output_path")
        
        if not input_path or not output_path:
            return jsonify({"error": "缺少必要参数: input_path 或 output_path"}), 400
        def convert_php_path_to_container(php_path):
            """
            将 PHP 传来的宿主机路径转换为容器内路径
            """
            # 定义路径映射
            mappings = {
                '/data/gitdata/git_beta_web/call_center/static/uploads': '/app/uploads',
            }
            
            for host_path, container_path in mappings.items():
                if php_path.startswith(host_path):
                    new_path = php_path.replace(host_path, container_path, 1)
                    logger.info(f"路径映射: {php_path} -> {new_path}")
                    return new_path
            
            # 如果没有映射，返回原路径并记录警告
            logger.warning(f"路径未映射，可能无法访问: {php_path}")
            return php_path
        input_paths = []
        if isinstance(input_path, list):
            # 数组形式
            for i, path in enumerate(input_path):
                if not isinstance(path, str):
                    return jsonify({"error": f"input_path[{i}] 不是字符串"}), 400
                
                container_path = convert_php_path_to_container(path)
                input_paths.append(container_path)
                
                logger.info(f"输入文件 {i+1}: {path} -> {container_path}")
                
        elif isinstance(input_path, str):
            # 单个文件
            container_path = convert_php_path_to_container(input_path)
            input_paths.append(container_path)
            logger.info(f"单个输入文件: {input_path} -> {container_path}")
        else:
            return jsonify({"error": f"input_path 类型错误: {type(input_path)}"}), 400
        output_path = convert_php_path_to_container(output_path)
        logger.info(f"转换后输出路径: {output_path}")
        # 验证输入文件是否存在
        missing_files = []
        for i, path in enumerate(input_paths):
            if not os.path.exists(path):
                missing_files.append({
                    "index": i,
                    "path": path
                })
        
        if missing_files:
            error_msg = "以下文件不存在:\n"
            for file_info in missing_files:
                error_msg += f"  文件{file_info['index']+1}: {file_info['path']}\n"
            return jsonify({"error": error_msg}), 400
        bitrate = "64k"
        sample_rate = int(16000)
        channels = int(1)
        logger.info(f"合并参数: 比特率={bitrate}, 采样率={sample_rate}, 声道={channels}")
        logger.info(f"开始合并 {len(input_paths)} 个WAV文件...")
        temp_dir = tempfile.mkdtemp(prefix="audio_merge_")
        logger.info(f"临时目录: {temp_dir}")
        try:
            result = _merge_multiple_wavs_simple(
                input_paths,
                output_path,
                temp_dir,
                sample_rate,
                channels,
            )
            if result["success"]:
                # 验证输出文件
                if not os.path.exists(output_path):
                    return jsonify({"error": "合并成功但输出文件不存在"}), 500
                
                file_size = os.path.getsize(output_path)
                
                
                logger.info(f"✅ 合并成功: {output_path}")
                
                
                return jsonify({
                    "success": True,
                    "message": f"成功合并 {len(input_paths)} 个WAV文件",
                    "data": {
                        "file_size": file_size,
                    }
                })
            else:
                return jsonify({"error": result["error"]}), 500
                
        finally:
            # 清理临时文件
            _cleanup_temp_dir(temp_dir)
    except Exception as e:
        logger.error(f"合并音频时出错: {str(e)}")
        return jsonify({"error": f"合并音频时出错: {str(e)}"}), 500
    
def _merge_multiple_wavs_simple(input_paths, output_path, temp_dir, 
                               sample_rate=16000, channels=1):
    """合并多个WAV文件 - 使用交叉淡入淡出处理衔接"""
    try:
        # 为每个输入音频流添加0.5秒静音垫片（apad），然后再拼接
        filter_chains = []
        concat_inputs = []
        pad_duration = 0.5
        for i in range(len(input_paths)):
            if i < len(input_paths) - 1:
                filter_chains.append(f"[{i}:a]apad=pad_dur={pad_duration}[pad{i}]")
            else:
                filter_chains.append(f"[{i}:a]anull[pad{i}]")  # 直接映射，无垫片
            concat_inputs.append(f"[pad{i}]")
        
        # 连接所有添加了静音垫片的音频流
        filter_complex = f"{';'.join(filter_chains)};{''.join(concat_inputs)}concat=n={len(input_paths)}:v=0:a=1[out]"
        
        # 3. 构建FFmpeg命令
        ffmpeg_cmd = ['ffmpeg', '-y']
        
        # 添加所有输入文件
        for file_path in input_paths:
            ffmpeg_cmd.extend(['-i', file_path])
        
        # 添加滤镜和输出参数
        ffmpeg_cmd.extend([
            '-filter_complex', filter_complex,
            '-map', '[out]',          # 映射输出流
            '-c:a', 'pcm_s16le',     # 输出格式：16-bit PCM WAV
            '-ar', str(sample_rate), # 采样率
            '-ac', str(channels),    # 声道数
            output_path
        ])
        
        logger.info(f"执行合并命令: {' '.join(ffmpeg_cmd)}")
        
        # 4. 执行命令
        result = subprocess.run(
            ffmpeg_cmd,
            capture_output=True,
            text=True,
            timeout=180  # 3分钟超时
        )
        
        if result.returncode != 0:
            logger.error(f"合并失败，错误: {result.stderr}")
            return {"success": False, "error": f"合并失败: {result.stderr[:200]}"}
        
        logger.info("✅ 文件合并成功")
        return {"success": True}
        
    except subprocess.TimeoutExpired:
        logger.error("合并处理超时")
        return {"success": False, "error": "处理超时"}
    except Exception as e:
        logger.error(f"合并过程出错: {str(e)}")
        return {"success": False, "error": str(e)}
       
def _cleanup_temp_dir(temp_dir):
    """清理临时目录"""
    try:
        import shutil
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
            logger.info(f"清理临时目录: {temp_dir}")
    except Exception as e:
        logger.warning(f"清理临时目录失败: {str(e)}")    
def check_model_service_health():
    """检查AI模型服务健康状态"""
    try:
        response = requests.get(f"{AI_MODEL_SERVICE_URL}/health", timeout=5)
        if response.status_code == 200:
            health_data = response.json()
            logger.info(f"✅ AI模型服务状态: {health_data.get('status', 'unknown')}")
            logger.info(f"📊 当前模型数: {health_data.get('model_stats', {}).get('total_models', 0)}")
            return True
        else:
            logger.warning(f"⚠️ AI模型服务响应异常: {response.status_code}")
            return False
    except Exception as e:
        logger.error(f"❌ 无法连接到AI模型服务: {str(e)}")
        return False


def start_gateway_service(port=5001):
    """启动AI网关服务"""
    logger.info(f"🚀 启动AI网关服务，端口: {port}")
    logger.info(f"📋 服务版本: {GATEWAY_VERSION}")
    logger.info(f"🔗 AI模型服务: {AI_MODEL_SERVICE_URL}")
    logger.info("✅ 网关服务初始化完成，等待请求...")
    # 🎯 检查依赖服务状态
    if not check_model_service_health():
        logger.warning("⚠️ AI模型服务可能不可用，但网关服务将继续启动")

    app.run(host='0.0.0.0', port=port, debug=False, threaded=True, use_reloader=False)


if __name__ == '__main__':
    # content_data = {
    #     "dialog_id":"1a7bea9490fd52c3",
    #     "content":"咱们现在不考虑也可以先过来了解一下目前装修市场的人工材料的费用,地址是${地址}",
    #     "variate":{
    #       "${地址}":{
    #         "content_type":1, # 1 自定义 2 动态变量
    #         "dynamic_var_set_type":1, # 0 未开启动态变量 1 常量赋值 2 原话采集
    #         "value":"财库国际",
    #         "var_is_save":0
    #       }
    #     }
    # }
    # actual_model_id = 'bb974aff6714d376'
    # user_input = '测试原话采集'
    # task_id = 1
    # original_number = '18631184126'
    # mixed_content, final_tts_text = process_ai_content(task_id, original_number, content_data, user_input, actual_model_id)
    # print(mixed_content, 'mixed_content')
    # print(final_tts_text, 'final_tts_text')
    # exit()
    start_gateway_service()