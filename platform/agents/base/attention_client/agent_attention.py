#-*- encoding: utf-8 -*-
__author__ = 'Jianggb'

import asyncio
import json, traceback
import re
import time
from base.agent_public.agent_log import logger
from base.agent_http.agent_http_client import sendRequestSync
from base.agent_storage_client.agent_content import ContentResult

from setting import BaseConfig


class AttentionClient:

    def __init__(self):
        ""

    @staticmethod
    async def get_attention(msg):
        """{"uid":"123456", "content":"你好", "task_id":"123456_123456", "seq":"111"}"""
        ret = 10
        att_resp = await sendRequestSync(f"{BaseConfig.AttentionUrl}/attention_remark", msg, timeout=30)
        '{"code":0, "msg":"ok", "uid":uid, "seq":seq, "attention":attention_response}'
        try:
            if 0 == att_resp['code']:
                ret = int(att_resp['attention'])
        except Exception as e:
            logger.error(f"get_attention error: {traceback.format_exc()}")
        if "task_id" not in msg:
            msg["task_id"] =  f"{msg['uid']}_{int(time.time()*1000)}"
        await ContentResult.add_main_result(msg["task_id"], {"关注度计算":ret})
        return ret

    @staticmethod
    async def get_remark(msg):
        ret = []
        remark_resp:dict = await sendRequestSync(f"{BaseConfig.AttentionUrl}/divide_remark", msg, timeout=30)
        '{"code":0, "msg":"ok", "uid":uid, "seq":seq, "divide":list(divide_response.values())}'
        try:
            if 0 == remark_resp['code']:
                ret = list(remark_resp["divide"].values())
        except Exception as e:
            logger.error(f"get_remark error: {traceback.format_exc()}")
        if "task_id" not in msg:
            msg["task_id"] =  f"{msg['uid']}_{int(time.time()*1000)}"
        await ContentResult.add_main_result(msg["task_id"], {"问题分类":ret})
        return ret

if __name__ == '__main__':
    logger.info(f"{BaseConfig.AttentionUrl=}")
    
    async def main():
        msg = {"uid":"123456", "content":"你好", "task_id":"123456_123456", "seq":"111"}
        ret = await AttentionClient.get_attention(msg)
        logger.info(f"{ret}")
        ret = await AttentionClient.get_remark(msg)
        logger.info(f"{ret}")
    asyncio.run(main())
