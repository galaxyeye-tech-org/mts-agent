#-*- encoding: utf-8 -*-
__author__ = 'Jianggb'

import asyncio
import json
import time
import typing
from typing import Optional, Union

from base.agent_public.agent_log import logger
from base.agent_http.agent_http_client import sendRequestSync
from base.agent_public.agent_tool import buildDialogueHistoryKey, buildOutputMapKey
from base.agent_public.agent_redis import AgentRedis
from base.agent_storage_client.agent_content import ContentResult
from base.service.memory_service import WorkMemoryService

from setting import BaseConfig


class StorageClient:

    def __init__(self):
        ""

    @staticmethod
    async def clear_dialogue_history(uid):
        history_key = buildDialogueHistoryKey(uid)
        AgentRedis().conn.delete(history_key)

    @staticmethod
    async def save_output_history(uid, content, resp_id=None, idx=None, tp="Q", role="user"):
        "对话存储,带格式"
        now_time = int(time.time()*1000)
        resp_id = resp_id if resp_id else "-1"
        idx = idx if idx else "0"
        msg = {"time":now_time, "uid": uid, "content": content, "type": tp, "resp_id":resp_id, "idx": idx, "role":role}
        logger.info(f"save_output_history {msg}")
        output_key = buildOutputMapKey(uid)
        AgentRedis().conn.lpush(output_key, str(msg))

    @staticmethod
    async def get_dialogue_history_last_time(uid):
        output_key = buildOutputMapKey(uid)
        output_len = AgentRedis().conn.llen(output_key)
        history = AgentRedis().conn.lrange(output_key, 0, 50)
        if output_len > 100:
            AgentRedis().conn.ltrim(output_key, 0, 50)
        dialogue_list, history_list, time_ret = StorageClient.trim_dialogue_history(history)
        if len(time_ret) == 0:
            return 9703571810791
        return time_ret[0]

    @staticmethod
    async def get_output_history(uid):
        output_key = buildOutputMapKey(uid)
        output_len = AgentRedis().conn.llen(output_key)
        history = AgentRedis().conn.lrange(output_key, 0, 50)
        if output_len > 100:
            AgentRedis().conn.ltrim(output_key, 0, 50)
        dialogue_list, history_list, time_ret = StorageClient.trim_dialogue_history(history)
        return history_list

    @staticmethod
    async def save_dialogue_history(uid, content, resp_id=None, idx=None, tp="Q", role="user", response_map=None):
        "对话存储"
        now_time = int(time.time()*1000)
        resp_id = resp_id if resp_id else "-1"
        idx = idx if idx else "0"
        msg = {"time":now_time, "uid": uid, "content": content, "type": tp, "resp_id":resp_id, "idx": idx, "role":role}
        logger.info(f"save_dialogue_history {msg}")
        history_key = buildDialogueHistoryKey(uid)
        AgentRedis().conn.lpush(history_key, str(msg))
        output_content = response_map if response_map else content
        await StorageClient.save_output_history(uid, output_content, resp_id=resp_id, idx=idx, tp=tp, role=role)

        return uid, content, resp_id, idx, tp, role, str(response_map)

    @staticmethod
    async def get_dialogue_history(uid):
        "history_list不包含最后一个用户输入"
        history_key = buildDialogueHistoryKey(uid)
        history_len = AgentRedis().conn.llen(history_key)
        history = AgentRedis().conn.lrange(history_key, 0, 99)
        if history_len > 200:
            AgentRedis().conn.ltrim(history_key, 0, 99)

        dialogue_list, history_list, time_ret = StorageClient.trim_dialogue_history(history)
        return dialogue_list, history_list

    @staticmethod
    def trim_dialogue_history(history:list):
        history_list:list[tuple[str, dict]] = []
        count = 0
        last_A_content_map = {}
        last_A_resp_id = ""
        last_A_saved = False
        last_A_role = "assistant"
        history.reverse()
        for item in history:
            msg = eval(item)
            msg_type = msg["type"]
            msg_content = str(msg["content"])
            msg_resp_id = msg["resp_id"]
            msg_idx = msg["idx"]
            msg_role = msg["role"]
            msg_time = msg["time"]
            if msg_type in ["Q", "q"]:
                if last_A_content_map and not last_A_saved:
                    history_list.append((last_A_role,last_A_content_map))
                    last_A_saved = True
                history_list.append((msg_role, {"0":(msg_content, msg_time)}))
                count += 1
            elif msg_type in ["A", "a"]:
                if not last_A_content_map:
                    last_A_resp_id = msg_resp_id
                    last_A_role = msg_role
                    last_A_content_map = {msg_idx: (msg_content, msg_time)}
                elif str(last_A_resp_id) != "-1" and last_A_resp_id == msg_resp_id:
                    last_A_content_map.update({msg_idx: (msg_content, msg_time)})
                else:
                    if not last_A_saved:
                        history_list.append((last_A_role,last_A_content_map))
                    last_A_resp_id = msg_resp_id
                    last_A_role = msg_role
                    last_A_content_map = {msg_idx: (msg_content, msg_time)}
                    last_A_saved = False

        if last_A_content_map and not last_A_saved:
            history_list.append((last_A_role,last_A_content_map))

        ret_history = []
        time_list = []
        for item in history_list:
            tp = item[0]
            content_map = item[1]
            content = ""
            key_list = list(content_map.keys())
            key_list.sort()
            content_time = 0
            for idx in key_list:
                content += content_map[idx][0]
                if content_time == 0:
                    content_time = content_map[idx][1]
                    time_list.append(content_time)

            tmp_dialogue = {"role":tp, "content":content}
            ret_history.append(tmp_dialogue)
        dialogue_list = []
        history_list = []
        if ret_history:
            dialogue_list = ret_history[-10:]
            history_list = dialogue_list
            if history_list and history_list[-1] and history_list[-1]["role"] == "user":
                history_list = history_list[:-1]
        time_ret = time_list[-10:]
        return dialogue_list, history_list, time_ret

    @staticmethod
    async def set_task_diffuse_energy(task, diffuse_energy):
        await ContentResult.set_task_diffuse_energy(task, diffuse_energy)

    @staticmethod
    async def get_task_diffuse_energy(task):
        return await ContentResult.get_task_diffuse_energy(task)

    @staticmethod
    async def add_task_llm_result(task, prompt_type, response):
        await ContentResult.add_task_llm_result(task, prompt_type, response)

    @staticmethod
    async def get_task_llm_result(task):
        return await ContentResult.get_task_llm_result(task)

    @staticmethod
    async def save_context(task, result:dict):
        await ContentResult.add_main_result(task, result)

    @staticmethod
    async def save_task_target(task, result:dict):
        await ContentResult.add_main_result(task, result)

    @staticmethod
    async def get_context(task):
        return await ContentResult.get_task_result(task)

    @staticmethod
    async def clear_context(task):
        return await ContentResult.clear_context(task)

    @staticmethod
    async def get_task_result_by_field(task, field):
        return await ContentResult.get_task_result_by_field(task, field)

    @staticmethod
    async def save_qa(uid, task_id, task_list):
        "task_list: {'taskid': 'taskid1','content': '我怎么去上海','type': 'Q','status': '进行中','parentid': 'taskid0'}"
        logger.info(f"{uid} 添加qa {task_list}")

        url = f'{BaseConfig.RagService}/common/qa/insert'

        data = {r'uid': uid, r'task_list':task_list}
        node_ids = []
        qa_resp = await sendRequestSync(url, data, uid=uid)
        if qa_resp and qa_resp[r'code'] == 0:
            node_ids = qa_resp[r'data'][r'node_ids']
        await ContentResult.add_main_result(task_id, {"添加qa":task_list})
        return node_ids
    
    @staticmethod
    async def get_qa(uid, task_id, content_list):
        """
        返回{"问题1":[{'taskid': 'taskid2', ‘Q':'怎么去上海','A': ['开车去上海'], "parentid":"taskid1"}], 
        "问题2":[{'taskid': 'taskid3', ‘Q':'我们怎么去上海','A': ['坐高铁去上海'], "parentid":"taskid1"}]}
        """
        logger.info(f"{uid} 查询qa {content_list}")
        data = {r'uid': uid, r'content': content_list, r'top': 5}

        url = f'{BaseConfig.RagService}/common/qa/search_by_content'

        if url:
            get_qa_resp = await sendRequestSync(url, data, uid=uid, timeout=10)
        else:
            answer_list = []
            idx = 1
            for content in content_list:
                answer_list.append({"taskid": idx, "Q": content, "A": ""})
                idx += 1
            get_qa_resp = {"code": "0", "msg":"ok", "data":[
                    {"question":"我怎么去上海","answer":answer_list
                    }
                ]
            }
        """
        {
        'code': 0,
        'msg': 'ok',
        'data': [
                {
                    "question":"我怎么去上海",
                    "answer":[]
                }
            ]
        }
        """
        if get_qa_resp:
            await ContentResult.add_main_result(task_id, {"查询qa": {"请求":data, "返回":get_qa_resp}})
        ret_map = {}
        if get_qa_resp and get_qa_resp[r'code'] == 0:
            content = get_qa_resp["data"]
            for question_map in content:
                question = question_map["question"]
                ret_map[question] = package_qa_response(question_map["answer"])
        """
        {"我怎么去上海":{}}
        """
        return ret_map

    @staticmethod
    async def query_by_nodeid(uid, task_id, node_id):
        logger.info(f"{uid} query_by_nodeid {node_id}")
        get_qa_resp = {}

        url = f'{BaseConfig.RagService}/common/qa/search_by_node_id'
        data = {r'uid': uid, 'node_id': node_id}

        get_qa_resp = await sendRequestSync(url, data, uid=uid, timeout=10)

        ret_map = {}
        if get_qa_resp and get_qa_resp["code"] == 0:
            ret_list = get_qa_resp["data"]
            ret_list = package_qa_list(ret_list)
            ret_map = package_qa_response(ret_list)
        return ret_map

    @staticmethod
    async def query_by_nodeids(uid, task_id, node_ids):
        logger.info(f"{uid} query_by_nodeids {node_ids}")
        get_qa_resp = {}

        url = f'{BaseConfig.RagService}/common/qa/search_by_node_ids'
        data = {r'uid': uid, 'node_ids': node_ids}

        get_qa_resp = await sendRequestSync(url, data, uid=uid, timeout=10)

        ret_map = {}
        if get_qa_resp and get_qa_resp["code"] == 0:
            data_ret_map:dict = get_qa_resp["data"]
            for nodeid in node_ids:
                node_ret_list = data_ret_map.get(nodeid, {})
                node_ret_list = package_qa_list(node_ret_list)
                node_ret_map = package_qa_response(node_ret_list)
                ret_map[nodeid] = node_ret_map
        return ret_map

    @staticmethod
    async def get_qa_answer(uid, task_id, content, attention):
        logger.info(f"{uid} get_qa_answer {content}")
        data = {"uid": uid, "content": content}
        get_qa_resp = {}
        url = f"{BaseConfig.RagService}/storage/user/qa/answer"
        get_qa_resp = await sendRequestSync(url, data, uid=uid, timeout=10)
        await ContentResult.add_main_result(task_id, {"qa/answer": {"请求":data, "返回":get_qa_resp}})
        if "code" in get_qa_resp and get_qa_resp["code"] == 0:
            get_qa_resp = get_qa_resp["data"]
        else:
            logger.info(f"get_qa_answer error {get_qa_resp}")
        
        ret_answer = {}
        if content in get_qa_resp and get_qa_resp[content]:
            ret_answer = get_qa_resp[content][0]
        else:
            sm_content = list(get_qa_resp.values())[0]
            ret_answer = get_qa_resp[sm_content][0]

        return ret_answer

    @staticmethod
    async def get_qa_and_memory_answer(uid, task_id, content, attention):
        logger.info(f"{uid} get_qa_and_memory_answer {content}")
        data = {"uid": uid, "content": content, "attention":attention}
        get_qa_resp = {}
        url = f"{BaseConfig.RagService}/storage/user/qa_and_memory/answer"
        get_qa_resp = await sendRequestSync(url, data, uid=uid, timeout=60)
        await ContentResult.add_main_result(task_id, {"qa_and_memory/answer": {"请求":data, "返回":get_qa_resp}})
        if "code" in get_qa_resp and get_qa_resp["code"] == 0:
            get_qa_resp = get_qa_resp["data"]
        else:
            logger.info(f"get_qa_answer error {get_qa_resp}")
        ret_answer = {}
        if content in get_qa_resp and get_qa_resp[content]:
            ret_answer = get_qa_resp[content][0]
        return ret_answer

    @staticmethod
    async def get_qa_answer_batch(uid, task_id, content_list, attention):
        logger.info(f"{uid} get_qa_answer_batch {content_list}")
        data = {"uid": uid, "content_list": content_list}
        get_qa_resp = {}
        url = f"{BaseConfig.RagService}/storage/user/qa/batch_answer"
        get_qa_resp = await sendRequestSync(url, data, uid=uid, timeout=60)
        await ContentResult.add_main_result(task_id, {"qa/batch_answer": {"请求":data, "返回":get_qa_resp}})
        if "code" in get_qa_resp and get_qa_resp["code"] == 0:
            get_qa_resp = get_qa_resp["data"]
        else:
            logger.info(f"get_qa_answer_batch error {get_qa_resp}")
        
        ret_answer = {}
        for content in content_list:
            if content in get_qa_resp and get_qa_resp[content]:
                if content in get_qa_resp[content]:
                    ret_answer[content] = get_qa_resp[content][content][0]
                else:
                    sm_content = list(get_qa_resp[content].values())[0]
                    ret_answer[content] = get_qa_resp[content][sm_content][0]
            else:
                ret_answer[content] = {}

        return ret_answer

    @staticmethod
    async def get_qa_and_memory_answer_batch(uid, task_id, content_list, attention):
        logger.info(f"{uid} get_qa_and_memory_answer_batch {content_list}")
        data = {"uid": uid, "content_list": content_list, "attention":attention}
        get_qa_resp = {}
        url = f"{BaseConfig.RagService}/storage/user/qa_and_memory/batch_answer"
        get_qa_resp = await sendRequestSync(url, data, uid=uid, timeout=60)
        await ContentResult.add_main_result(task_id, {"qa_and_memory/batch_answer": {"请求":data, "返回":get_qa_resp}})
        if "code" in get_qa_resp and get_qa_resp["code"] == 0:
            get_qa_resp = get_qa_resp["data"]
        else:
            logger.info(f"get_qa_and_memory_answer_batch error {get_qa_resp}")
        ret_answer = {}
        for content in content_list:
            if content in get_qa_resp and get_qa_resp[content]:
                ret_answer[content] = get_qa_resp[content][0]
            else:
                ret_answer[content] = {}
        return ret_answer

    @staticmethod
    async def query_knowledge_by_content(
            uid: str, query: str, diffusion: typing.Optional[list[str]] = None, limit: typing.Optional[int] = None,
            radius: typing.Optional[float] = None,
            max_token: int = 50000
    ) -> list[str]:
        """

        """

        logger.info(f"{uid} get_knowledge_by_content {uid=} {query=} {diffusion=} {limit=} {radius=} {max_token=}")

        if diffusion is None:
            diffusion = []

        url = f'{BaseConfig.RagService}/common/document/search'
        data = {r'uid': uid, r'query': query, r'diffusion': diffusion, r'max_token': max_token}

        if radius is not None:
            data[r'radius'] = radius

        if limit is not None:
            data[r'limit'] = limit

        resp: dict = await sendRequestSync(url, data, uid=uid, timeout=5)

        contents = []

        if not resp or resp['code'] != 0:
            logger.info(f"get_knowledge_by_content error {data=} {resp=}")
            return contents

        contents = [doc_record[r'paragraph'] for doc_record in resp[r'data'][r'vector_result']]

        if contents:
            #logger.info(f"写入knowledge工作记忆: {uid} {contents}")
            await StorageClient.save_work_memory(uid, json.dumps(contents, ensure_ascii=False), int(time.time()*1000), 
                        100, 0.1, **{"type":"knowledge"})

        return contents

    @staticmethod
    async def save_work_memory(
            uid: str, content: Optional[Union[str, dict]],
            timestamp: float = None, attention: int = 100, per_attention_quit_second: int = 1,
            **kwargs
    ):
        if not uid:
            raise Exception(f'uid is invalid, {uid=}')
        logger.info(f" 写入工作记忆: {uid} {content=} {kwargs=}")
        expire_time = 100
        if attention and attention > 0:
            expire_time = attention / per_attention_quit_second

        if not timestamp:
            timestamp = int(time.time() * 1000)

        await WorkMemoryService().save_memory_of_user(uid, timestamp, attention, content, expire_time, **kwargs)

    @staticmethod
    async def get_all_work_memory(uid: str) -> str:
        ret = {}
        ret.update(await StorageClient.get_work_memory(uid))
        ret["qa"] = await StorageClient.get_qa_work_memory(uid)
        ret["embedding"] = await StorageClient.get_embedding_work_memory(uid)
        ret["对话策略"] = await StorageClient.get_dialogue_strategy_work_memory(uid)
        ret["knowledge"] = await StorageClient.get_knowledge_work_memory(uid)
        return ret

    @staticmethod
    async def get_work_memory(uid: str, last_time=9703571810791) -> dict:
        work_memory_list = await WorkMemoryService().get_memories_of_user(uid)
        ret:dict[str, list[dict]] = {}
        for memory_map in work_memory_list:
            if "content" in memory_map and "type" in memory_map and memory_map['type'] in ["用户陈述", "印象", "结论"]:
                tp = memory_map['type']
                if tp not in ret:
                    ret[tp] = []
                if memory_map['content'] not in ret[tp]:
                    if tp == "用户陈述" and 'timestamp' in memory_map and \
                        last_time < memory_map['timestamp']:
                        continue
                    ret[tp].append(memory_map)
        
        ret = StorageClient.trim_memory(ret)
        
        return ret

    @staticmethod
    def trim_memory(memory_map:dict[str, list[dict]], limit=10):
        "将过多的数据删除，只保留最新的10条"
        del_tp = []
        for tp in memory_map:
            if not memory_map[tp]:
                del_tp.append(tp)
        for tp in del_tp:
            del memory_map[tp]
        ret_memory_map:dict[str, list[dict]] = {}
        for tp in memory_map:
            if tp not in ret_memory_map:
                ret_memory_map[tp] = []
            for memory in memory_map[tp]:
                if len(ret_memory_map[tp]) < limit:
                    ret_memory_map[tp].append(memory)
                elif "timestamp" in memory:
                    del_memory = None
                    for tmp_memory in ret_memory_map[tp]:
                        if "timestamp" not in tmp_memory:
                            del_memory = tmp_memory
                            break
                        elif "timestamp" in tmp_memory and memory['timestamp'] > tmp_memory['timestamp']:
                            if not del_memory:
                                del_memory = tmp_memory
                            else:
                                if del_memory['timestamp'] > tmp_memory['timestamp']:
                                    del_memory = tmp_memory
                    if del_memory:
                        ret_memory_map[tp].remove(del_memory)
                        ret_memory_map[tp].append(memory)
        tmp_ret_memory_map:dict[str, list[str]] = {}
        for tp in ret_memory_map:
            if tp not in tmp_ret_memory_map:
                tmp_ret_memory_map[tp] = []
            for memory in ret_memory_map[tp]:
                tmp_ret_memory_map[tp].append(memory['content'])
        return tmp_ret_memory_map

    @staticmethod
    async def get_qa_work_memory(uid: str) -> list:
        work_memory_list = await WorkMemoryService().get_memories_of_user(uid)
        qa_node_list = []
        for memory_map in work_memory_list:
            if "content" in memory_map and memory_map['content'] not in qa_node_list and \
                "type" in memory_map and memory_map['type'] == "qa":
                qa_node_list.append(memory_map['content'])
        question_answer_dict = {}
        unsolved_question = set()
        node_q_map = await StorageClient.query_by_nodeids(uid, uid, qa_node_list)
        for node_id in qa_node_list:
            q_map = node_q_map[node_id]
            for qa_question in q_map:
                task_item = q_map[qa_question]
                if task_item['A']:
                    question_answer_dict[task_item['Q']] = task_item['A']
                elif task_item['Q'] not in unsolved_question:
                    unsolved_question.add(task_item['Q'])
        ret = {"question_answer_dict":question_answer_dict, "unsolved_question":list(unsolved_question)}
        return ret

    @staticmethod
    async def get_embedding_work_memory(uid: str, last_time=9703571810791) -> dict:
        work_memory_list = await WorkMemoryService().get_memories_of_user(uid)
        embedding_map_list = []
        for memory_map in work_memory_list:
            if "content" in memory_map and "type" in memory_map and memory_map['type'] == "embedding":
                embedding_map_tmp = json.loads(memory_map['content'])
                """{"type": tp, "content": memory_map['content'], "attention": memory_map['attention',"timestamp":int]}"""
                if isinstance(embedding_map_tmp, dict):# 兼容之前版本的工作记忆写入
                    for tp in embedding_map_tmp:
                        for content in embedding_map_tmp[tp]:
                            embedding_map = {"type": tp, "content": content,"attention": 50}
                            embedding_map_list.append(embedding_map)
                elif isinstance(embedding_map_tmp, list):
                    for embedding_map in embedding_map_tmp:
                        if embedding_map['type'] == "用户陈述" and "timestamp" in embedding_map \
                            and last_time < embedding_map['timestamp']:
                            continue
                        embedding_map_list.append(embedding_map)
        sorted_data = sorted(embedding_map_list, key=lambda x: int(x['attention']), reverse=True)
        ret_embedding_map = {}
        count = 0
        for embedding_map in sorted_data:
            tp = embedding_map['type']
            if tp not in ret_embedding_map:
                ret_embedding_map[tp] = []
            if embedding_map['content'] not in ret_embedding_map[tp]:
                ret_embedding_map[tp].append(embedding_map['content'])
                count += 1
            if count > 5:
                break
        del_tp = []
        for tp in ret_embedding_map:
            if not ret_embedding_map[tp]:
                del_tp.append(tp)
        for tp in del_tp:
            del ret_embedding_map[tp]
        return ret_embedding_map

    @staticmethod
    async def get_dialogue_strategy_work_memory(uid: str) -> list:
        """
        :return:
        [{
            'id': '8b245a76-a0a3-11ee-ac71-000c291fec16',
            'robot_id': 'agent001',
            'attention': 60,
            '意图': '劝导用户',
            '执行': '你应该使用柔和的语言劝导用户，避免情绪化的对抗；并提供相应的证据与事实，用事实和数据来支持你的观点。',
            '用户状态': '用户态度较强硬，不接受他人的正确意见',
            '策略表述': '要是用户态度较强硬，还一直不听其他人的建议，你不要和他硬碰硬，应该柔和的和他说，再给他一些相似的案例。'
        }]
        """
        work_memory_list = await WorkMemoryService().get_memories_of_user(uid)

        strategies = []
        ids = set()

        for memory_map in work_memory_list:
            if r'content' in memory_map and memory_map.get(r'type') == r'对话策略':
                strategy = json.loads(memory_map['content'])
                if strategy[r'id'] in ids:
                    continue

                strategies.append(strategy)
                ids.add(strategy[r'id'])

        return strategies

    @staticmethod
    async def get_knowledge_work_memory(uid: str) -> list:
        work_memory_list = await WorkMemoryService().get_memories_of_user(uid)

        knowledge_list = []

        for memory_map in work_memory_list:
            if "content" in memory_map and "type" in memory_map and memory_map['type'] == "knowledge":
                tmp_knowledge_list = json.loads(memory_map['content'])
                if isinstance(tmp_knowledge_list, list):
                    for tmp_knowledge in tmp_knowledge_list:
                        if tmp_knowledge not in knowledge_list:
                            knowledge_list.append(tmp_knowledge)

        knowledge_list = knowledge_list[-10:]
        return knowledge_list

    @staticmethod
    async def save_intention(uid: str, robot_id: str, data: dict):

        return await WorkMemoryService().save_intention_for_user_robot_id(uid, robot_id, data)

    @staticmethod
    async def get_intention(uid: str, robot_id: str) -> dict:

        return await WorkMemoryService().get_intention_for_user_robot_id(uid, robot_id)

    @staticmethod
    async def memory_add(uid, content, attention, **kwargs):
        confidence = 40
        if "confidence" in kwargs:
            confidence = int(kwargs["confidence"])
            del kwargs["confidence"]
        tp = "用户陈述"
        if "type" in kwargs:
            tp = kwargs["type"]
            del kwargs["type"]
        add_msg = {"uid": uid,"timestamp": int(time.time()*1000),"attention": attention, 
                    "content": content, "confidence":confidence, "type": tp}
        if kwargs:
            add_msg["other_data"] = kwargs
        logger.info(f"{uid} memory_add {add_msg}")
        url = f"{BaseConfig.RagService}/storage/user/memory/add"
        memory_add_resp = await sendRequestSync(url, add_msg, uid=uid, timeout=10)
    
    @staticmethod
    async def memory_get(uid, content, attention=10, limit=5, last_time=9703571810791):
        get_msg = {"uid": uid,"content": content,"limit": limit}
        logger.info(f"{uid} memory_get {get_msg}")
        url = f"{BaseConfig.RagService}/storage/user/memory/get"
        memory_get_resp = await sendRequestSync(url, get_msg, uid=uid, timeout=10)
        ret_memory = {}
        work_memory = []
        if "code" in memory_get_resp and str(memory_get_resp["code"]) == "0" and "data" in memory_get_resp:
            ret_list:list[dict] = memory_get_resp["data"]
            for memory_map in ret_list:
                if "other_data" in memory_map and memory_map["other_data"]:
                    memory_map.update(memory_map["other_data"])
                    del memory_map["other_data"]
                tp = memory_map["type"] if "type" in memory_map else "用户陈述"
                if tp not in ret_memory:
                    ret_memory[tp] = []
                if memory_map['content'] not in ret_memory[tp]:
                    if tp == "用户陈述" and last_time < memory_map["timestamp"]:
                        continue
                    ret_memory[tp].append(memory_map['content'])
                    work_memory.append({"type": tp, "content": memory_map['content'], 
                                        "attention": memory_map['attention'],"timestamp":memory_map["timestamp"]})
        del_tp = []
        for tp in ret_memory:
            if not ret_memory[tp]:
                del_tp.append(tp)
        for tp in del_tp:
            del ret_memory[tp]
        if ret_memory:
            #logger.info(f"写入embedding工作记忆: {uid} {work_memory}")
            await StorageClient.save_work_memory(uid, json.dumps(work_memory, ensure_ascii=False), int(time.time()*1000), 
                        100, 0.1, **{"type":"embedding"})
        return ret_memory

    @staticmethod
    async def memory_get_page(uid, tp, limit=50):
        get_msg = {"uid": uid,"type": tp,"limit": limit, "cursor":0}
        logger.info(f"{uid} memory_get_page {get_msg}")
        url = f"{BaseConfig.RagService}/storage/user/all_memory/page"
        memory_get_resp = await sendRequestSync(url, get_msg, uid=uid, timeout=10)
        ret_memory_list:list = []
        if "code" in memory_get_resp and str(memory_get_resp["code"]) == "0" and "data" in memory_get_resp:
            ret_data = memory_get_resp["data"]
            cursor = ret_data["cursor"]
            ret_memory_list.extend(ret_data["infos"])
            while cursor:
                get_msg["cursor"] = cursor
                memory_get_resp = await sendRequestSync(url, get_msg, uid=uid, timeout=10)
                if "code" in memory_get_resp and str(memory_get_resp["code"]) == "0" and "data" in memory_get_resp:
                    ret_data = memory_get_resp["data"]
                    cursor = ret_data["cursor"]
                    ret_memory_list.extend(ret_data["infos"])
                else:
                    cursor = None

        return ret_memory_list

    @staticmethod
    async def memory_delete(uid, id):
        del_msg = {"id": id}
        logger.info(f"{uid} memory_delete {del_msg}")
        url = f"{BaseConfig.RagService}/storage/user/memory/delete"
        memory_delete_resp = await sendRequestSync(url, del_msg, uid=uid, timeout=10)

    @staticmethod
    async def all_memory_delete(uid):
        del_msg = {"uid": uid}
        logger.info(f"{uid} all_memory_delete {del_msg}")
        url = f"{BaseConfig.RagService}/storage/user/all_memory/delete"
        all_memory_delete_resp = await sendRequestSync(url, del_msg, uid=uid, timeout=10)

    @staticmethod
    async def add_cluster(uid, summarize:list[dict]):
        """
         [{"summarize": "早熟因家庭环境7777","describe": "小林由于家庭因素成长过早，承担了超越年龄的心理压力","attention": 88}
         ]
        """
        impression_list = []
        for impression in summarize:
            impression["uid"] = uid
            impression_list.append(impression)

        logger.info(f"{uid} add_cluster {impression_list}")
        impression_map = {"impression": impression_list}

        url = f"{BaseConfig.RagService}/cluster/impression_cluster"
        add_cluster_resp = await sendRequestSync(url, impression_map, uid=uid, timeout=10)

    @staticmethod
    async def add_dialogue_strategy(robot_id: str, data: dict, attention: int):
        """
        添加对话策略
        """

        logger.info(f'{robot_id=} add_dialogue_strategy {data=}')
        url = f'{BaseConfig.RagService}/strategy/dialogue/add'

        body = {
            r'robot_id': robot_id,
            r'data': data,
            r'attention': attention,
        }

        resp = await sendRequestSync(url, body)

        if resp == r'' or resp.get(r'code') != 0:
            # 此处有一个错误
            return None

        return resp[r'data']

    @staticmethod
    async def page_all_dialogue_strategy(robot_id: str, limit=1000) -> Optional[dict]:
        """
        批量获取对话策略
        """

        logger.info(f'{robot_id=} page_all_dialogue_strategy {limit=}')

        url = f'{BaseConfig.RagService}/strategy/dialogue/page'

        body = {
            r'robot_id': robot_id,
            r'limit': limit,
        }

        resp = await sendRequestSync(url, body)

        if resp == r'' or resp.get(r'code') != 0:
            return None

        return resp[r'data'][r'infos']

    @staticmethod
    async def get_dialogue_strategies_by_intention(robot_id: str, content: str, limit: int = 1000) -> Optional[dict]:

        logger.info(f'{robot_id=} {content=} get_dialogue_strategies_by_intention {limit=}')

        url = f'{BaseConfig.RagService}/strategy/dialogue/get'

        body = {
            r'robot_id': robot_id,
            r'content': content,
            r'limit': limit,
        }

        resp = await sendRequestSync(url, body)

        if resp == r'' or resp.get(r'code') != 0:
            return None

        return resp[r'data']

