#-*- encoding: utf-8 -*-
__author__ = 'Jianggb'

import json
import time
import traceback, asyncio
from base.agent_public.agent_exception import MissingParamException
from base.agent_public.agent_log import logger
from base.thoughts_flow_client.thoughtsFlow import ThoughtFlow
from base.large_model_client.agent_llm import request_llm

from setting import BaseConfig, PromptConfig


class DivergenceService(ThoughtFlow):
    "发散提问"
    def __init__(self):
        super().__init__()
        self.model = "发散提问"

    async def read_msg(self):
        while True:
            try:
            
                msgs = self.subStream(["Main"], "DivergenceService", "DivergenceService", count=1)
                if not msgs:
                    await asyncio.sleep(0.1)
                    continue
                min_attention = self.get_attention_threshold()
                for msg in msgs:
                    if "attention" not in msg or int(msg["attention"]) < min_attention or \
                       "divide" not in msg or ("11" not in msg["divide"] and "结论" not in msg["divide"]) or\
                        ("source" in msg and msg["source"] == self.model):
                        continue
                    logger.info(f"DivergenceService: {msg}" )
                    await self.divergence_service(msg)
            except MissingParamException as e:
                logger.info(f"消息处理出错,参数错误,缺少{e}")
            except Exception as e:
                logger.error(traceback.format_exc())

    async def divergence_service(self, msg):
        uid = msg["uid"]
        msg_id = msg['msg_id']
        task = msg["task_id"] if "task_id" in msg else f"{uid}_{int(time.time()*1000)}"
        msg["task_id"] = task
        divergence_input = msg["content"]
        divergence_type = "用户陈述"
        if "source" in msg and msg["source"] != "用户输入":
            divergence_type = "猜想"
        if divergence_type == "猜想":
            logger.info(f"发散提问 猜想 没有新知识，直接返回")
            #TODO 查询知识
            return
        dialog_list, history_list = await self.get_dialogue_history(uid)
        llm_data = {'uid':uid, 'dialog_list':dialog_list, "divergence_type":divergence_type, "divergence_input":divergence_input}
        divergence_response = await request_llm(task, llm_data, "发散提问")
        #输出问题到意识流
        divergence_map = json.loads(divergence_response)
        if "content" in divergence_map and divergence_map["content"]:
            question_input = divergence_map["content"]
            task_list = [{"task_id":task, "type":"Q", "content":question_input,"status":0, 
                        'parent_id': "None", "attention": int(msg["attention"])}]
            nodeids = await self.save_qa(uid, task, task_list)
            p_nodeid = "None"
            if nodeids:
                p_nodeid = nodeids[0]
                msg_data = {"uid": uid, "content": question_input, "p_nodeid": p_nodeid, "task_id": task}
                await self.writeMsgToMain(msg_data, [msg_id], msg_divide=12)
                #todo 判断问题是否有答案
                #保存问题到redis
                if p_nodeid:
                    attention = int(msg_data["attention"]) if "attention" in msg_data else 100
                    #logger.info(f"写入qa工作记忆: {p_nodeid} {attention}")
                    await self.save_work_memory(msg_data["uid"], p_nodeid, int(time.time()*1000), 
                                attention, 0.1, **{"type":"qa"})


def run():

    logger.info(f"DivergenceService进程启动")

    BaseConfig.open()
    PromptConfig.open()

    diverserv = DivergenceService()
    lp = asyncio.get_event_loop()
    tk = [asyncio.ensure_future(diverserv.read_msg()) for i in range(BaseConfig.MaxQps)]
    try:
        lp.run_until_complete(asyncio.wait(tk))
    except Exception as e:
        pass

    PromptConfig.close()
    BaseConfig.close()

    logger.info(f"DivergenceService进程完成")



if __name__ == '__main__':
    run()
