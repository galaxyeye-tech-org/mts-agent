# -*- coding: utf-8 -*-
import typing
from typing import Optional
from pymilvus import DataType

from hagworm.extend.error import catch_error
from pymongo import UpdateOne, InsertOne, DeleteOne, HASHED

from model.utils import DataUtils
from service import ServiceBase, StorageQueueBuffer

from setting import Config


class InsertQueueBuffer(StorageQueueBuffer):

    async def _handle_mongo(self, data_list: typing.List[dict]):

        data = []

        for _data in data_list:
            data.append(
                InsertOne(_data)
            )

        _collection = self._data_source.get_mongo_collection(Config.MongoDBName, Config.DataStorageMongoDialogueStrategy)

        await _collection.bulk_write(data, ordered=False)

    async def _handle_milvus(self, data_list: typing.List[dict]):

        data = []

        for _data in data_list:
            data.append(
                {
                    r'id': _data[r'_id'],
                    r'robot_id': _data[r'robot_id'],
                    r'uid': _data[r'uid'],
                    r'attention': _data[r'attention'],
                    r'embeddings': _data[r'embeddings'],
                }
            )

        await self._data_source.milvus_client.insert(
            Config.MilvusCollectionDialogueStrategyName,
            data
        )


class UpdateQueueBuffer(StorageQueueBuffer):

    async def _handle_mongo(self, data_list: typing.List[dict]):

        data = []

        for _data in data_list:
            data.append(
                UpdateOne(**_data)
            )

        _collection = self._data_source.get_mongo_collection(Config.MongoDBName, Config.DataStorageMongoDialogueStrategy)

        await _collection.bulk_write(data, ordered=False)


class DeleteQueueBuffer(StorageQueueBuffer):

    async def _handle_mongo(self, data_list: typing.List[dict]):

        data = []

        for _data in data_list:
            data.append(
                DeleteOne(**_data)
            )

        _collection = self._data_source.get_mongo_collection(Config.MongoDBName, Config.DataStorageMongoDialogueStrategy)

        await _collection.bulk_write(data, ordered=False)

    async def _handle_milvus(self, data_list: typing.List[dict]):

        pks = []

        for _data in data_list:
            pks.append(
                _data[r'filter'][r'_id']
            )

        await self._data_source.milvus_client.delete(
            Config.MilvusCollectionDialogueStrategyName,
            pks
        )