def package_qa_list(qa_list:list[dict]):
    """
    将[{'taskid': 'taskid1','content': '我怎么去上海Q','type': 'Q','status': '进行中','parent_id': 'nodeid0', “id”:”nodeid1”},
       {'taskid': 'taskid1','content': '我怎么去上海A','type': 'A','status': '进行中','parent_id': nodeid1, “id”:”nodeid2”}]列表
    转成
    [{
	“Q”:{'taskid': 'taskid1','content': '我怎么去上海Q','type': 'Q','status': '进行中','parentid': 'nodeid0', “id”:”nodeid1”},
	“A”:[
		{'taskid': 'taskid1','content': '我怎么去上海A','type': 'A','status': '进行中','parent_id': nodeid1, “id”:”nodeid2”}
        ]
    }]
    """
    node_map = {}
    parent_map:dict[str, list] = {}
    q_node_list = []
    for question_map in qa_list:
        nodeid = question_map["id"]
        node_map[nodeid] = question_map
        parentid = question_map["parent_id"]
        if question_map["type"] == "Q":
            q_node_list.append(nodeid)
        if parentid not in parent_map:
            parent_map[parentid] = []
        parent_map[parentid].append(nodeid)

    ret_list = []
    for parentid in q_node_list:
        if parentid == "None" or parentid not in node_map:
            continue
        if parentid not in parent_map:
            ret_list.append({"Q": node_map[parentid], "A": []})
            continue
        ret_map = {"Q": node_map[parentid], "A": []}
        for nodeid in parent_map[parentid]:
            if "A_" in node_map[nodeid]["type"]:
                ret_map["A"].append(node_map[nodeid])
        ret_list.append(ret_map)
    return ret_list


