#-*- encoding: utf-8 -*-

import time
import json
import traceback

import asyncio

from base.agent_public.agent_exception import MissingParamException
from base.agent_public.agent_log import logger
from base.agent_storage_client.agent_storage import StorageClient
from base.large_model_client.agent_llm import request_llm
from base.agent_public.agent_tool import check_param
from base.service import DataSource
from base.thoughts_flow_client.thoughtsFlow import ThoughtFlow

from setting import BaseConfig, PromptConfig


class StrategyService(ThoughtFlow):

    def __init__(self):
        super().__init__()
        self.model = r'策略'
        super().init()

        self._data_source = DataSource()

    async def read_msg(self):

        while True:
            try:

                msgs = self.subStream([r'Main'], r'Strategy', r'Strategy', count=1)

                if not msgs:
                    await asyncio.sleep(0.1)
                    continue

                for msg in msgs:
                    if r'target' not in msg or msg[r'target'] != r'对话管理':
                        continue

                    logger.info(f'StrategyService: {msg=}')

                    intention_record = await self.process_intention_logic(msg)

                    if intention_record:
                        await self.process_strategy_logic(msg, intention_record)

            except MissingParamException as e:
                logger.info(f"消息处理出错,参数错误,缺少{e}")

            except Exception as e:
                logger.error(traceback.format_exc())

    async def process_intention_logic(self, msg: dict):

        try:

            check_param(msg, [ r'uid', r'msg_id'])

            uid = msg[r'uid']
            msg_id = msg['msg_id']

            now_time = int(time.time() * 1000)
            task = msg.get(r'task_id', f'{uid}_{now_time}')

            # 尝试从意识流中读取 robot_id
            robot_id = msg.get(r'robot_id', r'agent001')

            cache_client = self._data_source.get_redis_client()
            async with cache_client.allocate_lock(
                    cache_client.get_safe_key(f'intention_{uid}_{robot_id}'), timeout=60,
                    blocking_timeout=0.1, blocking=True
            ) as locker:

                if not await locker.acquire():
                    logger.info(f'当前{uid=} {robot_id=} 锁已存在, 本轮不执行')
                    # 没有抢到锁, 直接退出
                    raise Exception(f'locker {uid}_{robot_id} 锁已存在, 本轮不执行')

                logger.info(f'当前{uid=} {robot_id=} 锁不存在, 本轮执行')

                dialog_list, history_list = await self.get_dialogue_history(uid)
                intention_record = await self.get_intention(uid, robot_id)

                llm_data = {
                    r'uid': uid,
                    r'dialog_list': dialog_list,
                    r'对话意图分析_response': intention_record,
                }

                llm_resp = await request_llm(task, llm_data, r'对话意图分析')

                logger.info(f'process_intention_logic server {llm_data=} {llm_resp=}')

                if not llm_resp:
                    logger.error(r'process_intention_logic llm resp Null')
                    return

                format_resp = json.loads(llm_resp)

                protocol_data ={
                    r'uid': uid, r'task_id': task, r'表达类型': r'发送协议',
                    r'target': r'表达管理', r'response': {
                        r'type': r'意图切换',
                        r'data': dict(
                            robot_id=robot_id,
                            **format_resp
                        )
                    }
                }

                await self.writeMsgToMain(protocol_data, [msg_id])

                await self.save_intention(uid, robot_id, format_resp)

                return format_resp

        except MissingParamException as e:
            logger.info(f"消息处理出错,参数错误,缺少{e}")

        except Exception as e:
            logger.error(traceback.format_exc())

    async def process_strategy_logic(self, msg: dict, intention_record: dict):

        try:

            check_param(msg, [r'content', r'uid'])
            uid = msg[r'uid']
            input_content = msg[r'content']
            now_time = int(time.time() * 1000)
            task = msg.get(r'task_id', f'{uid}_{now_time}')
            seq = msg.get(r'seq', now_time)

            # 尝试从意识流中读取 robot_id
            robot_id = msg.get(r'robot_id', r'agent001')

            dialogue_list, history_list = await self.get_dialogue_history(uid)

            items = await StorageClient.page_all_dialogue_strategy(robot_id)

            if items is None:
                raise Exception(f'对话策略查询持久化失败 {task=}')
            elif not items:
                logger.info(f'process_strategy_logic 对话策略查询结果为空 {task=}')
                return

            records = {}
            for index, info in enumerate(items, 1):
                _item = info[r'data']
                _item[r'robot_id'] = info[r'robot_id']
                _item[r'id'] = info[r'id']
                _item[r'attention'] = info[r'attention']
                records[str(index)] = _item

            llm_data = {
                r'uid': uid, r'records': records,
                r'dialog_list': dialogue_list,
                r'intention_record': intention_record,
            }

            tigger_resp = await request_llm(task, llm_data, r'策略匹配')

            logger.info(f'process_strategy_logic {task=} tigger {tigger_resp=}')

            # 当未匹配任何策略, 则为空
            if 'NULL' in tigger_resp:
                logger.info(f'process_strategy_logic {task=} not tigger')
                return

            try:
                format_resp = json.loads(tigger_resp)
            except:
                logger.error(r'反序列化错误, 大模型返回结果无法被反序列化')

            tigger_list = format_resp[r'触发选择']
            logger.info(f'process_strategy_logic {msg=} {tigger_list=}')

            datalist = [records[index] for index in tigger_list]

            timestamp = int(time.time()*1000)
            for data in datalist:
                attention = data[r'attention']
                await self.save_work_memory(
                    uid, json.dumps(data), timestamp, attention, 0.1,
                    type=r'对话策略', source=self.model,
                )

        except MissingParamException as e:
            logger.info(f"消息处理出错,参数错误,缺少{e}")
        except Exception as e:
            logger.error(traceback.format_exc())

    async def initliazte(self):

        BaseConfig.open()
        PromptConfig.open()

        await DataSource.initialize()

    async def realease(self):

        await DataSource.release()

        PromptConfig.close()
        BaseConfig.close()


async def main():

    strategy_service = StrategyService()

    await strategy_service.initliazte()

    tasks = [strategy_service.read_msg() for _ in range(BaseConfig.MaxQps)]
    await asyncio.gather(
        *tasks
    )

    await strategy_service.realease()


if __name__ == '__main__':


    asyncio.run(main())