class StrategyService(ServiceBase):

    def __init__(self):

        super().__init__()

        self._insert_queue_buffer = InsertQueueBuffer(
            Config.DialogMongoQueueBufferMemoryMaxSize,
            Config.DialogMongoQueueBufferMemoryTimeout,
            Config.DialogMongoQueueBufferMemoryTaskLimit,
        )

        self._update_queue_buffer = UpdateQueueBuffer(
            Config.DialogMongoQueueBufferMemoryMaxSize,
            Config.DialogMongoQueueBufferMemoryTimeout,
            Config.DialogMongoQueueBufferMemoryTaskLimit,
        )

        self._delete_queue_buffer = DeleteQueueBuffer(
            Config.DialogMongoQueueBufferMemoryMaxSize,
            Config.DialogMongoQueueBufferMemoryTimeout,
            Config.DialogMongoQueueBufferMemoryTaskLimit,
        )

    async def initialize(self):

        self._check_milvus_dialogue_strategy_collection()

    async def release(self):

        pass

    def _check_milvus_dialogue_strategy_collection(self):

        with catch_error():

            milvus_client = self._data_source.milvus_client

            _collection_name = Config.MilvusCollectionDialogueStrategyName

            if not milvus_client.has_collection(_collection_name):

                _schema = milvus_client.create_schema()
                _schema.add_field(r'id', DataType.VARCHAR, is_primary=True, auto_id=False, max_length=50)
                _schema.add_field(r'robot_id', DataType.VARCHAR, max_length=50)
                _schema.add_field(r'uid', DataType.VARCHAR, max_length=50)
                _schema.add_field(r'attention', DataType.INT8)
                _schema.add_field(r'embeddings', DataType.FLOAT_VECTOR, dim=Config.Word2VecBgeDim)

                _index_params = {
                    r'field_name': r'embeddings',
                    r'index_type': r'IVF_FLAT',
                    r'metric_type': r'IP',
                    r'params': {r'nlist': 2048},
                }

                milvus_client.create_collection_with_schema(
                    _collection_name,
                    _schema,
                    _index_params,
                    consistency_level=r'Strong'
                )

                _collection = milvus_client.get_collection(_collection_name)
                _collection.create_index(r'robot_id', {r'index_type': r'Trie'})
                _collection.create_index(r'attention', {r'index_type': r'STL_SORT'})


            self.log.info(f'initialize milvus collection: {_collection_name}')

    async def rebuild_milvus_dialogue_strategy(self):

        result = False

        with catch_error():

            milvus_client = self._data_source.milvus_client

            if milvus_client.has_collection(Config.MilvusCollectionDialogueStrategyName):

                milvus_client.drop_collection(Config.MilvusCollectionDialogueStrategyName)

            self._check_milvus_dialogue_strategy_collection()

            await self._rebuild_milvus_dialogue_strategy_from_mongodb()

            result = True

        return result

    async def _rebuild_milvus_dialogue_strategy_from_mongodb(self):

        result = -1

        with catch_error():

            page_size = Config.EmbeddingServiceThreadWorker // 2

            mongo_collection = self.get_dialogue_strategy_mongo_collection()

            _total = await mongo_collection.count_documents({})
            cursor = mongo_collection.find({})
            _doc: dict

            for _ in range(self.math.ceil(_total / page_size)):

                entities = []

                for _doc in await cursor.to_list(length=page_size):

                    entities.append({
                        r'id': _doc[r'_id'],
                        r'robot_id': _doc[r'robot_id'],
                        r'uid': _doc[r'uid'],
                        r'attention': _doc[r'attention'],
                        r'embeddings': _doc[r'embeddings'],
                    })

                if any(entities):
                    await self._data_source.milvus_client.insert(Config.MilvusCollectionDialogueStrategyName, entities)

            result = _total

        return result

    async def add_dialogue_strategy(self, robot_id: str, uid: str, data: dict, attention: int) -> Optional[str]:

        result = None

        with catch_error():

            _mongo_collection = self.get_dialogue_strategy_mongo_collection()

            timestamp = self.timestamp(msec=True)

            embeddings = await self._data_source.get_vector(data[r'意图'])

            if not uid:
                uid = DataUtils.StrategyPublicUid

            _id = self.uuid1_urn()
            document = {
                r'_id': _id,
                r'robot_id': robot_id,
                r'uid': uid,
                r'data': data,
                r'attention': attention,
                r'gmt_create': timestamp,
                r'gmt_modify': timestamp,
            }

            self.log.info(f'add_dialogue_strategy {document=}')

            document[r'embeddings'] = embeddings

            await self._insert_queue_buffer.append(document)

            result = _id

        return result

    async def page_all_dialogue_strategy(self, robot_id: str, uids: list[str], include_public: bool, limit: int = 10):

        total = 0
        infos = []

        with catch_error():

            _collection = self.get_dialogue_strategy_mongo_collection()

            _where = {r'robot_id': robot_id}

            if uids:

                if include_public:
                    uids.append(DataUtils.StrategyPublicUid)

                uids = list(set(uids))
                _where[r'uid'] = {r'$in': uids}

            total = await _collection.count_documents(_where)

            if not total:
                self.Break(f'{robot_id=} {uids=} have not any dialogue strategy!')

            exclude_field = {r'embeddings': 0}

            _infos = await _collection.find(_where, exclude_field).sort([(r'gmt_create', 1)]).limit(limit).to_list(limit)

            infos = DataUtils.format_mongo_records(_infos)

        return total, infos

    async def del_dialogue_strategy(self, id_: str):

        result = False

        with catch_error():

            self.log.info(f'del_dialogue_strategy {id_=}')

            await self._delete_queue_buffer.append(
                {
                    r'filter': {
                        r'_id': id_
                    }
                }
            )

            result = True

        return result

    async def get_dialogue_strategies(self, ids: list[str]):

        result = None

        with catch_error():

            _collection = self.get_dialogue_strategy_mongo_collection()

            exclude_field = {r'embeddings': 0}

            _infos = await _collection.find({r'_id': {r'$in': ids}}, exclude_field).to_list(len(ids))

            if _infos:
                result = DataUtils.format_mongo_records(_infos)

        return result

    async def get_similar_dialogue_strategies(
            self, robot_id: str, uid: str, include_public: bool, content: str, radius: float = 0.8, limit: int = 10,
    ) -> dict[str, float]:

        result = {}

        with catch_error():

            _search_vec = await self._data_source.get_vector(content)
            _search_params = {
                r'metric_type': r'IP',
                r'params': {
                    r'nprobe': 10,  # 最近十个聚类
                    r'radius': radius,
                }
            }

            self.log.info(
                f'get_similar_dialogue_strategies {content=} ==> {len(_search_vec)=}; {robot_id=}, {uids=}, {limit=}'
            )

            _expr = f'robot_id == "{robot_id}"'

            uids = []

            if uid:
                uids.append(uid)
            if include_public:
                uids.append(DataUtils.StrategyPublicUid)
            if uids:
                _uids_str = r','.join(f"'{_uid}'" for _uid in uids)
                _expr += f' and uid in [{_uids_str}]'

            _res = await self._data_source.milvus_client.search(
                Config.MilvusCollectionDialogueStrategyName, [_search_vec],
                # r'embeddings',
                search_params=_search_params,
                filter_=_expr,
                limit=limit,
                output_fields=[r'id']
            )

            self.log.info(f'get similar dialogue strategies: {_res}')
            for item in _res[0]:
                result[item[r'id']] = item[r'distance']

        return result

    async def regenerate_dialogue_strategies(self):

        result = -1

        with catch_error():

            page_size = Config.EmbeddingServiceThreadWorker // 2

            mongo_collection = self.get_dialogue_strategy_mongo_collection()

            _total = await mongo_collection.count_documents({})
            cursor = mongo_collection.find({})
            _doc: dict

            for _ in range(self.math.ceil(_total / page_size)):

                for _doc in await cursor.to_list(length=page_size):
                    if not _doc.get(r'embeddings', None):
                        content = _doc[r'data'][r'意图']
                        embeddings = await self._data_source.get_vector(content)
                        _doc[r'embeddings'] = embeddings

                        self._update_queue_buffer.safe_append(
                            {
                                r'filter': {
                                    r'_id': _doc[r'_id'],
                                },
                                r'update': {
                                    r'$set': {
                                        r'embeddings': embeddings,
                                    }
                                }
                            }
                        )

            result = _total

        return result

    async def regenerate_mongo_dialogue_strategy_collection(self):

        result = -1

        with catch_error():

            mongo_collection = self.get_dialogue_strategy_mongo_collection()
            await mongo_collection.create_index([(r'uid', HASHED)])

            page_size = 2000

            _total = await mongo_collection.count_documents({})
            cursor = mongo_collection.find({}, {'_id': 1})
            _doc: dict

            for _ in range(self.math.ceil(_total / page_size)):

                for _doc in await cursor.to_list(length=page_size):

                    self._update_queue_buffer.safe_append(
                        {
                            r'filter': {
                                r'_id': _doc[r'_id'],
                            },
                            r'update': {
                                r'$set': {
                                    r'uid': 'xtest006',
                                }
                            }
                        }
                    )

                result = _total

            return result
