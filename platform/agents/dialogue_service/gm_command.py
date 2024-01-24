#-*- encoding: utf-8 -*-
__author__ = 'Jianggb'


"""对话接入和表达发出"""
import json
import time, asyncio

from base.agent_public.agent_log import logger
from base.large_model_client.agent_llm import request_llm
from base.thoughts_flow_client.thoughtsFlow import ThoughtFlow
from base.agent_public.agent_tool import check_param
from base.agent_storage_client.agent_content import ContentResult
from base.agent_storage_client.user_status import UserStatus
from base.agent_storage_client.agent_storage import StorageClient

class GmCommand:
    def __init__(self):
        pass
    
    @classmethod
    async def parse_request(cls, thtFlow:ThoughtFlow, query:dict):
        ""
        check_param(query, ["uid", "method", "seq"])
        _uid = query["uid"]
        now_time = int(time.time()*1000)
        _seq = query["seq"] if "seq" in query else now_time
        _method = query["method"]
        match _method:
            case "insert_stream":
                check_param(query, ["data"])
                return await cls.insert_stream(_uid, _seq, query["data"], thtFlow)
            case "set_exp_status":
                check_param(query, ["data"])
                return await cls.set_exp_status(_uid, _seq, query["data"], thtFlow)
            case "get_exp_status":
                return await cls.get_exp_status(_uid, _seq, thtFlow)
            case "set_model_attention":
                check_param(query, ["data"])
                return await cls.set_model_attention(_uid, _seq, query["data"], thtFlow)
            case "get_model_attention":
                return await cls.get_model_attention(_uid, _seq, thtFlow)
            case "set_public_attention_ratio":
                check_param(query, ["data"])
                return await cls.set_public_attention_ratio(_uid, _seq, query["data"], thtFlow)
            case "get_public_attention_ratio":
                return await cls.get_public_attention_ratio(_uid, _seq, thtFlow)
            case "get_last_task":
                return await cls.get_last_task(_uid, _seq, thtFlow)
            case "get_work_memory":
                return await cls.get_work_memory(_uid, _seq, thtFlow)
            case "get_llm_result":
                check_param(query, ["data"])
                return await cls.get_llm_result(_uid, _seq, query["data"], thtFlow)
            case "get_history_dialog":
                return await cls.get_history_dialog(_uid, _seq, thtFlow)
            case "delete_last_task":
                return await cls.delete_last_task(_uid, _seq, thtFlow)
            case "get_memory_by_content":
                check_param(query, ["data"])
                return await cls.get_memory_by_content(_uid, _seq, query["data"], thtFlow)
            case "get_qa_by_content":
                check_param(query, ["data"])
                return await cls.get_qa_by_content(_uid, _seq, query["data"], thtFlow)
            case "get_robot_role":
                return await cls.get_robot_role(_uid, _seq, thtFlow)
            case "clear_robot_role":
                return await cls.clear_robot_role(_uid, _seq, thtFlow)
            case r'set_role_transform':
                check_param(query, ["data"])
                return await cls.set_role_transform(_uid, _seq, query["data"])
            case r'get_intention':
                return await cls.get_intention(_uid, _seq, query['data'])
        return {"code":-1, "msg":"不支持method", "uid":_uid, "seq":_seq}

    @staticmethod
    async def insert_stream(_uid, _seq, _data:dict, thtFlow:ThoughtFlow):
        now_time = int(time.time()*1000)
        check_param(_data, ["content"])
        input_txt = _data["content"]
        target = _data["target"] if "target" in _data else ""
        attention = _data["attention"] if "attention" in _data else None
        divide = _data["divide"] if "divide" in _data else None
        input_txt = input_txt.strip()
        if not input_txt:
            resp = {"code":0, "msg":"没有有效输入", "uid":_uid, "seq":_seq}
            return resp
        if input_txt[-1] not in ["？","！","。","~"]:
            input_txt = input_txt + "。"
        task = f"{_uid}_{now_time}"
        msg = {"uid": _uid, "seq": _seq, "content": input_txt, "target": target, "task_id":task}
        if attention:
            try:
                msg["attention"] = int(attention)
            except Exception as e:
                pass
        if divide:
            msg["divide"] = divide
        thtFlow.model = "GM"
        await thtFlow.writeMsgToMain(msg)
        await thtFlow.save_context(msg['task_id'], {f"写入意识流_{target}":msg})
        resp = {"code":0, "msg":"ok", "uid":_uid, "seq":_seq, "task_id":task}
        return resp


    @staticmethod
    async def set_exp_status(_uid, _seq, _data:dict, thtFlow:ThoughtFlow):
        check_param(_data, ["status"])
        satus = _data["status"]
        thtFlow.thtredis.set_expression_status(_uid, satus)
        resp = {"code":0, "msg":"ok", "uid":_uid, "seq":_seq}
        return resp

    @staticmethod
    async def get_exp_status(_uid, _seq, thtFlow:ThoughtFlow):
        status = thtFlow.thtredis.get_expression_status(_uid)
        resp = {"code":0, "msg":"ok", "uid":_uid, "seq":_seq, "data":{"status": status}}
        return resp


    @staticmethod
    async def set_model_attention(_uid, _seq, _data:dict, thtFlow:ThoughtFlow):
        check_param(_data, ["model", "attention"])
        model = _data["model"]
        attention = int(_data["attention"])
        thtFlow.thtredis.set_min_attention(model, attention)
        resp = {"code":0, "msg":"ok", "uid":_uid, "seq":_seq}
        return resp

    @staticmethod
    async def get_model_attention(_uid, _seq, thtFlow:ThoughtFlow):
        models = ["主动求解","发散提问","植物认知"]
        ret_map = {}
        for model in models:
            attention = thtFlow.thtredis.get_min_attention(model)
            ret_map[model] = attention
        resp = {"code":0, "msg":"ok", "uid":_uid, "seq":_seq, "data":ret_map}
        return resp

    @staticmethod
    async def set_public_attention_ratio(_uid, _seq, _data:dict, thtFlow:ThoughtFlow):
        check_param(_data, ["ratio"])
        ratio = round(float(_data["ratio"]), 2)
        thtFlow.thtredis.set_attention_ratio(ratio)
        resp = {"code":0, "msg":"ok", "uid":_uid, "seq":_seq}
        return resp

    @staticmethod
    async def get_public_attention_ratio(_uid, _seq, thtFlow:ThoughtFlow):
        ratio = thtFlow.thtredis.get_attention_ratio()
        resp = {"code":0, "msg":"ok", "uid":_uid, "seq":_seq, "data":{"ratio": ratio}}
        return resp

    @staticmethod
    async def get_last_task(_uid, _seq, thtFlow:ThoughtFlow):
        last_task = thtFlow.thtredis.get_last_task(_uid)
        resp = {"code":0, "msg":"ok", "uid":_uid, "seq":_seq, "data":{"last_task": last_task}}
        return resp

    @staticmethod
    async def delete_last_task(_uid, _seq, thtFlow:ThoughtFlow):
        thtFlow.thtredis.delete_last_task(_uid)
        resp = {"code":0, "msg":"ok", "uid":_uid, "seq":_seq}
        return resp

    @staticmethod
    async def get_work_memory(_uid, _seq, thtFlow:ThoughtFlow):
        work_memory = await thtFlow.get_all_work_memory(_uid)
        resp = {"code":0, "msg":"ok", "uid":_uid, "seq":_seq, "data":{"work_memory": work_memory}}
        return resp

    @staticmethod
    async def get_llm_result(_uid, _seq, _data:dict, thtFlow:ThoughtFlow):
        check_param(_data, ["task_id"])
        task_id = _data["task_id"]
        result = await ContentResult.get_task_llm_result(task_id)
        resp = {"code":0, "msg":"ok", "uid":_uid, "seq":_seq, "data":{"result": result}}
        return resp

    @staticmethod
    async def get_history_dialog(_uid, _seq, thtFlow:ThoughtFlow):
        dialogue_list, history_list = await thtFlow.get_dialogue_history(_uid)
        resp = {"code":0, "msg":"ok", "uid":_uid, "seq":_seq, "data":{"dialogue_list": dialogue_list}}
        return resp

    @staticmethod
    async def get_qa_by_content(_uid, _seq, _data:dict, thtFlow:ThoughtFlow):
        check_param(_data, ["content"])
        content = _data["content"]
        ret = await thtFlow.get_qa(_uid, _uid, [content])
        resp = {"code":0, "msg":"ok", "uid":_uid, "seq":_seq, "data":{"result": ret}}
        return resp

    @staticmethod
    async def get_robot_role(_uid, _seq, thtFlow:ThoughtFlow):
        ret = await UserStatus.get_user_role(_uid)
        resp = {"code":0, "msg":"ok", "uid":_uid, "seq":_seq, "data":ret}
        return resp

    @staticmethod
    async def clear_robot_role(_uid, _seq, thtFlow:ThoughtFlow):
        ret = await UserStatus.clear_robot_role(_uid)
        resp = {"code":0, "msg":"ok", "uid":_uid, "seq":_seq}
        return resp

    @staticmethod
    async def get_memory_by_content(_uid, _seq, _data:dict, thtFlow:ThoughtFlow):
        check_param(_data, ["content"])
        content = _data["content"]
        ret = await thtFlow.memory_get(_uid, content)
        resp = {"code":0, "msg":"ok", "uid":_uid, "seq":_seq, "data":{"result": ret}}
        return resp

    @staticmethod
    async def set_role_transform(_uid: str, _seq: int, _data: dict):

        check_param(_data, ["content"])
        content = _data["content"]
        robot_id = _data.get(r'robot_id', r'agent001')
        now_time = int(time.time() * 1000)
        task = f"{_uid}_{now_time}"

        llm_data = {
            r'role_content': content,
        }

        response = await request_llm(task, llm_data, r'角色转化')

        logger.info(f'role_transform llm {llm_data=} {response=}')

        if not response:
            raise Exception(r'角色转化失败: 大模型无返回')

        format_response = json.loads(response)
        if r'role' not in format_response or r'description' not in format_response:
            raise Exception(f'角色转化失败: 大模型转换结果不符合格式要求, 大模型返回 => {format_response}')

        await UserStatus.set_user_role(_uid, format_response, robot_id)

        resp = {"code":0, "msg":"ok", "uid":_uid, "seq":_seq}
        return resp

    @staticmethod
    async def get_intention(uid: str, seq, data: dict):
        robot_id = data.get(r'robot_id', r'agent001')
        ret = await StorageClient.get_intention(uid, robot_id=robot_id)

        resp = {"code": 0, "msg": "ok", "uid": uid, "seq": seq, "data": {"result": ret}}
        return resp


if __name__ == '__main__':
    async def main():
        input_txt = "我在家。"
        
        if input_txt[-1] not in ["？","！","。","~"]:
            input_txt = input_txt + "。"
        logger.info(f"{input_txt}")
    asyncio.run(main())
    