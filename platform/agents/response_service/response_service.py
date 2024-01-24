#-*- encoding: utf-8 -*-
__author__ = 'Jianggb'

import json
import time
import traceback, asyncio
from base.agent_public.agent_log import logger
from base.agent_storage_client.agent_content import ContentResult
from base.agent_storage_client.user_status import UserStatus
from base.thoughts_flow_client.thoughtsFlow import ThoughtFlow
from base.large_model_client.agent_llm import request_llm

from setting import BaseConfig, PromptConfig


class ResponseService(ThoughtFlow):
    "响应服务"
    def __init__(self):
        super().__init__()
        self.model = "响应服务"

    async def read_msg(self):
        while True:
            try:
                msgs = self.subStream(["Main"], "ResponseService", "ResponseService", count=1)
                if not msgs:
                    await asyncio.sleep(0.1)
                    continue
                for msg in msgs:
                    if "target" not in msg or msg["target"] != self.model:
                        continue
                    logger.info(f"ResponseService: {msg}" )
                    await self.response_service(msg)
            except Exception as e:
                logger.error(traceback.format_exc())

    async def response_service(self, msg):
        uid = msg["uid"]
        msg_id = msg['msg_id']
        task = msg["task_id"] if "task_id" in msg else f"{uid}_{int(time.time()*1000)}"
        msg["task_id"] = task
        user_input = msg["content"]

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
        logger.info(f"{last_time=}")
        work_memory:dict[str, list] = await self.get_work_memory(uid, last_time)
        embedding_memory:dict[str, list] = await self.get_embedding_work_memory(uid, last_time)
        strategy_memory = await self.get_dialogue_strategy_work_memory(uid)
        
        embedding_map = await self.memory_get(uid, user_input, last_time=last_time)
        await ContentResult.add_main_result(task, {"memory_get": {"请求":user_input, "返回":embedding_map}})
        for tp in embedding_map:
            if tp in embedding_memory:
                for embedding in embedding_map[tp]:
                    if embedding not in embedding_memory[tp]:
                        embedding_memory[tp].append(embedding)
            else:
                embedding_memory[tp] = embedding_map[tp]

        if "用户陈述" in embedding_memory and "用户陈述" in work_memory:
            inter_embedding = set(embedding_memory["用户陈述"]) & set(work_memory["用户陈述"])
            for embedding in inter_embedding:
                embedding_memory["用户陈述"].remove(embedding)
        
        robot_role = await UserStatus.get_user_role(uid)
        dialog_list, history_list = await self.get_dialogue_history(uid)
        work_knowledge_list = await self.get_knowledge_work_memory(uid)
        knowledge_list = await self.query_knowledge_by_content(uid, user_input, max_token=500)
        if work_knowledge_list:
            knowledge_list.extend(work_knowledge_list)
        knowledge_list = list(set(knowledge_list))

        llm_data = {'uid':uid, 'dialog_list':dialog_list, "question_answer_dict":question_answer_dict, "work_memory":work_memory,
                    "embedding_memory":embedding_memory, "strategy_memory":strategy_memory,"input":user_input, 
                    "question_unsolved_dict":question_unsolved_dict, "robot_role":robot_role, "knowledge_list":knowledge_list}
        
        #history_list 加入格式
        formate_history_list = await self.get_output_history(uid)
        exp_status = self.thtredis.get_expression_status(uid)
        
        response_str = await request_llm(task, llm_data, "响应", history_list=formate_history_list, exp_status=exp_status)
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
            await self.writeMsgToMain(exp_data, [msg_id])


def run():

    logger.info(f"ResponseService进程启动")

    BaseConfig.open()
    PromptConfig.open()

    respserv = ResponseService()
    lp = asyncio.get_event_loop()
    tk = [asyncio.ensure_future(respserv.read_msg()) for i in range(BaseConfig.MaxQps)]
    try:
        lp.run_until_complete(asyncio.wait(tk))
    except Exception as e:
        pass

    PromptConfig.close()
    BaseConfig.close()

    logger.info(f"ResponseService进程完成")


if __name__ == '__main__':
    run()
