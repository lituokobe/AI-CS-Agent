import hashlib
import threading
import time
import asyncio
from pymilvus import MilvusClient, AsyncMilvusClient, MilvusException
from pymilvus.milvus_client import IndexParams
from common.logger import setup_logger
from functionals.embedding_functions import embed_documents

logger = setup_logger('milvus', category='milvus', console_output=True)

#TODO: sync Milvus client
class LaunchMilvus:
    def __init__(self, vector_db_url: str, collection_name: str, intentions: list|None = None, knowledge: list|None = None):
        self.client = MilvusClient(uri = vector_db_url, secure=False)
        self.collection_name = collection_name
        self.merged_data = (intentions or []) + (knowledge or [])
        self._ensure_collection_ready(self.merged_data)
        self.dimension:int = 1024 # dimension from the embedding model: BGE, Qwen0.6B - 1024; Qwen4B - 2560

    def _generate_phrase_id(self, intention_id: str, phrase: str) -> int:
        """Generate a deterministic ID for a phrase."""
        hash_str = hashlib.sha256(f"{intention_id}:{phrase}".encode()).hexdigest()
        # Convert to int and mask to 63 bits (safe for INT64)
        return int(hash_str[:16], 16) & ((1 << 63) - 1)

    def _ensure_collection_ready(self, merged_data: list|None = None):
        """Ensure collection exists and is ready with data."""
        # if collection doesn't exist, create it.
        if not self.client.has_collection(self.collection_name):
            self._create_collection()
            self._create_hnsw_index()
            logger.info(f"已创建新的collection：{self.collection_name}和HNSW index")
        else:
            self._ensure_hnsw_index()
            logger.info(f"Collection：{self.collection_name}已存在，使用已有的HNSW index")

        # Always upsert latest data
        if merged_data:
            self._upsert_intention_data(merged_data)

        # Ensure the collection is loaded
        self.client.load_collection(self.collection_name, timeout=30)

    def _create_collection(self):
        """Create the Milvus collection schema."""
        self.client.create_collection(
            collection_name=self.collection_name,
            dimension = self.dimension,
            metric_type="COSINE",
            auto_id=False,  # We manage IDs by ourselves
            primary_field="id",
            extra_fields=[
                {"name": "id", "data_type": "INT64", "is_primary": True},
                {"name": "intention_id", "data_type": "VARCHAR", "max_length": 512},
                {"name": "intention_name", "data_type": "VARCHAR", "max_length": 512},
                {"name": "phrase", "data_type": "VARCHAR", "max_length": 4096},
            ]
        )
        logger.info(f"已创建向量数据库collection：{self.collection_name}")

    def _create_hnsw_index(self):
        """Create HNSW index - called only once when collection is created."""
        try:
            # First, drop any existing indexes on the vector field
            existing_indexes = self.client.list_indexes(self.collection_name)
            for index_name in existing_indexes:
                try:
                    self.client.release_collection(self.collection_name)
                    self.client.drop_index(self.collection_name, index_name)
                    logger.info(f"向量数据库collection：{self.collection_name}已删除现有index：{index_name}")
                except Exception as e:
                    logger.warning(f"向量数据库collection：{self.collection_name}删除index{index_name}时发生警告：{str(e)}")
            # Create HNSW index
            index_params = IndexParams()
            index_params.add_index(
                field_name="vector",
                index_type="HNSW",
                metric_type="COSINE",
                params={"M": 16, "efConstruction": 200}
            )
            self.client.create_index(
                collection_name=self.collection_name,
                index_params=index_params
            )
            logger.info(f"向量数据库collection：{self.collection_name}已创建向量数据库HNSW index")
        except MilvusException as e:
            logger.error(f"向量数据库collection：{self.collection_name}创建HNSW index时发生错误：{str(e)}")
            raise RuntimeError(str(e))

    def _ensure_hnsw_index(self):
        """Ensure HNSW index exists, create if missing or wrong type."""
        try:
            self.client.release_collection(self.collection_name)
            existing_indexes = self.client.list_indexes(self.collection_name)

            if not existing_indexes:
                # No index exists, create HNSW
                self._create_hnsw_index()
                return

            # Check if HNSW index exists
            hnsw_exists = False
            for index_name in existing_indexes:
                try:
                    index_info = self.client.describe_index(self.collection_name, index_name)
                    if (index_info.get('index_type') == 'HNSW' and
                            index_info.get('metric_type') == 'COSINE'):
                        hnsw_exists = True
                        logger.info(f"向量数据库collection：{self.collection_name}HNSW index已存在，index名称为{index_name}")
                        break
                except Exception as e:
                    logger.warning(f"向量数据库collection：{self.collection_name}检查index{index_name}时发生警告: {str(e)}")

            if not hnsw_exists:
                # Existing index is not HNSW, replace it
                logger.info(f"向量数据库collection：{self.collection_name}现有index不是HNSW类型，替换为HNSW")
                self._create_hnsw_index()

        except Exception as e:
            logger.error(f"向量数据库collection：{self.collection_name}检查HNSW index时发生错误：{str(e)}")
            raise RuntimeError(str(e))

    def _upsert_intention_data(self, merged_data: list):
        """Upsert intention data - index automatically handles new vectors."""
        upsert_data = []
        embedding_tasks = []
        BATCH_SIZE = 50
        for item in merged_data:
            intention_id = item.get("intention_id")
            intention_name = item.get("intention_name")
            for phrase in item.get("semantic", []):
                clean_phrase = phrase.strip()
                if clean_phrase:  # skip empty
                    embedding_tasks.append(
                        {
                            "phrase": clean_phrase,
                            "intention_id": intention_id,
                            "intention_name": intention_name,
                        }
                    )

        for i in range(0, len(embedding_tasks), BATCH_SIZE):
            batch_tasks = embedding_tasks[i : i + BATCH_SIZE]
            batch_phrases = [task["phrase"] for task in batch_tasks]

            # Fetch batched embeddings (1 HTTP request instead of 50)
            batch_embeddings = embed_documents(batch_phrases)

            # Reconstruct the data for Milvus
            for task, embedding in zip(batch_tasks, batch_embeddings):
                # Note: The server already returns a Python list, so .tolist() is no longer needed!
                if len(embedding) != self.dimension:
                    e_m = f"向量数据库collection：{self.collection_name}向量维度应为{self.dimension}，目前为{len(embedding)}"
                    logger.error(e_m)
                    raise ValueError(e_m)

                phrase_id = self._generate_phrase_id(
                    task["intention_id"], task["phrase"]
                )
                upsert_data.append(
                    {
                        "id": phrase_id,
                        "vector": embedding,
                        "intention_id": task["intention_id"],
                        "intention_name": task["intention_name"],
                        "phrase": task["phrase"],
                    }
                )

        if not upsert_data:
            logger.info(f"没有问法短语插入向向量数据库collection：{self.collection_name}")
            return

        # Upsert (insert or replace)
        self.client.upsert(collection_name=self.collection_name, data=upsert_data)
        logger.info(f"更新{len(upsert_data)}条问法短语到向量数据库collection：{self.collection_name}")

    def get_index_info(self):
        """Get information about current index."""
        try:
            existing_indexes = self.client.list_indexes(self.collection_name)
            index_info_list = []
            for index_name in existing_indexes:
                index_info = self.client.describe_index(self.collection_name, index_name)
                index_info_list.append({
                    'name': index_name,
                    'info': index_info
                })
            return index_info_list
        except Exception as e:
            logger.error(f"向量数据库collection：{self.collection_name}获取index信息时发生错误：{str(e)}")
            return []

