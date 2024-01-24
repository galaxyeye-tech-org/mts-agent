# -*- coding: utf-8 -*-

__author__ = r'wsb310@gmail.com'

import typing

from pymongo import HASHED, DESCENDING, InsertOne, UpdateOne, DeleteOne
from pymilvus import DataType
from torch.cuda import OutOfMemoryError

from model.fields import QAPair

from hagworm.extend.error import catch_error
from hagworm.extend.asyncio.future import ThreadWorker

from service import StorageQueueBuffer, ServiceBase

from setting import Config


THREAD_WORKER = ThreadWorker(Config.QAServiceThreadWorker)


class InsertQueueBuffer(StorageQueueBuffer):

    async def _handle_mongo(self, data_list: typing.List[dict]):

        data = []

        for _data in data_list:
            data.append(
                InsertOne(_data)
            )

        _collection = self._data_source.get_mongo_collection(Config.MongoDBName, Config.DataStorageMongoQuestion)

        await _collection.bulk_write(data, ordered=False)

    async def _handle_milvus(self, data_list: typing.List[dict]):

        data = []

        for _data in data_list:
            data.append(
                {
                    r'id': _data[r'_id'],
                    r'uid': _data[r'uid'],
                    r'type': _data[r'type'],
                    r'attention': _data[r'attention'],
                    r'confidence': _data[r'confidence'],
                    r'embeddings': _data[r'embeddings'],
                }
            )

        await self._data_source.milvus_client.insert(
            Config.MilvusCollectionQuestionName,
            data
        )


class UpdateQueueBuffer(StorageQueueBuffer):

    async def _handle_mongo(self, data_list: typing.List[dict]):

        data = []

        for _data in data_list:
            data.append(
                UpdateOne(**_data)
            )

        _collection = self._data_source.get_mongo_collection(Config.MongoDBName, Config.DataStorageMongoQuestion)

        await _collection.bulk_write(data, ordered=False)


class DeleteQueueBuffer(StorageQueueBuffer):

    async def _handle_mongo(self, data_list: typing.List[dict]):

        data = []

        for _data in data_list:
            data.append(
                DeleteOne(**_data)
            )

        _collection = self._data_source.get_mongo_collection(Config.MongoDBName, Config.DataStorageMongoQuestion)

        await _collection.bulk_write(data, ordered=False)

    async def _handle_milvus(self, data_list: typing.List[dict]):

        pks = []

        for _data in data_list:
            pks.append(
                _data[r'filter'][r'_id']
            )

        await self._data_source.milvus_client.delete(
            Config.MilvusCollectionQuestionName,
            pks
        )


