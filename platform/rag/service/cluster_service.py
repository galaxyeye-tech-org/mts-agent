# -*- coding: utf-8 -*-
# @FileName  : cluster_service.py
# @Description 文本聚类
# @Author： yangmingxing
# @Email: yangmingxing@galaxyeye-tech.com
# @Date 12/15/23 2:03 PM 
# @Version 1.0

import requests
import json
import numpy as np
import pandas as pd
import uuid
import datetime
import typing
import sklearn

from pymilvus import DataType
from hagworm.extend.asyncio.task import MultiTasks
from sklearn.cluster import KMeans
from hagworm.extend.asyncio.future import ThreadWorker
from service import ServiceBase, StorageQueueBuffer
from setting import Config
from hagworm.extend.error import catch_error
from pymongo import HASHED, DESCENDING, InsertOne, UpdateOne, DeleteOne


THREAD_WORKER = ThreadWorker(128)

def get_future_datetime(seconds):
    current_datetime = datetime.datetime.now()
    time_difference = datetime.timedelta(seconds=seconds)
    future_datetime = current_datetime + time_difference
    formatted_datetime = future_datetime.strftime("%Y-%m-%d %H:%M:%S")
    return formatted_datetime

class InsertQueueBuffer(StorageQueueBuffer):

    async def _handle_milvus(self, data_list: typing.List[dict]):

        data = []
        for _data in data_list:
            data.append(
                {
                    r'id': _data[r'text'].split("_")[1],
                    r'uid': _data[r'uid'],
                    r'cluster': _data[r'text'],
                    r'embeddings': _data[r'vec']
                }
            )

        await self._data_source.milvus_client.insert(
            Config.MilvusCollectionClusterName,
            data
        )

class DeleteQueueBuffer(StorageQueueBuffer):

    async def _handle_milvus(self, data_list: typing.List[dict]):
        pks = []

        for _data in data_list:
            pks.append(
                _data[r'id']
            )

        await self._data_source.milvus_client.delete(
            Config.MilvusCollectionClusterName,
            pks
        )