#TODO: async Milvus client
class LaunchMilvusAsync:
    def __init__(
            self,
            vector_db_url: str,
            collection_name: str,
            intentions: list|None = None,
            knowledge: list|None = None
    ):
        self.client = AsyncMilvusClient(uri = vector_db_url, secure=False)
        self.collection_name = collection_name
        self.merged_data = (intentions or []) + (knowledge or [])
        self.embedding_cache = {}  # Embedding cache to avoid redundant computation
        self._stats = {
            "embeddings_generated": 0,
            "embeddings_cached": 0,
            "total_phrases_processed": 0
        }
        self._cache_lock = asyncio.Lock()
        self._max_cache_size = 10000
        self.limit = 10000 # limit for collection client query
        self.dimension = 1024 # dimension from the embedding model: BGE, Qwen0.6B - 1024; Qwen4B - 2560

    def _generate_phrase_id(self, intention_id: str, phrase: str) -> int:
        """Generate a deterministic ID for a phrase."""
        hash_str = hashlib.sha256(f"{intention_id}:{phrase}".encode()).hexdigest()
        # Convert to int and mask to 63 bits (safe for INT64)
        return int(hash_str[:16], 16) & ((1 << 63) - 1)

    async def ensure_collection_ready(self):
        """Ensure collection exists and is ready with data."""
        start_time = time.time()
        logger.info(f"开始处理向量数据库collection：{self.collection_name}")

        has_collection = False

        # if collection doesn't exist, create it.
        try:
            has_collection = await self.client.has_collection(self.collection_name, timeout=20.0)  # AWAIT
        except asyncio.TimeoutError:
            logger.error(f"向量数据库collection：{self.collection_name} 连接超时 (20秒)")
            return None
        except Exception as e:
            logger.error(f"查询向量数据库collection：{self.collection_name} 是否存在失败: {str(e)}")
            return None

        if not has_collection:
            await self._create_collection()
            await self._create_hnsw_index()
            logger.info(f"已创建新的向量数据库collection：{self.collection_name}和其HNSW index")
            try:
                await self.client.load_collection(self.collection_name, timeout=30)
                logger.info(f"向量数据库collection：{self.collection_name}已加载到内存")
            except Exception as e:
                logger.warning(f"加载向量数据库collection：{self.collection_name}失败，尝试继续：{str(e)}")
            # insert latest data
            if self.merged_data:
                await self._insert_all_data(self.merged_data)
        else:
            await self._ensure_hnsw_index()
            logger.info(f"向量数据库collection：{self.collection_name}已存在，使用已有的HNSW index")
            # load collection before query
            try:
                await self.client.load_collection(self.collection_name, timeout=30)
                logger.info(f"向量数据库collection：{self.collection_name}已加载到内存")
            except Exception as e:
                logger.warning(f"向量数据库collection：{self.collection_name}失败，尝试继续：{str(e)}")
            # update with latest data
            if self.merged_data:
                await self._incremental_sync_data(self.merged_data)

        # Check duplicates
        # await self.cleanup_duplicate_phrases()

        elapsed = time.time() - start_time
        logger.info(f"向量数据库collection: {self.collection_name}处理完成，耗时：{elapsed:.3f}秒")

    async def _create_collection(self):
        """Create the Milvus collection schema."""
        await self.client.create_collection(
            collection_name=self.collection_name,
            dimension = self.dimension,
            metric_type="COSINE",
            auto_id=False,  # We manage IDs by ourselves
            primary_field="id",
            extra_fields=[
                {"name": "id", "data_type": "INT64", "is_primary": True},
                {"name": "intention_id", "data_type": "VARCHAR", "max_length": 512},
                {"name": "intention_name", "data_type": "VARCHAR", "max_length": 512},
                {"name": "phrase", "data_type": "VARCHAR", "max_length": 4096},
            ]
        )
        logger.info(f"已创建向量数据库collection：{self.collection_name}")

    async def _create_hnsw_index(self):
        """Create HNSW index - called only once when collection is created."""
        try:
            # First, drop any existing indexes on the vector field
            existing_indexes = await self.client.list_indexes(self.collection_name)

            if existing_indexes:
                try:
                    await self.client.release_collection(self.collection_name)
                except Exception as e:
                    logger.warning(f"向量数据库collection：{self.collection_name}释放内存时发生警告：{str(e)}")

            for index_name in existing_indexes:
                try:
                    await self.client.drop_index(self.collection_name, index_name)
                    logger.info(f"向量数据库collection：{self.collection_name}已删除现有index：{index_name}")
                except Exception as e:
                    logger.warning(f"向量数据库collection：{self.collection_name}删除index {index_name}时发生警告：{str(e)}")

            # Create HNSW index
            index_params = IndexParams()
            index_params.add_index(
                field_name="vector",
                index_type="HNSW",
                metric_type="COSINE",
                params={"M": 16, "efConstruction": 200}
            )
            await self.client.create_index(
                collection_name=self.collection_name,
                index_params=index_params
            )
            logger.info(f"已创建向量数据库collection：{self.collection_name}的HNSW index")
        except MilvusException as e:
            logger.error(
                f"创建向量数据库collection：{self.collection_name} HNSW index时发生错误：{str(e)}"
            )
            raise RuntimeError(str(e))

    async def _ensure_hnsw_index(self):
        """确保HNSW索引存在，不存在则创建"""
        try:
            await self.client.release_collection(self.collection_name)
            existing_indexes = await self.client.list_indexes(self.collection_name)

            if not existing_indexes:
                logger.info(f"向量数据库collection：{self.collection_name}不存在索引，创建HNSW索引")
                await self._create_hnsw_index()
                return

            hnsw_exists = False
            for index_name in existing_indexes:
                try:
                    index_info = await self.client.describe_index(self.collection_name, index_name)
                    if (index_info.get('index_type') == 'HNSW' and index_info.get('metric_type') == 'COSINE'):
                        hnsw_exists = True
                        logger.info(f"向量数据库collection：{self.collection_name} HNSW index已存在，索引名称为{index_name}")
                        break
                except Exception as e:
                    logger.warning(f"向量数据库collection：{self.collection_name}检查索引{index_name}时发生警告：{str(e)}")

            if not hnsw_exists:
                logger.info(f"向量数据库collection：{self.collection_name}现有索引不是HNSW类型，替换为HNSW")
                await self._create_hnsw_index()

        except Exception as e:
            logger.error(f"向量数据库collection：{self.collection_name}检查HNSW索引时发生错误：{str(e)}")
            raise RuntimeError(str(e))

    async def _get_existing_phrase_ids_with_retry(self, max_retries: int = 3) -> set[int]:
        """带重试机制的获取现有ID"""
        for attempt in range(max_retries):
            try:
                return await self._get_existing_phrase_ids()
            except Exception as e:
                logger.warning(f"向量数据库collection：{self.collection_name}获取现有ID失败 (尝试 {attempt + 1}/{max_retries})：{e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt)  # 指数退避
                else:
                    logger.error(f"向量数据库collection：{self.collection_name}获取现有ID最终失败：{e}")
                    raise

    async def _get_existing_phrase_ids(self) -> set[int]:
        """Fetch all existing phrase_id values from Milvus (with pagination)."""
        existing_ids = set()
        try:
            offset = 0
            while True:
                results = await self.client.query(
                    collection_name=self.collection_name,
                    filter="",
                    output_fields=["id"],
                    limit=self.limit,
                    offset=offset
                )
                if not results:
                    break
                for r in results:
                    pid = r.get("id")
                    if pid is not None and pid != -1:  # exclude metadata sentinel
                        existing_ids.add(int(pid))
                if len(results) < self.limit:
                    break
                offset += self.limit
            return existing_ids
        except Exception as e:
            e_m = f"无法获取现有向量数据库collection：{self.collection_name} phrase_id列表：{e}"
            logger.error(e_m)
            raise RuntimeError(e_m)

    async def _prepare_target_data(
        self, merged_data: list[dict]
    ) -> tuple[set[int], dict[int, dict]]:
        """Prepare target data: compute IDs and build mapping."""
        target_phrase_ids = set()
        phrase_id_to_data = {}

        for item in merged_data:
            intention_id = item.get("intention_id")
            intention_name = item.get("intention_name")
            for phrase in item.get("semantic", []):
                clean_phrase = phrase.strip()
                if not clean_phrase:
                    continue

                phrase_id = self._generate_phrase_id(intention_id, clean_phrase)
                target_phrase_ids.add(phrase_id)

                phrase_id_to_data[phrase_id] = {
                    "intention_id": intention_id,
                    "intention_name": intention_name,
                    "phrase": clean_phrase,
                }

        logger.info(f"向量数据库collection：{self.collection_name}目标数据包含{len(target_phrase_ids)}条短语")
        return target_phrase_ids, phrase_id_to_data

    async def _incremental_sync_data(self, merged_data: list[dict]):
        """Incrementally sync data: insert new, delete obsolete."""
        try:
            logger.info(f"向量数据库collection：{self.collection_name}开始增量同步数据...")
            target_phrase_ids, phrase_id_to_data = await self._prepare_target_data(merged_data)
            existing_phrase_ids = await self._get_existing_phrase_ids_with_retry()
            logger.info(f"向量数据库collection：{self.collection_name}现有数据包含{len(existing_phrase_ids)}条短语")

            to_delete = existing_phrase_ids - target_phrase_ids
            to_insert = target_phrase_ids - existing_phrase_ids

            if to_delete:
                logger.info(f"向量数据库collection：{self.collection_name}删除{len(to_delete)}条过期问法短语")
                await self._batch_delete_phrases(list(to_delete))

            if to_insert:
                logger.info(f"向量数据库collection：{self.collection_name}插入{len(to_insert)}条新问法短语")
                await self._batch_insert_phrases(to_insert, phrase_id_to_data)
            else:
                logger.info(f"向量数据库collection：{self.collection_name}问法短语已同步，无需更新")

            self._log_sync_stats(len(existing_phrase_ids), len(to_delete), len(to_insert), len(target_phrase_ids))

        except Exception as e:
            logger.error(f"向量数据库collection：{self.collection_name}更新失败：{str(e)}")
            raise

    async def _batch_delete_phrases(self, phrase_ids: list[int], batch_size: int = 1000):
        """Batch delete phrases (fallback to chunked deletion on failure)."""
        if not phrase_ids:
            return
        try:
            if len(phrase_ids)<=batch_size: # Try in one go for small amount deletion
                await self.client.delete(collection_name=self.collection_name, ids=phrase_ids)
                logger.info(f"向量数据库collection：{self.collection_name}一次性删除{len(phrase_ids)}条短语")
            else: # Delete in batches for large amount
                for i in range(0, len(phrase_ids), batch_size):
                    batch = phrase_ids[i:i + batch_size]
                    await self.client.delete(collection_name=self.collection_name, ids=batch)
                    logger.info(f"向量数据库collection：{self.collection_name}正在分批删除，已删除批次 {i // batch_size + 1}: {len(batch)} 条")
                    await asyncio.sleep(0.01)  # Delay a bit to reduce server pressure
                logger.info(f"向量数据库collection：{self.collection_name}分批删除完成，共{len(phrase_ids)}条")
        except Exception as e:
            logger.warning(f"向量数据库collection：{self.collection_name}删除失败，尝试降级方案：{str(e)}")
            await self._delete_with_filter_fallback(phrase_ids)

    async def _delete_with_filter_fallback(self, phrase_ids: list[int]):
        try:
            id_str = ", ".join(str(pid) for pid in phrase_ids)
            filter_expr = f"id in [{id_str}]"
            await self.client.delete(
                collection_name=self.collection_name,
                filter=filter_expr
            )
        except Exception as e:
            logger.error(f"向量数据库collection：{self.collection_name} filter删除也失败，尝试逐个删除：{str(e)}")
            # Delete one by one
            success_count = 0
            for pid in phrase_ids:
                try:
                    await self.client.delete(
                        collection_name=self.collection_name,
                        filter=f"id == {pid}"
                    )
                    success_count += 1
                except Exception:
                    logger.warning(f"向量数据库collection：{self.collection_name}无法删除phrase_id {pid}")
            logger.info(f"向量数据库collection：{self.collection_name}逐个删除完成：{success_count}/{len(phrase_ids)}成功")

    async def _batch_insert_phrases(self, phrase_ids_to_insert: set[int], phrase_id_to_data: dict[int, dict]):
        """Batch insert phrases with cached embedding."""
        if not phrase_ids_to_insert:
            return

        MILVUS_BATCH_SIZE = 100
        phrase_ids_list = list(phrase_ids_to_insert)

        for i in range(0, len(phrase_ids_list), MILVUS_BATCH_SIZE):
            batch_ids = phrase_ids_list[i:i + MILVUS_BATCH_SIZE]
            batch_data = await self._prepare_insert_batch(batch_ids, phrase_id_to_data)
            if batch_data:
                try:
                    await self.client.insert(collection_name=self.collection_name, data=batch_data)
                    logger.debug(f"向量数据库collection：{self.collection_name}已插入批次 {i // MILVUS_BATCH_SIZE + 1}: {len(batch_data)} 条")
                except Exception as e:
                    e_m = f"向量数据库collection：{self.collection_name}批次插入失败：{str(e)}"
                    logger.error(e_m)
                    raise RuntimeError(e_m)
            await asyncio.sleep(0)  # yield control

    async def _prepare_insert_batch(
        self, batch_ids: list[int], phrase_id_to_data: dict[int, dict]
    ) -> list[dict]:
        """Prepare a batch of data with embeddings using batched API calls and cache."""
        batch_data = []
        uncached_phrases = []  # List of tuples: (phrase_id, phrase_text, data_dict)

        # 1. Separate cached and uncached phrases
        async with self._cache_lock:
            for phrase_id in batch_ids:
                data = phrase_id_to_data.get(phrase_id)
                if not data:
                    continue

                phrase_text = data["phrase"]
                intention_id = data["intention_id"]
                cache_key = f"{intention_id}:{phrase_text}"

                self._stats["total_phrases_processed"] += 1

                if cache_key in self.embedding_cache:
                    embedding = self.embedding_cache[cache_key]
                    self._stats["embeddings_cached"] += 1
                    batch_data.append(
                        {
                            "id": phrase_id,
                            "vector": embedding,
                            "intention_id": intention_id,
                            "intention_name": data["intention_name"],
                            "phrase": phrase_text,
                        }
                    )
                else:
                    uncached_phrases.append((phrase_id, phrase_text, data))

        # 2. Fetch embeddings for uncached phrases in bulk
        if uncached_phrases:
            EMBED_API_BATCH_SIZE = 50

            uncached_texts = [item[1] for item in uncached_phrases]
            uncached_embeddings = []

            # Chunk the uncached texts to avoid sending massive payloads in a single HTTP request
            for j in range(0, len(uncached_texts), EMBED_API_BATCH_SIZE):
                chunk_texts = uncached_texts[j : j + EMBED_API_BATCH_SIZE]
                try:
                    # embed_documents is sync (uses requests), so we run it in a thread
                    chunk_embs = await asyncio.to_thread(embed_documents, chunk_texts)
                    uncached_embeddings.extend(chunk_embs)
                except Exception as e:
                    logger.error(f"批量获取嵌入向量失败: {e}")
                    # If the API fails, append None for these phrases so they are safely skipped
                    uncached_embeddings.extend([None] * len(chunk_texts))

            # 3. Map embeddings back to phrases, validate, update cache, and add to batch_data
            async with self._cache_lock:
                # Simple cache clearance if we exceed max size
                if (
                    len(self.embedding_cache) + len(uncached_phrases)
                    > self._max_cache_size
                ):
                    keys_to_remove = list(self.embedding_cache.keys())[
                        : len(uncached_phrases) + (self._max_cache_size // 10)
                    ]
                    for key in keys_to_remove:
                        del self.embedding_cache[key]

                for (phrase_id, phrase_text, data), embedding in zip(
                    uncached_phrases, uncached_embeddings
                ):
                    if embedding is None:
                        continue

                    if hasattr(embedding, "tolist"):
                        embedding = embedding.tolist()

                    if len(embedding) != self.dimension:
                        logger.error(
                            f"向量数据库collection：{self.collection_name}向量维度错误: {len(embedding)}，跳过：{phrase_text[:50]}..."
                        )
                        continue

                    cache_key = f"{data['intention_id']}:{phrase_text}"
                    self.embedding_cache[cache_key] = embedding
                    self._stats["embeddings_generated"] += 1

                    batch_data.append(
                        {
                            "id": phrase_id,
                            "vector": embedding,
                            "intention_id": data["intention_id"],
                            "intention_name": data["intention_name"],
                            "phrase": phrase_text,
                        }
                    )

        return batch_data

    async def _insert_all_data(self, merged_data: list[dict]):
        """Insert all data on first-time collection creation."""
        logger.info(f"向量数据库collection：{self.collection_name}开始初始数据插入...")
        phrase_id_to_data = {}
        all_items_count = 0

        for item in merged_data:
            intention_id = item.get("intention_id")
            intention_name = item.get("intention_name")
            for phrase in item.get("semantic", []):
                clean_phrase = phrase.strip()
                if clean_phrase:
                    phrase_id = self._generate_phrase_id(intention_id, clean_phrase)
                    phrase_id_to_data[phrase_id] = {
                        "intention_id": intention_id,
                        "intention_name": intention_name,
                        "phrase": clean_phrase,
                    }
                    all_items_count += 1

        MILVUS_BATCH_SIZE = 200
        phrase_ids_list = list(phrase_id_to_data.keys())
        for i in range(0, len(phrase_ids_list), MILVUS_BATCH_SIZE):
            batch_ids = phrase_ids_list[i:i + MILVUS_BATCH_SIZE]
            insert_batch = await self._prepare_insert_batch(batch_ids, phrase_id_to_data)
            if insert_batch:
                await self.client.insert(collection_name=self.collection_name, data=insert_batch)
                logger.debug(f"向量数据库collection：{self.collection_name}初始插入批次{i // MILVUS_BATCH_SIZE + 1}: {len(insert_batch)}条")
            await asyncio.sleep(0)

        logger.info(f"向量数据库collection：{self.collection_name}初始数据插入完成，共 {all_items_count}条短语")

    def _log_sync_stats(self, existing_count: int, deleted_count: int, inserted_count: int, final_count: int):
        """Log sync statistics."""
        # Calculate cache hit rate
        total_embeddings = self._stats["embeddings_generated"] + self._stats["embeddings_cached"]
        cache_hit_rate = 0
        if total_embeddings > 0:
            cache_hit_rate = self._stats["embeddings_cached"] / total_embeddings * 100

        logger.info(
            f"向量数据库collection：{self.collection_name}更新数据同步统计:\n"
            f"  原有记录: {existing_count}\n"
            f"  删除记录: {deleted_count}\n"
            f"  新增记录: {inserted_count}\n"
            f"  最终记录: {final_count}\n"
            f"  变化率: {(deleted_count + inserted_count) / max(existing_count, 1) * 100:.1f}%\n"
            f"  嵌入性能统计:\n"
            f"    总处理短语: {self._stats['total_phrases_processed']}\n"
            f"    生成嵌入: {self._stats['embeddings_generated']}\n"
            f"    缓存命中: {self._stats['embeddings_cached']}\n"
            f"    缓存命中率: {cache_hit_rate:.1f}%"
        )

    async def get_index_info(self):
        """Get information about current index."""
        try:
            existing_indexes = await self.client.list_indexes(self.collection_name)
            return [
                {
                    'name': index_name,
                    'info': await self.client.describe_index(self.collection_name, index_name)
                }
                for index_name in existing_indexes
            ]
        except Exception as e:
            logger.error(f"获取index信息时发生错误：{e}")
            return []

    async def cleanup_duplicate_phrases(self):
        """Clean duplicated phrases"""
        try:
            await self.client.load_collection(self.collection_name, timeout=30)
            offset = 0
            all_data = []
            while True:
                results = await self.client.query(
                    collection_name=self.collection_name,
                    filter="",
                    output_fields=["id", "phrase", "intention_id"],
                    limit=self.limit,
                    offset=offset
                )
                if not results:
                    break
                all_data += results
                if len(results) < self.limit:
                    break
                offset += self.limit

            if not all_data:
                logger.info(f"向量数据库collection：{self.collection_name}为空，无需检查重复记录")
                return

            # find duplicates
            seen = {}
            duplicates = []

            for item in all_data:
                key = f"{item['intention_id']}:{item['phrase']}"
                if key in seen:
                    duplicates.append(item['id'])
                else:
                    seen[key] = item['id']

            if duplicates:
                logger.info(f"向量数据库collection：{self.collection_name}发现{len(duplicates)}条重复记录，正在清理...")
                await self.client.delete(
                    collection_name=self.collection_name,
                    ids=duplicates
                )
                logger.info(f"向量数据库collection：{self.collection_name}已清理{len(duplicates)}条重复记录")
            else:
                logger.info(f"向量数据库collection：{self.collection_name}未发现重复记录")

        except Exception as e:
            logger.error(f"向量数据库collection：{self.collection_name}清理重复数据失败: {str(e)}")

async def initialize_milvus_async(
        vector_db_url: str,
        collection_name: str,
        intentions: list|None = None,
        knowledge: list|None = None
) -> AsyncMilvusClient:
    milvus_launcher = LaunchMilvusAsync(vector_db_url, collection_name, intentions, knowledge)
    await milvus_launcher.ensure_collection_ready()  # ONE-TIME SETUP
    return milvus_launcher.client

# test
if __name__ == "__main__":
    async def test_phrase_id():
        # Test deterministic ID generation (no client needed)
        launcher = LaunchMilvusAsync("http://127.0.0.1:19530", "test")
        id1 = launcher._generate_phrase_id("001", "good")
        id2 = launcher._generate_phrase_id("002", "good")
        id3 = launcher._generate_phrase_id("001", "bad")
        id4 = launcher._generate_phrase_id("002", "bad")
        id5 = launcher._generate_phrase_id("001", "good")

        print(f"id1: {id1}")
        print(f"id2: {id2}")
        print(f"id3: {id3}")
        print(f"id4: {id4}")
        print(f"id5: {id5}")

        # Now test full async flow (optional)
        await launcher.ensure_collection_ready()

    asyncio.run(test_phrase_id())