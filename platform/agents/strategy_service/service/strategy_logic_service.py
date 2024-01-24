# -*- coding: utf-8 -*-
import json

from base.agent_storage_client.agent_storage import StorageClient
from base.large_model_client.agent_llm import request_llm
from hagworm.extend.asyncio.net import HTTPJsonClientPool

from base.service import ServiceBase
from base.agent_public.agent_log import logger


class StrategyLogicService(ServiceBase):

    def __init__(self):

        super().__init__()

        self._http_rag_client = HTTPJsonClientPool()

    async def strategy_add_for_user(self, input_txt: str, task: str, robot_id: str, attention: int):

        llm_data = {
            r'strategy_directive': input_txt,
        }

        response = await request_llm(task, llm_data, r'策略转化')

        logger.info(f'strategy_add_for_user {llm_data=} {response=}')

        if not response:
            raise Exception(r'策略转化失败: 大模型无返回')

        format_response = json.loads(response)

        if r'用户状态' not in format_response or r'意图' not in format_response:
            raise Exception(f'策略转换失败: 大模型转换结果不符合格式要求, 大模型返回 => {format_response}')

        format_response[r'策略表述'] = input_txt

        storage_resp = await StorageClient.add_dialogue_strategy(robot_id, format_response, attention)

        return storage_resp
