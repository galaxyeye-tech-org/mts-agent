#-*- encoding: utf-8 -*-
__author__ = 'Jianggb'

"""对话接入和表达发出"""
import json

import time, asyncio
from base.agent_public.agent_log import logger
from base.agent_storage_client.user_status import UserStatus
from base.large_model_client.agent_llm import request_llm
from base.thoughts_flow_client.thoughtsFlow import ThoughtFlow
from base.agent_public.agent_tool import check_param
from base.service import ServiceBase, DialogElasticsearchQueueBuffer

from setting import BaseConfig


class DialogueService(ServiceBase):
    """
    如果该Service需要接收意识流消息, 需要在启动时
    await DataSource.initialize()
    释放资源时
    await DataSource.release()

    具体参考 StrategyService 此时不能再继承自ServiceBase
    """

    def __init__(self):

        super().__init__()

        self._dialog_queue_buffer = DialogElasticsearchQueueBuffer(
            BaseConfig.DialogActionQueueBufferMaxSize,
            BaseConfig.DialogActionQueueBufferTimeout,
            BaseConfig.DialogActionQueueBufferTaskLimit
        )

    @property
    def dialog_queue_buffer(self):

        return self._dialog_queue_buffer

    async def parse_request(self, thtFlow:ThoughtFlow, query:dict):
        ""
        check_param(query, ["uid", "method", "seq"])
        _uid = query["uid"]
        now_time = int(time.time()*1000)
        _seq = query["seq"] if "seq" in query else now_time
        _method = query["method"]
        match _method:
            case "input":
                check_param(query, ["data"])
                return await self.input_request(_uid, _seq, query["data"], thtFlow)
            case "get_task_context":
                check_param(query, ["data"])
                return await self.get_task_context(_uid, _seq, query["data"], thtFlow)
            case "clear_dialogue_history":
                return await self.clear_dialogue_history(_uid, _seq, thtFlow)
            case "clear_context":
                return await self.clear_context(_uid, _seq, query["data"], thtFlow)
        return {"code":-1, "msg":"不支持method", "uid":_uid, "seq":_seq}

    async def input_request(self, _uid, _seq, _data:dict, thtFlow:ThoughtFlow):
        now_time = int(time.time()*1000)
        input_txt = _data["content"] if "content" in _data else ""
        input_txt = input_txt.strip()
        if not input_txt:
            resp = {"code":0, "msg":"没有有效输入", "uid":_uid, "seq":_seq}
            return resp
        if input_txt[-1] not in ["？","！","。","~"]:
            input_txt = input_txt + "。"
        task = f"{_uid}_{now_time}"
        await UserStatus.set_user_lasted_exp(_uid)
        dialog_list, history_list = await thtFlow.get_dialogue_history(_uid)
        ori_dialog_list = []
        for dialog in dialog_list:
            role = dialog["role"]
            if dialog["role"] != "user":
                role = "assistant"
            ori_dialog = {"content": dialog["content"], "role": role}
            ori_dialog_list.append(ori_dialog)

        uid, content, resp_id, idx, tp, role, response = await thtFlow.save_dialogue_history(_uid, input_txt)
        await self._dialog_queue_buffer.append({
            r'_op_type': r'create',
            r'_index': BaseConfig.DialogElasticsearchIndex,
            r'uid': uid,
            r'content': content,
            r'resp_id': resp_id,
            r'idx': idx,
            r'tp': tp,
            r'role': role,
            r'response_map': response,
            r'@timestamp': int(time.time() * 1000),
        })

        msg = {"uid": _uid, "seq": _seq, "content": input_txt, "target": "响应服务", "task_id":task, "source":"用户输入"}
        await thtFlow.writeMsgToMain(msg)
        
        llm_data = {'uid':_uid, "ori_dialog_list":ori_dialog_list, 'input':input_txt}
        fix_input = await request_llm(task, llm_data, "对话补全")
        if "null" in fix_input:
            fix_input = input_txt
        else:
            fix_map = json.loads(fix_input)
            fix_input = fix_map["content"]
        msg = {"uid": _uid, "seq": _seq, "content": fix_input, "target": "对话管理", "task_id":task, "source":"用户输入"}
        thtFlow.model = "对话"
        await thtFlow.writeMsgToMain(msg)
        await thtFlow.save_context(msg['task_id'], {"写入对话管理":msg})
        resp = {"code":0, "msg":"ok", "uid":_uid, "seq":_seq, "task_id":task}
        return resp

    @staticmethod
    async def get_task_context(_uid, _seq, _data:dict, thtFlow:ThoughtFlow):
        task_id = _data["task_id"]
        task_context = await thtFlow.get_context(task_id)
        sorted_dict_by_value = {k: v for k, v in sorted(task_context.items(), key=lambda item: item[0], reverse=True)}
        resp = {"code":0, "msg":"ok", "uid":_uid, "seq":_seq, "task_context":sorted_dict_by_value}
        return resp

    @staticmethod
    async def clear_context(_uid, _seq, _data:dict, thtFlow:ThoughtFlow):
        task_id = _data["task_id"]
        await thtFlow.clear_context(task_id)
        resp = {"code":0, "msg":"ok", "uid":_uid, "seq":_seq}
        return resp

    @staticmethod
    async def clear_dialogue_history(_uid, _seq, thtFlow:ThoughtFlow):
        await thtFlow.clear_dialogue_history(_uid)
        resp = {"code":0, "msg":"ok", "uid":_uid, "seq":_seq}
        return resp


if __name__ == '__main__':
    async def main():
        input_txt = "我在家。"
        
        if input_txt[-1] not in ["？","！","。","~"]:
            input_txt = input_txt + "。"
        logger.info(f"{input_txt}")
    asyncio.run(main())
    