def package_qa_response(qa_list:list[dict[str,dict]]):
    """
    [{
	“Q”:{'task_id': 'taskid1','content': '我怎么去上海Q','type': 'Q','status': '进行中','parent_id': 'nodeid0', “id”:”nodeid1”},
	“A”:[
		{'task_id': 'taskid1','content': '我怎么去上海A','type': 'A','status': '进行中','parent_id': nodeid1, “id”:”nodeid2”}
        ]
    }]
    """
    ret_dict = {}
    for qa_dict in qa_list:
        if "Q" not in qa_dict or "A" not in qa_dict or "task_id" not in qa_dict["Q"] or\
             "content" not in qa_dict["Q"] or "id" not in qa_dict["Q"]:
            logger.info(f"qa_dict {qa_dict} is not correct")
            continue
        ret_dict[qa_dict["Q"]["content"]] = {"taskid": qa_dict["Q"]["task_id"], "Q": qa_dict["Q"]["content"],
                                             "nodeid": qa_dict["Q"]["id"], "parentid": qa_dict["Q"]["parent_id"]}
        a_list = []
        for a_dict in qa_dict["A"]:
            if "content" not in a_dict:
                logger.info(f"a_dict {a_dict} is not correct")
                continue
            a_list.append(a_dict["content"])
        ret_dict[qa_dict["Q"]["content"]]["A"] = a_list
    """
    {"我怎么去上海Q":{"taskid":'taskid1',"Q":'我怎么去上海Q',"nodeid":”nodeid1”,"A":["我怎么去上海A"], 'parentid': 'nodeid0'}}
    """
    return ret_dict