class QAService(ServiceBase):

    def __init__(self):
        #
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

        await self._check_question_mongo_collection()

        await self._check_neo4j_question_graph()

        await self._check_milvus_question_collection()

        # self._qa_tree_node_helper = QATreeNodeHelper(self.log)

    async def release(self):

        pass

    async def _check_question_mongo_collection(self):

        with catch_error():

            mongo_db = self._data_source.get_mongo_database(Config.MongoDBName)

            if not (names := await mongo_db.list_collection_names()) or Config.DataStorageMongoQuestion not in set(names):

                _collection = mongo_db.get_collection(Config.DataStorageMongoQuestion)

                await _collection.create_index([(r'task_id', HASHED)])
                await _collection.create_index([(r'type', HASHED)])
                await _collection.create_index([(r'status', HASHED)])
                await _collection.create_index([(r'parent_id', HASHED)])
                await _collection.create_index([(r'attention', DESCENDING)])
                await _collection.create_index([(r'confidence', DESCENDING)])
                await _collection.create_index([(r'gmt_create', DESCENDING)])
                await _collection.create_index([(r'gmt_modify', DESCENDING)])

                self.log.info(r'create question mongo collection and index')

    async def _check_neo4j_question_graph(self):

        with catch_error():

            await self._data_source.neo4j_client_for_qa.execute_query(
                r'CREATE CONSTRAINT uni_qa_container_name IF NOT EXISTS FOR (n:qa_container) REQUIRE (n.name) IS UNIQUE'
            )

            await self._data_source.neo4j_client_for_qa.execute_query(
                r'CREATE CONSTRAINT uni_qa_content_name IF NOT EXISTS FOR (n:qa_content) REQUIRE (n.name) IS UNIQUE'
            )

            await self._data_source.neo4j_client_for_qa.execute_query(
                r'CREATE INDEX idx_qa_content_uid IF NOT EXISTS FOR (n:qa_content) ON (n.uid)'
            )

            await self._data_source.neo4j_client_for_qa.execute_query(
                r'MERGE (r:qa_container {name: "qa_root"})'
            )

            self.log.info(f'initialize neo4j question root node')

    async def _add_neo4j_node(
            self,
            id_: str, uid: str, task_id: str, content: str, type_: str,
            parent_id: str, attention: int, confidence: int, status: int
    ):

        with catch_error():

            if parent_id is None or parent_id == r'None':

                await self._data_source.neo4j_client_for_qa.execute_query(
                    r'''
                    MATCH (r:qa_container {name: "qa_root"})
                    MERGE (u:qa_container {name: $uid})
                    MERGE (c:qa_content {name: $name, uid: $uid, task_id: $task_id, content: $content, type: $type, parent_id: $parent_id, attention: $attention, confidence: $confidence, status: $status})
                    MERGE (r) -[:qa_link]-> (u)
                    MERGE (u) -[:qa_link]-> (c)
                    ''',
                    parameters_={
                        r'name': id_,
                        r'uid': uid,
                        r'task_id': task_id,
                        r'content': content,
                        r'type': type_,
                        r'parent_id': parent_id,
                        r'attention': attention,
                        r'confidence': confidence,
                        r'status': status,
                    }
                )

            else:

                await self._data_source.neo4j_client_for_qa.execute_query(
                    r'''
                    MATCH (c1:qa_content) WHERE c1.name = $parent_id
                    MERGE (c2:qa_content {name: $name, uid: $uid, task_id: $task_id, content: $content, type: $type, parent_id: $parent_id, attention: $attention, confidence: $confidence, status: $status})
                    MERGE (c1) -[:qa_link]-> (c2)
                    ''',
                    parameters_={
                        r'name': id_,
                        r'uid': uid,
                        r'task_id': task_id,
                        r'content': content,
                        r'type': type_,
                        r'parent_id': parent_id,
                        r'attention': attention,
                        r'confidence': confidence,
                        r'status': status,
                    },
                )

    async def _update_neo4j_node(self, id_: str, status: int):

        with catch_error():

            _, summary, _ = await self._data_source.neo4j_client_for_qa.execute_query(
                r'''
                MATCH (qc:qa_content {name: $name})
                SET qc.status = $status
                ''',
                parameters_={
                    r'name': id_,
                    r'status': status,
                }
            )

            self.log.info(f"_update_neo4j_node {id_=} {status=} Query counters: {summary.counters}.")

    async def _del_neo4j_node(self, id_: str):

        with catch_error():

            _, summary, _ = await self._data_source.neo4j_client_for_qa.execute_query(
                r'''
                MATCH (qc:qa_content {name: $name})
                DETACH DELETE qc
                ''',
                parameters_={
                    r'name': id_,
                }
            )

            self.log.info(f"_del_neo4j_node {id_=} Query counters: {summary.counters}.")

    async def _get_neo4j_children_nodes(self, uid: str, node_ids: list[str]):

        with catch_error():
            records, summary, keys = await self._data_source.neo4j_client_for_qa.execute_query(
                r'''
                MATCH (root:qa_content where root.uid = $uid and root.name in $node_names)-[:qa_link]->(node:qa_content)
                return 
                root.name as node_id, 
                collect(
                    {
                        id: node.name,
                        task_id: node.task_id,
                        content: node.content,
                        type: node.type,
                        status: node.status,
                        parent_id: node.parent_id,
                        attention: node.attention,
                        confidence: node.confidence
                    }
                ) as children 
                ''',
                parameters_={
                    r'uid': uid,
                    r'node_names': node_ids,
                }
            )

            if len(records) > 0:
                records = [record.data() for record in records]

            return records, summary, keys

    async def _get_neo4j_qa_nodes_content(self, uid: str, question_ids: list[str], answer_ids: list[str]):

        with catch_error():
            records, summary, keys = await self._data_source.neo4j_client_for_qa.execute_query(
                r'''
                match (root:qa_content)-[:qa_link]->(node:qa_content)
                where root.uid = $uid and root.name in $question_ids
                return root.content as content, collect(
                    {
                        id: node.name,
                        task_id: node.task_id,
                        content: node.content,
                        type: node.type,
                        status: node.status,
                        parent_id: node.parent_id,
                        attention: node.attention,
                        confidence: node.confidence
                    }
                ) as children
                UNION
                match (root:qa_content )-[:qa_link]->(node:qa_content)
                where node.uid = $uid and node.name in $answer_ids and NOT (root.name IN $question_ids)
                return root.content as content, collect(
                    {
                        id: node.name,
                        task_id: node.task_id,
                        content: node.content,
                        type: node.type,
                        status: node.status,
                        parent_id: node.parent_id,
                        attention: node.attention,
                        confidence: node.confidence
                    }
                ) as children
                ''',
                parameters_={
                    r'uid': uid,
                    r'question_ids': question_ids,
                    r'answer_ids': answer_ids,
                }
            )

            if len(records) > 0:
                records = [record.data() for record in records]

            return records, summary, keys

    async def _get_neo4j_nodes_recursively(self, uid: str, node_ids: list[str]):

        with catch_error():
            records, summary, keys = await self._data_source.neo4j_client_for_qa.execute_query(
                r'''
                MATCH (root:qa_content {uid: $uid})-[links:qa_link*0..]->(node:qa_content)
                where root.name in $node_ids
                return 
                root.name as id,
                collect({
                    id: node.name,
                    task_id: node.task_id,
                    content: node.content,
                    type: node.type,
                    status: node.status,
                    parent_id: node.parent_id,
                    attention: node.attention,
                    confidence: node.confidence
                }) as children
                ''',
                parameters_={
                    r'uid': uid,
                    r'node_ids': node_ids,
                }
            )

            if len(records) > 0:
                records = [record.data() for record in records]

            return records, summary, keys

    @THREAD_WORKER
    def _check_milvus_question_collection(self):

        with catch_error():

            milvus_client = self._data_source.milvus_client

            _collection_name = Config.MilvusCollectionQuestionName

            if not milvus_client.has_collection(_collection_name):

                _schema = milvus_client.create_schema()
                _schema.add_field(r'id', DataType.VARCHAR, is_primary=True, auto_id=False, max_length=50)
                _schema.add_field(r'uid', DataType.VARCHAR, max_length=50)
                _schema.add_field(r'type', DataType.VARCHAR, max_length=50)
                _schema.add_field(r'attention', DataType.INT8)
                _schema.add_field(r'confidence', DataType.INT8)
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
                _collection.create_index(r'uid', {r'index_type': r'Trie'}, index_name=r'idx_uid')
                _collection.create_index(r'type', {r'index_type': r'Trie'}, index_name=r'idx_type')
                _collection.create_index(r'attention', {r'index_type': r'STL_SORT'}, index_name=r'idx_attention')
                _collection.create_index(r'confidence', {r'index_type': r'STL_SORT'}, index_name=r'idx_confidence')

            self.log.info(f'initialize question milvus collection: {_collection_name}')

    async def get_answer_node_from_qa(self, uid: str, question: str, radius: float = 0.7) -> QAPair:

        result = {}

        with catch_error():

            vector = await self._data_source.get_vector(question)

            milvus_resp = await self._data_source.milvus_client.search(
                Config.MilvusCollectionQuestionName, [vector],
                search_params={
                    r'params': {
                        r'nprobe': 10,
                        r'radius': radius,
                    },
                },
                filter_=f'uid == "{uid}"',
                output_fields=[r'id', r'type']
            )

            if len(qa_nodes := milvus_resp[0]) == 0:
                self.Break(f'{uid=}  {question=} have no any matched question and answer!')

            collection = self.get_question_mongo_collection()

            _node_ids = [_item[r'id'] for _item in qa_nodes]

            mongo_resp = await collection.find(
                {r'_id': {r'$in': _node_ids}},
                {r'_id': 1, 'content': 1}
            ).to_list(len(_node_ids))

            mongo_dict = {_val[r'_id']: _val for _val in mongo_resp}

            question_nodes, answer_nodes = [], []
            question_ids, answer_ids = [], []
            for node in qa_nodes:
                if node[r'entity'][r'type'] == r'Q':
                    question_nodes.append(node)
                    question_ids.append(node[r'id'])
                if node[r'entity'][r'type'].startswith(r'A'):
                    answer_nodes.append(node)
                    answer_ids.append(node[r'id'])

            neo4j_resp, _, _ = await self._get_neo4j_qa_nodes_content(uid, question_ids, answer_ids)

            result = {item[r'content']: item[r'children'] for item in neo4j_resp}

        return result

    async def batch_get_answer_node_from_qa(
            self, uid: str, questions: list[str], radius: float = 0.7, vectors: dict[str, [list[float]]] = None
    ) -> dict[str, QAPair]:

        result = {question: {} for question in questions}

        with catch_error():

            if not vectors:
                vector_list = [await self._data_source.get_vector(question) for question in questions]

            else:
                vector_list = [vectors[question] for question in questions]

            milvus_resp = await self._data_source.milvus_client.search(
                Config.MilvusCollectionQuestionName, vector_list,
                search_params={
                    r'params': {
                        r'nprobe': 10,
                        r'radius': radius,
                    },
                },
                filter_=f'uid == "{uid}"',
                output_fields=[r'id', r'type']
            )

            for i in range(len(questions)):

                if len(qa_nodes := milvus_resp[i]) == 0:
                    continue

                question_ids, answer_ids = [], []
                for node in qa_nodes:
                    if node[r'entity'][r'type'] == r'Q':
                        question_ids.append(node[r'id'])
                    if node[r'entity'][r'type'].startswith(r'A'):
                        answer_ids.append(node[r'id'])

                neo4j_resp, _, _ = await self._get_neo4j_qa_nodes_content(uid, question_ids, answer_ids)

                result[questions[i]] = {item[r'content']: item[r'children'] for item in neo4j_resp}

            self.log.info(f'{uid=} {questions=} batch get question_answers: {result}')

        return result

    async def insert_qa_node_pair(self, uid: str, question: str, answer: str, attention: int):

        res = {}

        task_body = {
            r'task_id': "None",
            r'content': question,
            r'type': r'Q',
            r'confidence': self._get_default_qa_confidence(r'Q'),
            r'parent_id': "None",
            r'attention': attention,
            r'status': 0
        }

        question_nodes = await self.insert_node(uid, [task_body])

        if len(question_nodes) > 0:

            task_body.update({
                "content": answer,
                "type": "A_问答求解",
                r'confidence': self._get_default_qa_confidence(r'A_问答求解'),
                "parent_id": question_nodes[0],
            })

            answer_nodes = await self.insert_node(uid, [task_body])

            if len(answer_nodes) > 0:

                task_body[r'id'] = answer_nodes[0]

                res[question] = [task_body]

        return res

    async def batch_insert_qa_node_pair(
            self, uid: str, qa_pairs: dict[str, str], attention: int,
            vectors: dict[str, list[float]] = None
    ):

        res = {question: [] for question in qa_pairs.keys()}

        with catch_error():

            if len(qa_pairs := {question: answer for question, answer in qa_pairs.items() if answer}) == 0:

                return res

            task_body = {
                r'task_id': "None",
                r'content': None,
                r'type': r'Q',
                r'confidence': self._get_default_qa_confidence(r'Q'),
                r'parent_id': "None",
                r'attention': attention,
                r'status': 0
            }

            question_tasks = []
            for question in qa_pairs.keys():
                _copy = task_body.copy()
                _copy[r'content'] = question
                question_tasks.append(_copy)

            question_nodes = await self.insert_node(uid, question_tasks, vectors=vectors)

            if len(question_nodes) != len(qa_pairs):
                self.Break(f'batch insert qa node pair failed! {len(qa_pairs)} {len(question_nodes)=}')

            for question_node, (question, answer) in zip(question_nodes, qa_pairs.items()):

                copy = task_body.copy()
                copy.update({
                    "content": answer,
                    "type": "A_问答求解",
                    r'confidence': self._get_default_qa_confidence(r'A_问答求解'),
                    "parent_id": question_node,
                })

                answer_nodes = await self.insert_node(uid, [copy])

                if len(answer_nodes) > 0:

                    copy[r'id'] = answer_nodes[0]

                    res[question] = [copy]

        return res

    ##############################################################################################################
    # 以下为重构后的接口

    async def _rebuild_milvus_question_from_mongodb(self):

        with catch_error():

            mongo_collection = self.get_question_mongo_collection()

            total = await mongo_collection.count_documents({})
            page_size = 500

            cursor = mongo_collection.find({})

            for _index in range(self.math.ceil(total / page_size)):

                self.log.info(f'rebuild milvus question from mongodb {_index}')

                # _mongo_data = []
                _milvus_data = []

                for _doc in await cursor.to_list(length=page_size):

                    # if not isinstance(_doc[r'content'], str):
                    #     self.log.error(f'content type error: {_doc}')
                    #     continue
                    #
                    # _embeddings = await self._data_source.get_vector(_doc[r'content'])
                    #
                    # _mongo_data.append(
                    #     UpdateOne(
                    #         {
                    #             r'_id': _doc[r'_id'],
                    #         },
                    #         {
                    #             r'$set': {
                    #                 r'embeddings': _embeddings,
                    #             }
                    #         }
                    #     )
                    # )

                    _milvus_data.append(
                        {
                            r'id': _doc[r'_id'],
                            r'uid': _doc[r'uid'],
                            r'type': _doc[r'type'],
                            r'attention': _doc[r'attention'],
                            r'confidence': _doc[r'confidence'],
                            r'embeddings': _doc[r'embeddings'],
                        }
                    )

                # if _mongo_data:
                #     await self._data_source.get_mongo_collection(
                #         Config.MongoDBName,
                #         Config.DataStorageMongoQuestion
                #     ).bulk_write(
                #         _mongo_data,
                #         ordered=False
                #     )

                if _milvus_data:
                    await self._data_source.milvus_client.insert(
                        Config.MilvusCollectionQuestionName,
                        _milvus_data
                    )

        self.log.info(r'rebuild milvus question from mongodb finished')

    async def rebuild_milvus_question(self):

        result = False

        with catch_error():

            milvus_client = self._data_source.milvus_client

            _collection = Config.MilvusCollectionQuestionName

            if milvus_client.has_collection(_collection):
                milvus_client.drop_collection(_collection)

            await self._check_milvus_question_collection()

            await self._rebuild_milvus_question_from_mongodb()

            result = True

        return result

    async def rebuild_neo4j_question(self):

        with catch_error():

            await self._data_source.neo4j_client_for_qa.execute_query(r'MATCH (n:qa_container) DETACH DELETE n')
            await self._data_source.neo4j_client_for_qa.execute_query(r'MATCH (n:qa_content) DETACH DELETE n')
            await self._data_source.neo4j_client_for_qa.execute_query(r'MERGE (r:qa_container {name: "qa_root"})')

            mongo_collection = self.get_question_mongo_collection()

            parent_ids = [r'None']
            page_size = 100

            _sub_parent_ids = []

            while len(parent_ids) > 0:

                for _index in range(0, len(parent_ids), page_size):

                    _records = await mongo_collection.find(
                        {
                            r'parent_id': {
                                r'$in': parent_ids[_index: _index + page_size],
                            }
                        },
                        {
                            r'_id': 1,
                            r'uid': 1,
                            r'task_id': 1,
                            r'content': 1,
                            r'type': 1,
                            r'parent_id': 1,
                            r'attention': 1,
                            r'confidence': 1,
                            r'status': 1,
                        }
                    ).to_list(0xffff)

                    self.log.info(f'rebuild neo4j question from mongodb {_index}: {len(_records)}')

                    for _row in _records:

                        with catch_error():

                            await self._add_neo4j_node(
                                _row[r'_id'],
                                _row[r'uid'],
                                _row[r'task_id'],
                                _row[r'content'],
                                _row[r'type'],
                                _row[r'parent_id'],
                                _row[r'attention'],
                                _row[r'confidence'],
                                _row[r'status'],
                            )

                            _sub_parent_ids.append(_row[r'_id'])

                parent_ids, _sub_parent_ids = _sub_parent_ids, []

        self.log.info(r'rebuild neo4j question from mongodb finished')

    async def regenerate_question_fields(self):

        result = -1

        with (catch_error()):

            page_size = 100

            mongo_collection = self.get_question_mongo_collection()

            _total = await mongo_collection.count_documents({})
            cursor = mongo_collection.find({})
            _doc: dict

            for _ in range(self.math.ceil(_total / page_size)):

                for _doc in await cursor.to_list(length=page_size):
                    _update_fields, _type = {}, _doc[r'type']

                    if r'confidence' not in _doc and _type and _type.startswith("A"):

                        if _type == r'A_用户回答':
                            _update_fields[r'confidence'] = Config.DefaultQAUserAnswerConfi

                        else:
                            _update_fields[r'confidence'] = Config.DefaultQAAnswerConfi

                    if _type == r'Q' and _doc.get(r'confidence') != Config.DefaultQAQuestionConfi:

                        _update_fields[r'confidence'] = Config.DefaultQAQuestionConfi

                    if _update_fields:
                        self._update_queue_buffer.safe_append({
                                r'filter': {
                                    r'_id': _doc[r'_id'],
                                },
                                r'update': {
                                    r'$set': _update_fields
                                }
                            })

            result = _total

        return result

    @classmethod
    def _get_default_qa_confidence(cls, qa_type: str) -> int:

        match qa_type.strip():

            case r'Q':
                return Config.DefaultQAQuestionConfi

            case r'A_用户回答':
                return Config.DefaultQAUserAnswerConfi

            case item if item.startswith(r'A'):
                return Config.DefaultQAAnswerConfi

            case _:
                return Config.DefaultQAConfi

    async def insert_node(
            self, uid: str, task_list: typing.List[typing.Dict[str, typing.Any]],
            vectors: dict[str, list[float]] = None
    ):

        result = []

        with catch_error():

            self.log.info(f'insert qa node: {uid=} {task_list=}')

            now_time = self.timestamp()

            for _task in task_list:

                nid = self.uuid1_urn()

                if vectors is None or not (embeddings := vectors.get(_task[r'content'])):
                    embeddings = await self._data_source.get_vector(_task[r'content'])

                if _task.get(r'confidence') is None:

                    _task[r'confidence'] = self._get_default_qa_confidence(_task['type'])

                _doc = {
                    r'_id': nid,
                    r'uid': uid,
                    r'task_id': _task[r'task_id'],
                    r'content': _task[r'content'],
                    r'embeddings': embeddings,
                    r'type': _task['type'],
                    r'confidence': _task['confidence'],
                    r'parent_id': _task[r'parent_id'],
                    r'attention': _task[r'attention'],
                    r'status': _task[r'status'],
                    r'gmt_create': now_time,
                    r'gmt_modify': now_time,
                }

                await self._insert_queue_buffer.append(_doc)

                await self._add_neo4j_node(
                    _doc[r'_id'],
                    _doc[r'uid'],
                    _doc[r'task_id'],
                    _doc[r'content'],
                    _doc[r'type'],
                    _doc[r'parent_id'],
                    _doc[r'attention'],
                    _doc[r'confidence'],
                    _doc[r'status'],
                )

                result.append(nid)

        return result

    async def update_node(self, uid: str, node_id: str, status: int):

        result = False

        with catch_error():

            self.log.info(f'update qa node: {uid=} {node_id=} {status=}')

            await self._update_queue_buffer.append(
                {
                    r'filter': {
                        r'_id': node_id,
                    },
                    r'update': {
                        r'$set': {
                            r'status': status,
                            r'gmt_modify': self.timestamp(),
                        }
                    }
                }
            )

            await self._update_neo4j_node(node_id, status)

            result = True

        return result

    async def delete_node(self, uid: str, node_id: str):

        result = False

        with catch_error():

            self.log.info(f'delete qa node: {uid=} {node_id=}')

            await self._delete_queue_buffer.append(
                {
                    r'filter': {
                        r'_id': node_id,
                    },
                }
            )

            await self._del_neo4j_node(node_id)

            result = True

        return result

    async def query_by_question(self, uid: str, limit: int, question: typing.List[str]):

        result = []

        with catch_error():

            vectors = [await self._data_source.get_vector(val) for val in question]

            milvus_resp = await self._data_source.milvus_client.search(
                Config.MilvusCollectionQuestionName, vectors,
                search_params={
                    r'params': {
                        r'nprobe': 10,
                        r'radius': 0.7,
                    },
                },
                filter_=f'uid == "{uid}" and type == "Q"',
                limit=limit,
                output_fields=[r'id', r'uid', r'attention']
            )

            collection = self.get_question_mongo_collection()

            _node_ids = list(set([_item[r'id'] for _item in self.itertools.chain(*milvus_resp)]))

            mongo_resp = await collection.find(
                {r'_id': {r'$in': _node_ids}},
                {r'uid': 0, r'embeddings': 0, r'gmt_create': 0, r'gmt_modify': 0}
            ).to_list(len(_node_ids))

            mongo_dict = {_val[r'_id']: _val for _val in mongo_resp}

            neo4j_resp, _, _ = await self._get_neo4j_children_nodes(uid, _node_ids)
            neo4j_dict = {item[r'node_id']: item[r'children'] for item in neo4j_resp}

            for i in range(len(milvus_resp)):
                milvus_group = milvus_resp[i]

                _resp = {
                    r'question': question[i],
                    r'answer': []
                }

                for milvus_info in milvus_group:

                    if milvus_info[r'id'] not in mongo_dict:
                        continue

                    _qa = {
                        r'Q': {
                            r'id': milvus_info[r'id'],
                            r'score': milvus_info[r'distance'],
                            r'type': mongo_dict[milvus_info[r'id']][r'type'],
                            r'content': mongo_dict[milvus_info[r'id']][r'content'],
                            r'task_id': mongo_dict[milvus_info[r'id']][r'task_id'],
                            r'parent_id': mongo_dict[milvus_info[r'id']][r'parent_id'],
                            r'status': mongo_dict[milvus_info[r'id']][r'status'],
                            r'attention': mongo_dict[milvus_info[r'id']][r'attention'],
                            r'confidence': mongo_dict[milvus_info[r'id']][r'confidence']
                        },
                        r'A': neo4j_dict.get(milvus_info[r'id'], [])
                    }

                    _resp[r'answer'].append(_qa)

                result.append(_resp)

        return result

    async def query_by_node_id(self, uid: str, node_id: str):

        records = []

        with catch_error():

            _neo4j_resp, _, _ = await self._get_neo4j_nodes_recursively(uid, [node_id])
            if _neo4j_resp:
                records = _neo4j_resp[0].get(r'children')

        return records

    async def query_by_node_ids(self, uid: str, node_ids: list[str]):

        records = []

        with catch_error():

            _neo4j_resp, _, _ = await self._get_neo4j_nodes_recursively(uid, node_ids)
            records = {item[r'id']: item[r'children'] for item in _neo4j_resp}

        return records

    async def batch_get_vectors(self, content_list: list[str]) -> dict[str, list[float]]:

        result = None

        with catch_error():

            try:

                result = {content: (await self._data_source.get_vector(content)) for content in content_list}

            except OutOfMemoryError:

                self.log.error(f'get vector failed, out fo CUDA memory: {content_list=}')

        return result
