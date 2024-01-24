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


class SummarizeService(ThoughtFlow):
    "印象冲击总结"
    def __init__(self):
        super().__init__()
        self.model = "印象冲击总结"

    async def read_msg(self):
        while True:
            try:
            
                msgs = self.subStream(["Main"], "SummarizeService", "SummarizeService", count=1)
                if not msgs:
                    await asyncio.sleep(0.1)
                    continue
                for msg in msgs:
                    if "target" not in msg or msg["target"] != self.model:
                        continue
                    logger.info(f"SummarizeService: {msg}" )
                    await self.summarize_service(msg)
            except MissingParamException as e:
                logger.info(f"消息处理出错,参数错误,缺少{e}")
            except Exception as e:
                logger.error(f"{traceback.format_exc()}")

    async def summarize_service(self, msg):
        if "content_list" in msg and "cluster_id" in msg:
            await self.summarize_add(msg)
        elif "cluster_ids" in msg:
            await self.summarize_del(msg)
        

    async def summarize_add(self, msg):
        "添加印象冲击总结"
        uid = msg["uid"]
        content_list = msg["content_list"]
        msg_id = msg['msg_id']
        impress_dict = {item["summarize"]:item["describe"] for item in content_list }
        cluster_id = msg["cluster_id"] if "cluster_id" in msg and msg["cluster_id"] else None

        llm_data = {'uid':uid, 'impress_dict':impress_dict}
        summarize_response = await request_llm(uid, llm_data, "印象冲击总结")
        summarize_map:dict = json.loads(summarize_response)
        summarize_list = [f"{k}。{v}" for k, v in summarize_map.items()]
        attention_param = {"uid":uid, "content":str(summarize_list)}
        attention_param["quest_role"] = "assistant"
        attention_ret = await self.attention_remark(attention_param)
        #写入记忆
        for summarize in summarize_list:
            #await self.memory_add(uid, summarize, attention_ret, source=self.model, type="结论")
            msg_data = {"uid": uid, "content": summarize, "attention":attention_ret}
            if cluster_id:
                msg_data["cluster_id"] = cluster_id
            await self.writeMsgToMain(msg_data, [msg_id], ["猜想",11,22])

    async def summarize_del(self, msg):
        "删除印象冲击总结"
        cluster_ids = msg["cluster_ids"]
        uid = msg["uid"]
        memory_list = await self.memory_get_page(uid, "猜想")
        del_memory_ids = []
        for memory in memory_list:
            if "other_data" in memory and memory["other_data"] and "cluster_id" in memory["other_data"] \
                and memory["other_data"]["cluster_id"] in cluster_ids:
                #del_memory_ids.append(memory["_id"])
                await self.memory_delete(uid, memory["_id"])


def run():

    logger.info(f"SummarizeService进程启动")

    BaseConfig.open()
    PromptConfig.open()

    summarizeserv = SummarizeService()
    lp = asyncio.get_event_loop()
    tk = [asyncio.ensure_future(summarizeserv.read_msg()) for i in range(BaseConfig.MaxQps)]
    try:
        lp.run_until_complete(asyncio.wait(tk))
    except Exception as e:
        pass

    PromptConfig.close()
    BaseConfig.close()

    logger.info(f"SummarizeService进程完成")


if __name__ == '__main__':
    run()