class ClusterService(ServiceBase):

    def __init__(self):
        super().__init__()

        self._insert_queue_buffer = InsertQueueBuffer(
            Config.DialogMongoQueueBufferMemoryMaxSize,
            Config.DialogMongoQueueBufferMemoryTimeout,
            Config.DialogMongoQueueBufferMemoryTaskLimit,
        )

        self._delete_queue_buffer = DeleteQueueBuffer(
            Config.DialogMongoQueueBufferMemoryMaxSize,
            Config.DialogMongoQueueBufferMemoryTimeout,
            Config.DialogMongoQueueBufferMemoryTaskLimit,
        )

    def get_cluster_text(self, impression):
        impression_values = Config.ClusterImpressionValues
        if len(impression_values) == 1:
            result_impression = impression[impression_values[0]]
        else:
            result_impression_list = [impression[value] for value in impression_values]
            result_impression = "，".join(result_impression_list)
        return result_impression

    async def release(self):
        pass

    async def initialize(self):
        await self.check_cluster_task_mongo_collection()
        await self.check_vectors_task_mongo_collection()
        await self._check_milvus_cluster_collection()

    async def check_cluster_task_mongo_collection(self):
        with catch_error():
            mongo_db = self._data_source.get_mongo_database(Config.MongoDBName)

            if not (names := await mongo_db.list_collection_names()) or \
                    Config.DataStorageMongoCluster not in set(names):
                _collection = mongo_db.get_collection(Config.DataStorageMongoCluster)

                await _collection.create_index([(r'uid', HASHED)])
                await _collection.create_index([(r'cluster_name', HASHED)])
                await _collection.create_index([(r'text', HASHED)])
                await _collection.create_index([(r'attention')])
                await _collection.create_index([(r'confidence')])
                await _collection.create_index([(r'origin_time')])
                await _collection.create_index([(r'expiration_time')])
                await _collection.create_index([(r'datetime')])
                await _collection.create_index([(r'timeout')])

                self.log.info(r'create train task mongo collection')

    async def check_vectors_task_mongo_collection(self):
        with catch_error():
            mongo_db = self._data_source.get_mongo_database(Config.MongoDBName)

            if not (names := await mongo_db.list_collection_names()) or \
                    Config.DataStorageMongoVec not in set(names):
                _collection = mongo_db.get_collection(Config.DataStorageMongoVec)

                await _collection.create_index([(r'uid', HASHED)])
                await _collection.create_index([(r'text', HASHED)])
                await _collection.create_index([(r'vec')])
                await _collection.create_index([(r'count')])
                await _collection.create_index([(r'datetime')])

                self.log.info(r'create train task mongo collection')

    @THREAD_WORKER
    def _check_milvus_cluster_collection(self):

        with catch_error():

            milvus_client = self._data_source.milvus_client

            _collection_name = Config.MilvusCollectionClusterName

            if not milvus_client.has_collection(_collection_name):

                _schema = milvus_client.create_schema()
                _schema.add_field(r'id', DataType.VARCHAR, is_primary=True, auto_id=False, max_length=50)
                _schema.add_field(r'uid', DataType.VARCHAR, max_length=50)
                _schema.add_field(r'cluster', DataType.VARCHAR, max_length=50)
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
                _collection.create_index(r'cluster', {r'index_type': r'Trie'}, index_name=r'idx_cluster')
            self.log.info(f'initialize question milvus collection: {_collection_name}')

    async def get_answer_node_from_qa(self, uid: str, impression: str) -> dict[str, list[str]]:

        result = {}
        with catch_error():

            vector = await self._data_source.get_vector(impression)
            milvus_resp = await self._data_source.milvus_client.search(
                Config.MilvusCollectionClusterName, [vector],
                search_params={
                    r'params': {
                        r'nprobe': 10,
                        r'radius': 0.7,
                    },
                },
                filter_=f'uid == "{uid}"',
                output_fields=[r'cluster', "embeddings"]
            )

            if len(qa_nodes := milvus_resp[0]) == 0:
                self.Break(f'{uid=}  {impression=} have no any matched question and answer!')
                result = {}
            else:
                result = [_item for _item in qa_nodes]
        return result

    async def add_mongo_cluster_vec(self, uid, text, vec, count):
        result = None

        with catch_error():
            collection = self.get_vec_mongo_collection()

            if isinstance(text, str):
                document = {
                    r'uid': uid,
                    r'text': text,
                    r'vec': vec,
                    r'count': count,
                    r'datetime': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                # milvus to do
                await self._insert_queue_buffer.append(document)
                await collection.insert_one(document)

            self.log.info(f'add media file info record ')
        return result

    async def update_mongo_cluster_vecs(self, filter, update_data):
        result = None

        with catch_error():
            collection = self.get_vec_mongo_collection()
            await collection.update_one(filter, update_data)

            self.log.info(f'add media file info record ')
        return result

    async def add_mongo_record(self, uid_impression, cluster_name=None):
        result = None

        with catch_error():
            collection = self.get_cluster_mongo_collection()

            if isinstance(uid_impression, dict):
                document = {
                    r'uid': uid_impression["uid"],
                    r'cluster_name': cluster_name,
                    r'summarize': uid_impression["summarize"],
                    r'describe': uid_impression["describe"],
                    r'attention': uid_impression["attention"],
                    r'confidence': uid_impression["confidence"],
                    r'origin_time': uid_impression["origin_time"],
                    r'timeout': uid_impression["timeout"],
                    r'expiration_time': uid_impression["expiration_time"],
                    r'datetime': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }

                await collection.insert_one(document)
            else:
                if uid_impression and len(uid_impression) > 0:
                    for impression in uid_impression:
                        if "_id" in impression.keys():
                            impression.pop("_id")

                        impression["cluster_name"] = cluster_name
                        impression["datetime"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                    await collection.insert_many(uid_impression)

            self.log.info(f'add media file info record ')
        return result

    async def delete_uid_pressions(self, filter):
        with catch_error():
            collection = self.get_cluster_mongo_collection()
            await collection.delete_many(filter)
            self.log.info(f'delete media file info record {filter}')

        return True

    async def delete_uid_cluster_vectors(self, uid):
        with catch_error():
            collection = self.get_vec_mongo_collection()
            document = {
                r'uid': uid
            }

            await collection.delete_many(document)
            self.log.info(f'delete media file info record {document=}')

        return True

    async def find_mongo_record(self, filter, screen=None):
        # if screen is None:
        #     screen = {"_id": 0}

        with catch_error():
            collection = self.get_cluster_mongo_collection()
            response = collection.find(filter, screen)
            self.log.info(f'find media file info record {response}')
            result = response

        return result

    async def find_mongo_vectors(self, filter, screen=None):
        if screen is None:
            screen = {"_id": 0}

        with catch_error():
            collection = self.get_vec_mongo_collection()
            response = collection.find(filter, screen)
            self.log.info(f'find media file info record {response}')
            result = response

        return result

    async def impression_classification(self, impressions):
        uid = None
        for impression in impressions:
            if not isinstance(impression.get("uid", ""), str) or len(impression.get("uid", "").strip()) < 1:
                return None, "params uid is error"

            if not isinstance(impression.get("summarize", ""), str) or len(impression.get("summarize", "").strip()) < 1:
                return None, "params summarize is error"

            if not isinstance(impression.get("describe", ""), str) or len(impression.get("describe", "").strip()) < 1:
                return None, "params describe is error"

            if not isinstance(impression.get("attention", ""), int) or impression.get("attention") < 1 or impression.get("attention") > 100:
                return None, "params attention is error"

            if uid is None:
                uid = impression.get("uid")

            if uid is not None and uid != impression.get("uid"):
                return None, "params uid is not same"

            if "timeout" not in impression.keys():
                impression["timeout"] = 604800

            if "confidence" not in impression.keys():
                impression["confidence"] = Config.ClusterConfidence

            if impression.get("confidence") < 1 or impression.get("confidence") > 5:
                return None, "params confidence is error"

            impression["origin_time"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            impression["expiration_time"] = get_future_datetime(impression.get("timeout"))
        return uid, impressions

    async def get_impression_vec(self, impression_list):
        tasks = MultiTasks()
        for impression in impression_list:
            tasks.append(self._data_source.get_vector(self.get_cluster_text(impression)))

        impression_vecs = await tasks
        np_impression_vecs = [impression_vec for impression_vec in impression_vecs]
        return np_impression_vecs

    async def checkout_cluster_threshold(self, uid, cluster_name, cluster_data, cluster_centers):
        # 返回两类： 游离的和成簇的
        free_impressions = []
        cluster_impressions = []
        if len(cluster_data) <= 1:
            free_impressions.extend(cluster_data)
        else:
            for impression_data in cluster_data:
                cluster_text = self.get_cluster_text(impression_data)
                similarity = await self.texts_similarity(uid, cluster_text, cluster_centers[cluster_name], True)
                if similarity >= Config.ClusterThreshold:
                    cluster_impressions.append(impression_data)
                else:
                    free_impressions.append(impression_data)

        if len(cluster_impressions) >= 2:
            similarity = await self.texts_similarity(uid, self.get_cluster_text(cluster_impressions[0]), self.get_cluster_text(cluster_impressions[1]))
            if similarity < Config.ClusterImpressionThreshold:
                free_impressions.extend(cluster_impressions)
                cluster_impressions = []

        return free_impressions, cluster_impressions

    async def texts_similarity(self, uid: str, text1: str, text2, cluster_similarity: bool=False):
        vector1 = await self._data_source.get_vector(text1)
        if cluster_similarity:
            vector2 = text2
        else:
            vector2 = await self._data_source.get_vector(text2)
        similarity = np.dot(vector1, vector2) / (np.linalg.norm(vector1) * np.linalg.norm(vector2))
        self.log.info(f'uid: {uid} -- similarity: {similarity} -- {text1}')
        return similarity

    async def save_cluster(self, uid, cluster_dic, cluster_centers, no_cluster=True):
        if not no_cluster:
            await self.add_mongo_record(cluster_dic, None)
        else:
            # 存储簇
            for cluster_name, cluster_data in cluster_dic.items():
                 free_impressions, cluster_impressions = await self.checkout_cluster_threshold(uid, cluster_name, cluster_data, cluster_centers)
                 if cluster_impressions:
                    # 计算总值
                    cluster_impressions_list = [impression["confidence"] * Config.ClusterConfidenceWeight for impression in cluster_impressions]
                    cluster_impressions_score = sum(cluster_impressions_list)

                    await self.add_mongo_record(cluster_impressions, cluster_name)
                    # 存储簇名称和簇中心
                    await self.add_mongo_cluster_vec(uid, cluster_name, cluster_centers[cluster_name], cluster_impressions_score)

                    if cluster_impressions_score >= Config.ClusterGuess:
                        await self.cluster_guess(uid, cluster_name, cluster_impressions)

                 await self.add_mongo_record(free_impressions, None)

    async def delete_cluster_guess(self, uid, cluster_ids):
        print("send mts delete cluster .............................")
        # 发送给mts
        content_info = {
            "uid": uid,
            "seq": str(uuid.uuid4()),
            "cluster_ids": cluster_ids
        }
        try:
            response = requests.post(f"http://{Config.ClusterMtsAgent}/mts_agent/summarize/v1/del_summarize",
                                     data=json.dumps(content_info), timeout=10)
            data = json.loads(response.content)
            self.log.info(f"delete cluster:{content_info} -- {data}")
        except Exception as e:
            self.log.error(f"send delete cluster fails:{str(e)} -- {content_info}")

    async def cluster_guess(self, uid, cluster_id, impressions):
        # print("send mts guess.............................")
        # 由簇生成猜想，发送给mts
        for impression in impressions:
            if "_id" in impression.keys():
                del impression["_id"]

        content_info = {
            "uid": uid,
            "seq": str(uuid.uuid4()),
            "cluster_id": cluster_id,
            "content_list": impressions
        }
        # 发送给mts
        try:
            response = requests.post(f"http://{Config.ClusterMtsAgent}/mts_agent/summarize/v1/summarize", data=json.dumps(content_info), timeout=10)
            data = json.loads(response.content)
            self.log.info(f"mts impressions:{content_info} -- {data}")
        except Exception as e:
            self.log.error(f"send mts impressions fails:{str(e)} -- {content_info}")

    async def get_max_similarity_cluster(self, uid, user_impression, cluster_count_list):
        # milvus to do
        result = await self.get_answer_node_from_qa(uid, self.get_cluster_text(user_impression))
        self.log.info(f'milvus search:{self.get_cluster_text(user_impression)} -- {result}')
        if result:
            return {"max_similarity": result[0].get("distance"), "cluster_name": result[0].get("entity").get("cluster")}
        else:
            return {}

        # max_similarity = 0.0
        # similarity_cluster = None
        # for cluster_count in cluster_count_list:
        #     similarity = await self.texts_similarity(uid, self.get_cluster_text(user_impression), cluster_count["vec"], True)
        #     if similarity > max_similarity:
        #         max_similarity = similarity
        #         similarity_cluster = cluster_count["text"]
        #
        # return {"max_similarity": max_similarity, "cluster_name": similarity_cluster}

    async def impression_cluster_mongo(self, uid, user_impression, cluster_info, mongo_cluster_count_list):
        # 游离数量不达标，存在簇, 簇分类入库或游离入库
        # 复制一个数据，进行前后对比，发送给mts
        user_free_impressions = []
        origin_cluster_count = {}

        mongo_cluster_count = {}
        for cluster_count in mongo_cluster_count_list:
            mongo_cluster_count[cluster_count["text"]] = cluster_count["count"]

        for cluster_impression in cluster_info:
            cluster_name = cluster_impression["cluster_name"]
            if cluster_name not in origin_cluster_count.keys():
                origin_cluster_count[cluster_name] = cluster_impression["confidence"] * Config.ClusterConfidenceWeight
            else:
                origin_cluster_count[cluster_name] += cluster_impression["confidence"] * Config.ClusterConfidenceWeight

        for impression in user_impression:
            # 比较相似度
            result = await self.get_max_similarity_cluster(uid, impression, mongo_cluster_count_list)
            if result and result["max_similarity"] >= Config.ClusterThreshold:
                impression["cluster_name"] = result["cluster_name"]
                cluster_info.append(impression)
                origin_cluster_count[result["cluster_name"]] += impression["confidence"] * Config.ClusterConfidenceWeight
                await self.add_mongo_record(impression, result["cluster_name"])
            else:
                # 没有进入簇的印象
                user_free_impressions.append(impression)

        for cluster_name, cluster_count in origin_cluster_count.items():
            send_mts_flag = False
            # 20240104 一个簇只会触发一次猜想
            if mongo_cluster_count[cluster_name] < Config.ClusterGuess:
                if cluster_count >= Config.ClusterGuess:
                    send_mts_flag = True
            # else:
            #     if cluster_count - mongo_cluster_count[cluster_name] >= Config.ClusterGuess:
            #         send_mts_flag = True

            if send_mts_flag:
                cluster_guess = [impression for impression in cluster_info if impression["cluster_name"] == cluster_name]
                await self.cluster_guess(uid, cluster_name, cluster_guess)
                # 更新mongo——vector的数据
                update_filter = {"text": cluster_name}
                update_data = {"$set": {"datetime": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                         "count": cluster_count}}
                await self.update_mongo_cluster_vecs(update_filter, update_data)
        return user_free_impressions

    async def user_impression_cluster_change(self, uid, user_impression):
        filter = {"uid": uid}

        # 删除一下过期的印象
        date_now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        delete_filter = {"uid": uid, "expiration_time": {"$lt": date_now}}
        await self.delete_uid_pressions(delete_filter)

        result = await self.find_mongo_record(filter)
        mongo_uid_impress = [data async for data in result]

        # 印象表信息信息
        cluster_info = [data for data in mongo_uid_impress if data.get("cluster_name")]
        impressions_cluster_id_list = [clster["cluster_name"] for clster in cluster_info]
        free_impression = [data for data in mongo_uid_impress if not data.get("cluster_name")]

        # cluster表聚类信息
        mongo_clusters = await self.find_mongo_vectors(filter)
        mongo_cluster_count_list = [mongo_cluster async for mongo_cluster in mongo_clusters]
        mongo_cluster_id_list = [clster["text"] for clster in mongo_cluster_count_list]

        dele_cluster_ids = list(set(mongo_cluster_id_list) - set(impressions_cluster_id_list))
        if dele_cluster_ids:
            await self.delete_cluster_guess(uid, dele_cluster_ids)

        #   查询vec所有的簇id   和 印象表的簇id
        #   1、比较两个簇id列表差异  删除vec中多余的簇id

        if len(free_impression) + len(user_impression) >= Config.ClusterFreeCluster:
            # 游离数量达标, 则发生聚类
            user_impression.extend(mongo_uid_impress)
            await self.user_impression_cluster(uid, user_impression, impressions_cluster_id_list)

        elif not cluster_info and len(free_impression) + len(user_impression) >= Config.ClusterFreeImpression:
            # 游离数量达标, 则发生聚类
            user_impression.extend(mongo_uid_impress)
            await self.user_impression_cluster(uid, user_impression, impressions_cluster_id_list)

        elif not cluster_info and len(free_impression) + len(user_impression) < Config.ClusterFreeImpression:
            # 游离数量不达标，不存在簇, 直接入库
            uid_impressions = [impression for impression in user_impression if impression["uid"] == uid]
            await self.add_mongo_record(uid_impressions)
        else:
            user_free_impressions = await self.impression_cluster_mongo(uid, user_impression, cluster_info, mongo_cluster_count_list)
            free_impression.extend(user_free_impressions)
            if len(free_impression) >= Config.ClusterFreeImpression:
                await self.user_impression_cluster(uid, free_impression, impressions_cluster_id_list, True)
            else:
                await self.add_mongo_record(user_free_impressions, None)

    async def cluster_kmeans(self, uid, impression_list, impression_vecs):
        # 选择可能的聚类数
        if len(impression_vecs)//3 <= 2:
            top_possible = 3
        else:
            top_possible = len(impression_vecs)//3

        if top_possible > len(impression_list):
            top_possible = len(impression_list)

        possible_k_values = range(1, top_possible)
        # 存储每个聚类数对应的聚类内误差
        inertia_values = []
        kmeans = None
        for k in possible_k_values:
            # 使用K均值算法
            kmeans = KMeans(n_clusters=k, random_state=42, n_init="auto")
            y_pred = kmeans.fit(impression_vecs)

            # 获取聚类内误差
            inertia_values.append(kmeans.inertia_)

        # 4. 获取聚类结果
        cluster_labels = kmeans.labels_
        cluster_centers = kmeans.cluster_centers_

        # 5. 分析聚类结果
        clusters = {}
        for i, label in enumerate(cluster_labels):
            if label not in clusters:
                clusters[label] = []
            clusters[label].append(impression_list[i])

        # 输出每个簇的文本
        cluster_dic = {}
        cluster_center = {}
        for index in range(len(clusters)):
            cluster_name = "簇_" + str(uuid.uuid4())
            cluster_dic[cluster_name] = list(clusters[index])
            # cluster_center[cluster_name] = cluster_centers[index].tolist()
            cluster_center[cluster_name] = sklearn.preprocessing.normalize([cluster_centers[index]], axis=1, norm='l2').tolist()[0]
        return cluster_dic, cluster_center

    async def user_impression_cluster(self, uid, user_impression, cluster_id_list, free_part=False):
        impression_vecs = await self.get_impression_vec(user_impression)
        try:
            cluster_dic, cluster_center = await self.cluster_kmeans(uid, user_impression, impression_vecs)

            if free_part:
                mongo_id = [free_impression["_id"] for free_impression in user_impression if "_id" in free_impression.keys()]
                if mongo_id:
                    await self.delete_uid_pressions({"uid": uid, "_id": {'$in': mongo_id}})
            else:
                # milvus to do
                screen = {"_id": 0, "text": 1}
                mongo_clusters = await self.find_mongo_vectors({"uid": uid}, screen)
                milvus_id = [cluster_info["text"].split("_")[1] async for cluster_info in mongo_clusters]
                if milvus_id:
                    for m_id in milvus_id:
                        await self._delete_queue_buffer.append({"id": m_id})

                # 删除mongo向量里的簇信息
                cluster_ids = list(set(cluster_id_list))
                if cluster_ids:
                    await self.delete_cluster_guess(uid, cluster_ids)

                await self.delete_uid_cluster_vectors(uid)
                await self.delete_uid_pressions({"uid": uid})

            await self.save_cluster(uid, cluster_dic, cluster_center)
        except Exception as e:
            self.log.error(f'cluster is error: {e}')
            await self.save_cluster(uid, user_impression, {}, False)

    async def search_impression_by_uid(self, uid: str):
        # 删除一下过期的印象
        date_now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        delete_filter = {"uid": uid, "expiration_time": {"$lt": date_now}}
        await self.delete_uid_pressions(delete_filter)

        screen = {"_id": 0, "uid": 0, "datetime": 0}
        result = await self.find_mongo_record({"uid": uid}, screen)
        mongo_uid_impress = [data async for data in result]
        impression_df = pd.json_normalize(mongo_uid_impress)
        if impression_df.empty:
            return {}
        impression_df.replace(np.nan, "游离印象", inplace=True)

        # 按多列分组
        cluster_group = {}
        grouped = impression_df.groupby(['cluster_name'])
        for name, group in grouped:
            cluster_group[name[0]] = group.to_dict(orient='records')

        return cluster_group

    async def impression_cluster(self, impressions: list):
        self.log.info(f'cluster rvc: {impressions}')
        result = False
        with catch_error():
            uid, impression_classification = await self.impression_classification(impressions)
            if uid is None:
                return result

            self.call_soon(self.user_impression_cluster_change, uid, impression_classification)
        return True

    async def search_impression(self, uid: str):
        result = False
        with catch_error():
            if uid is None or (uid is not None and len(uid.strip()) < 1):
                return result

        return await self.search_impression_by_uid(uid)