#-*- encoding: utf-8 -*-
__author__ = 'Jianggb'

import json
import time
import traceback, asyncio

from base.agent_public.agent_log import logger
from base.agent_public.agent_redis import AgentRedis
from base.agent_public.agent_tool import get_second_task_key
from base.agent_storage_client.agent_content import ContentResult
from base.agent_storage_client.user_status import UserStatus
from base.thoughts_flow_client.thoughtsFlow import ThoughtFlow
from base.large_model_client.agent_llm import request_llm

from setting import BaseConfig, PromptConfig


class SecondExpression(ThoughtFlow):
    "主动表达"
    def __init__(self):
        super().__init__()
        self.model = "主动表达"

    async def read_msg(self):
        while True:
            try:
                await asyncio.sleep(1)
                tasks = []
                all_online_user = await UserStatus.get_online_user()
                for uid in all_online_user:
                    exp_time = await UserStatus.get_user_exp_time(uid)
                    lasted_exp = exp_time[0]
                    AI_lasted_exp = exp_time[1]
                    AI_second_exp = exp_time[2]
                    if not lasted_exp or not AI_lasted_exp:
                        continue
                    lasted_exp = int(lasted_exp)
                    AI_lasted_exp = int(AI_lasted_exp)
                    if not AI_second_exp:
                        AI_second_exp = 0
                    else:
                        AI_second_exp = int(AI_second_exp)
                    max_exp = max(lasted_exp, AI_lasted_exp, AI_second_exp)
                    now_time = int(time.time())
                    if AI_lasted_exp == max_exp and now_time - AI_lasted_exp > 20:
                        # AI主动表达之后20s内没有用户输入，则AI主动表达
                        logger.info(f"AI主动表达:{uid} {exp_time}")
                        tasks.append(self.expression_service(uid))
                if tasks:
                    results = await asyncio.gather(*tasks)
            except Exception as e:
                logger.error(traceback.format_exc())

    async def expression_service(self, uid):
        msg_id = "0-0"
        task = f"{uid}_{int(time.time()*1000)}"

        qa_work_dict = await self.get_qa_work_memory(uid)
        #{"question_answer_dict":question_answer_dict, "unsolved_question":unsolved_question}
        unsolved_idx = 1
        question_answer_dict = {}
        question_unsolved_dict = {}
        if "question_answer_dict" in qa_work_dict and qa_work_dict["question_answer_dict"]:
            question_answer_dict.update(qa_work_dict["question_answer_dict"])
        if "unsolved_question" in qa_work_dict and qa_work_dict["unsolved_question"]:
            for unsolved_qs in qa_work_dict["unsolved_question"]:
                question_unsolved_dict[str(unsolved_idx)] = unsolved_qs
                unsolved_idx += 1
        
        last_time = await self.get_dialogue_history_last_time(uid)
        logger.info(f"last_time:{uid} {last_time}")
        work_memory = await self.get_work_memory(uid, last_time)
        embedding_memory = await self.get_embedding_work_memory(uid, last_time)
        strategy_memory = await self.get_dialogue_strategy_work_memory(uid)
        
        dialog_list, history_list = await self.get_dialogue_history(uid)

        user_input = r''
        for dialog_map in dialog_list[::-1]:
            if dialog_map['role'] == r'user':
                user_input = dialog_map[r'content']
                break
        
        embedding_map = await self.memory_get(uid, user_input, last_time=last_time)
        await ContentResult.add_main_result(task, {"memory_get": {"请求":user_input, "返回":embedding_map}})
        for tp in embedding_map:
            if tp in embedding_memory:
                for embedding in embedding_map[tp]:
                    if embedding not in embedding_memory[tp]:
                        embedding_memory[tp].append(embedding)
            else:
                embedding_memory[tp] = embedding_map[tp]

        robot_role = await UserStatus.get_user_role(uid)

        if not question_answer_dict and not work_memory and not embedding_memory and not question_unsolved_dict:
            logger.info(f"主动表达没有数据:{uid}")
            msg_data = {"uid":uid, "msg":"主动表达没有数据"}
            await self.writeMsgToMain(msg_data, [msg_id])
            await UserStatus.set_AI_second_exp(uid)
            return
        work_knowledge_list = await self.get_knowledge_work_memory(uid)
        knowledge_list = await self.query_knowledge_by_content(uid, user_input, max_token=500)
        if work_knowledge_list:
            knowledge_list.extend(work_knowledge_list)
        knowledge_list = list(set(knowledge_list))

        llm_data = {'uid':uid, 'dialog_list':dialog_list, "question_answer_dict":question_answer_dict, "work_memory":work_memory,
                    "embedding_memory":embedding_memory, "strategy_memory":strategy_memory, "robot_role":robot_role,
                    "question_unsolved_dict":question_unsolved_dict, "knowledge_list":knowledge_list}
        
        #history_list 加入格式
        formate_history_list = await self.get_output_history(uid)
        exp_status = self.thtredis.get_expression_status(uid)
        response_str = await request_llm(task, llm_data, "主动表达", history_list=formate_history_list, exp_status=exp_status)
        if "无法追加" in response_str:
            logger.info(f"无法追加主动表达数据:{uid}")
            msg_data = {"uid":uid, "msg":"无法追加主动表达数据"}
            await self.writeMsgToMain(msg_data, [msg_id])
            await UserStatus.set_AI_second_exp(uid)
            return
        #输出到意识流
        if response_str:
            try:
                response_map = json.loads(json.dumps(eval(response_str), ensure_ascii=False))
                resp = response_map["response"]
            except Exception as e:
                resp = response_str
            exp_data = {"uid":uid, "task_id":task}
            exp_data["response_map"] = response_str
            exp_data["target"] = "表达管理"
            exp_data["content"] = resp
            exp_data["role"] = "assistant"

            exp_time = await UserStatus.get_user_exp_time(uid)
            lasted_exp = exp_time[0]
            AI_lasted_exp = exp_time[1]
            AI_second_exp = exp_time[2]
            lasted_exp = int(lasted_exp)
            AI_lasted_exp = int(AI_lasted_exp)
            if not AI_second_exp:
                AI_second_exp = 0
            else:
                AI_second_exp = int(AI_second_exp)
            max_exp = max(lasted_exp, AI_lasted_exp, AI_second_exp)
            now_time = int(time.time())
            if AI_lasted_exp == max_exp and now_time - AI_lasted_exp > 20:
                # 大模型返回需要时间，发送之前再次判断
                await self.writeMsgToMain(exp_data, [msg_id])
            else:
                logger.info(f"AI主动表达时间再次判断不用发送:{uid} {exp_time}")
                msg_data = {"uid":uid, "msg":"AI主动表达时间再次判断不用发送"}
                await self.writeMsgToMain(msg_data, [msg_id])

    async def second_task_main(self):
        while True:
            try:
                await asyncio.sleep(0.5)
                all_online_user = await UserStatus.get_online_user()
                for uid in all_online_user:
                    exp_time = await UserStatus.get_user_exp_time(uid)
                    lasted_exp = exp_time[0]
                    AI_lasted_exp = exp_time[1]
                    AI_second_exp = exp_time[2]
                    AI_second_task = exp_time[3]
                    if not lasted_exp or not AI_lasted_exp:
                        continue
                    lasted_exp = int(lasted_exp)
                    AI_lasted_exp = int(AI_lasted_exp)
                    if not AI_second_exp:
                        AI_second_exp = 0
                    else:
                        AI_second_exp = int(AI_second_exp)
                    max_exp = max(lasted_exp, AI_lasted_exp, AI_second_exp)
                    now_time = int(time.time())
                    if AI_lasted_exp == max_exp and now_time - AI_lasted_exp > 20 and \
                        (not AI_second_task or now_time - int(AI_second_task) > 20):
                        # AI主动表达之后20s内没有用户输入，则AI主动表达
                        logger.info(f"AI主动表达任务添加:{uid} {exp_time}")
                        await UserStatus.set_AI_second_task(uid)
                        await add_second_task(uid)
            except Exception as e:
                logger.error(traceback.format_exc())

    async def second_response_expression(self):
        while True:
            uid = await pop_second_task()
            if not uid:
                await asyncio.sleep(0.5)
            else:
                logger.info(f"AI主动表达任务执行:{uid}")
                await self.expression_service(uid)


async def add_second_task(uid):
    "添加主动表达任务"
    second_task_key = get_second_task_key()
    AgentRedis().conn.rpush(second_task_key, uid)


async def pop_second_task():
    "获取主动表达任务"
    second_task_key = get_second_task_key()
    uid = AgentRedis().conn.lpop(second_task_key)
    return uid


def run():
    logger.info(f"SecondExpression进程启动")

    BaseConfig.open()
    PromptConfig.open()

    respserv = SecondExpression()
    lp = asyncio.get_event_loop()
    #tk = [asyncio.ensure_future(respserv.read_msg())]
    tk = [asyncio.ensure_future(respserv.second_task_main())]
    tk.extend([asyncio.ensure_future(respserv.second_response_expression()) for i in range(BaseConfig.MaxQps)])
    try:
        lp.run_until_complete(asyncio.wait(tk))
    except Exception as e:
        pass

    PromptConfig.close()
    BaseConfig.close()

    logger.info(f"SecondExpression进程完成")


if __name__ == '__main__':
    run()