if __name__ == '__main__':
    async def main():
        qa_map = {'1': '用户是否经常感到焦虑，特别是在事物没有按照特定的方式组织时？', 
                  '2': '用户是否有反复检查事物以确保它们处于完美状态的行为？', 
                  '3': '用户是否有因为事物没有完全按照计划进行而感到极度不安或沮丧的情况？', 
                  '4': '用户是否花费大量时间来规划和组织事务，以至于它影响了他们的日常生活或工作效率？', 
                  '5': '用户是否对细节的关注到了影响生活质量的程度？', 
                  '6': '用户是否有因为无法控制所有细节而感到沮丧或焦虑的情况？', 
                  '7': '用户是否有强迫性的行为，比如不断清洁或整理，即使这些行为没有实际的必要性？', 
                  '8': '用户的家人、朋友或同事是否觉得用户的计划和组织行为过于严格或不合理？', 
                  '9': '用户是否有在没有任何外部压力的情况下，自我施加过度组织和计划的倾向？', 
                  '10': '用户是否有因为事物不完美而避免某些活动或情况的行为？'
                }
        uid = "xtest006"
        ret = await StorageClient().get_qa_and_memory_answer_batch(uid, uid, list(qa_map.values()), 10)
        ret = json.dumps(ret, ensure_ascii=False)
        logger.info(f"last_time:{ret}")
        
    
    coroutine_id = main.__qualname__
    logger.info(f" 启动协程 {coroutine_id}")
    asyncio.run(main())
    # msgDic = {'uid': 'jgbtest1016', 'seq': '99099', 'content': '然后运动久了也会有点晕。', 'target': '问题分解', 'task_id': 'cmrtest009_1703054131544', 'source': '对话管理', '写入函数': 'dialogue_management_service.py:46:dialogue_management_service', 'attention': '80', 'divide': [11, 22, 32], 'parent_id': ['0-0'], 'msg_id': '1703054134862-0', 'embbeding': '', 'role': '医生'}
    # StorageClient.memory_add(msgDic["uid"], msgDic["content"], int(msgDic["attention"]), **{"source": f"思绪流_{self.model}"})
    # logger.info(StorageClient.memory_get("jgbtest1016"))
    