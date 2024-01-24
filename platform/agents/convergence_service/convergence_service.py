#-*- encoding: utf-8 -*-
__author__ = 'Jianggb'

import json
import time
import traceback, asyncio
from base.agent_public.agent_log import logger
from base.thoughts_flow_client.thoughtsFlow import ThoughtFlow
from base.large_model_client.agent_llm import request_llm

from setting import BaseConfig, PromptConfig


class ConvergenceService(ThoughtFlow):
    "收敛问题主动求解"
    def __init__(self):
        super().__init__()
        self.model = "主动求解"

    async def read_msg(self):
        while True:
            last_time = int(time.time()*1000)
            try:
                msgs = self.subStream(["Main"], "ConvergenceService", "ConvergenceService", count=1)
                if not msgs:
                    await asyncio.sleep(0.1)
                    continue
                min_attention = self.get_attention_threshold()
                for msg in msgs:
                    now_time = int(time.time()*1000)
                    if now_time - last_time < 10*1000:
                        msg_id = msg['msg_id']
                        #self.set_attention_threshold(msg_id, "ConvergenceService", "Main")
                    if "attention" not in msg or int(msg["attention"]) < min_attention or "divide" not in msg or\
                        "12"  not in msg["divide"] or ("22"  not in msg["divide"] and "23"  not in msg["divide"]) or\
                        ("source" in msg and msg["source"] == self.model):
                        continue
                    logger.info(f"ConvergenceService: {msg}")
                    last_time = int(time.time()*1000)
                    await self.convergence_service(msg)
            except Exception as e:
                logger.error(traceback.format_exc())

    async def convergence_service(self, msg):
        now_time = int(time.time()*1000)
        uid = msg["uid"]
        msg_id = msg['msg_id']
        #self.set_attention_threshold(msg_id, "ConvergenceService", "Main")
        question_input = msg["content"]
        attention = int(msg["attention"])
        convergence_energy = attention
        if "convergence_energy" in msg:
            convergence_energy = int(msg["convergence_energy"])
        if convergence_energy < 40:
            logger.info(f"能量不够，跳过")
            return
        convergence_energy = convergence_energy*0.7
        try:
            task = msg["task_id"] if "task_id" in msg else f"{uid}_{now_time}"
            msg["task_id"] = task
            work_knowledge_list = await self.get_knowledge_work_memory(uid)
            knowledge_list = await self.query_knowledge_by_content(uid, question_input, max_token=500)
            if work_knowledge_list:
                knowledge_list.extend(work_knowledge_list)
            knowledge_list = list(set(knowledge_list))
            llm_data = {'uid':uid, 'question_input':question_input, "knowledge_list":knowledge_list}
            convergence_response = await request_llm(task, llm_data, "主动求解")
            convergence_map:dict = json.loads(convergence_response)
            
            q_list = list(convergence_map.values())
            p_nodeid = msg["p_nodeid"] if "p_nodeid" in msg else "None"

            qa_resp_map = {}
            if attention < BaseConfig.ConvergenceMinAttention:
                qa_resp_map = await self.get_qa_answer_batch(uid, task, q_list, attention)
            else:
                qa_resp_map = await self.get_qa_and_memory_answer_batch(uid, task, q_list, attention)

            for quesion in qa_resp_map:
                if qa_resp_map[quesion] and "parent_id" in qa_resp_map[quesion]:
                    tmp_p_nodeid = qa_resp_map[quesion]["parent_id"]
                    #logger.info(f"写入qa工作记忆: {tmp_p_nodeid} {attention}")
                    await self.save_work_memory(uid, tmp_p_nodeid, int(time.time()*1000), 
                                attention, 0.1, **{"type":"qa"})

            question_answer_dict = {}
            question_unsolved_dict = {}
            unsolved_idx = 1
            qa_s_task_list = []
            for s_quesion in q_list:
                if s_quesion in qa_resp_map and qa_resp_map[s_quesion]:
                    question_answer_dict[s_quesion] = qa_resp_map[s_quesion]["content"]
                else:
                    question_unsolved_dict[str(unsolved_idx)] = s_quesion
                    unsolved_idx += 1

            task_list = []
            for idx in question_unsolved_dict:
                task_map = {"task_id":task, "type":"Q", "content":question_unsolved_dict[idx],"status":0, 
                            'parent_id': str(p_nodeid), "attention":attention}
                task_list.append(task_map)
            nodeids = await self.save_qa(uid, task, task_list)
            if len(nodeids) == 0:
                logger.info(f"保存QA失败")
                return 
            idx = 0
            for task_map in task_list:
                tmp_nodeid = nodeids[idx]
                idx += 1
                await self.save_work_memory(uid, tmp_nodeid, int(time.time()*1000), 
                                attention, 0.1, **{"type":"qa"})

            llm_data = {'uid':uid, "question_unsolved_dict":question_unsolved_dict}
            llm_data.update(await self.get_task_llm_result(task))
            function_resp = await request_llm(task, llm_data, "问题分类与工具")
            """
            {"提问具体对象":[1,2,3,4],"搜索公共知识库":[5,6]
            }
            """
            function_resp_map = {}
        
            function_resp_map = json.loads(function_resp)
            qa_s_task_list = []
            if "搜索公共知识库" in function_resp_map:
                llm_data = {'uid':uid}
                for idx in function_resp_map["搜索公共知识库"]:
                    question_idx = str(idx)
                    llm_data["question_input"] = question_unsolved_dict[question_idx]
                    llm_data.update(await self.get_task_llm_result(task))
                    expression_resp = await request_llm(task, llm_data, "搜索公共知识库")
                    if expression_resp and int(question_idx) in nodeids:
                        task_map = {"task_id":task, "type":"A", "content":str(expression_resp),
                                    "status":0, 'parent_id': nodeids[int(question_idx)], "attention":attention}
                        qa_s_task_list.append(task_map)
                        question_answer_dict[question_unsolved_dict[question_idx]] = expression_resp
            if qa_s_task_list:
                await self.save_qa(uid, task, qa_s_task_list)
            
            work_memory = await self.get_work_memory(uid)
            embedding_memory = await self.memory_get(uid, question_input, 10, 20)

            if not question_answer_dict and not work_memory and not embedding_memory:
                return
            llm_data = {"uid":uid, "question_answer_dict":question_answer_dict, "question_input":question_input, 
                        "work_memory":work_memory, "embedding_memory":embedding_memory}
            llm_data.update(await self.get_task_llm_result(task))
            function_resp = await request_llm(task, llm_data, "主动求解_提问猜想")
            function_map = json.loads(function_resp)
            if "presumption" in function_map and function_map["presumption"]:
                answer_resp = function_map["presumption"]
                #调用是否满意GPT
                llm_data = {"uid":uid, "question_input":question_input, "presumption":answer_resp}
                llm_data.update(await self.get_task_llm_result(task))
                feedback_resp = await request_llm(task, llm_data, "主动求解_反馈")
                if feedback_resp:
                    feedback_map = json.loads(feedback_resp)
                    score_sum = 0
                    for tmp_score in feedback_map.values():
                        score_sum += int(tmp_score)
                    if 80 > score_sum:
                        # 不满意再次分解问题
                        llm_data = {"uid":uid, "question_answer_dict":question_answer_dict, "question_input":question_input, 
                                "work_memory":work_memory, "embedding_memory":embedding_memory, "presumption":answer_resp,
                                "question_unsolved_list":list(question_unsolved_dict.values())}
                        llm_data.update(await self.get_task_llm_result(task))
                        second_function_resp = await request_llm(task, llm_data, "主动求解_再次求解")
                        if second_function_resp:
                            second_function_map:dict = json.loads(second_function_resp)
                            second_question = sorted(second_function_map.items(), key=lambda x:x[0])[0][1]
                            logger.info(f" 再次求解问题：{second_question}")
                            second_task_list = [{"task_id":task, "type":"Q", "content":second_question,"status":0, 
                                        'parent_id': str(p_nodeid), "attention": int(msg["attention"])}]
                            second_nodeids = await self.save_qa(uid, task, second_task_list)
                            second_p_nodeid = "None"
                            if second_nodeids:
                                second_p_nodeid = second_nodeids[0]
                                tmp_msg = msg.copy()
                                tmp_msg["content"] = second_question
                                tmp_msg["convergence_energy"] = convergence_energy
                                tmp_msg["p_nodeid"] = second_p_nodeid
                                await self.save_work_memory(uid, second_p_nodeid, int(time.time()*1000), 
                                            attention, 0.1, **{"type":"qa"})
                                second_answer = await self.convergence_service(tmp_msg)
                task_map = {"task_id":task, "type":"A_主动求解回答", "content":str(answer_resp),
                                    "status":0, 'parent_id': str(p_nodeid), "attention":attention}
                await self.save_qa(uid, task, [task_map])
                #发送思绪流结论
                msg_data = {"uid":uid, "content":answer_resp, "task_id": task}
                await self.writeMsgToMain(msg_data, [msg_id], ["结论", 11, 22])
                return answer_resp
        except Exception as e:
            logger.info(f"主动求解错误：{traceback.format_exc()}")
            await self.save_context(task, {"主动求解_错误":traceback.format_exc()})




def run():
    logger.info(f"ConvergenceService进程启动")

    BaseConfig.open()
    PromptConfig.open()

    converserv = ConvergenceService()
    lp = asyncio.get_event_loop()
    tk = [asyncio.ensure_future(converserv.read_msg()) for i in range(BaseConfig.MaxQps)]
    try:
        lp.run_until_complete(asyncio.wait(tk))
    except Exception as e:
        pass

    PromptConfig.close()
    BaseConfig.close()

    logger.info(f"ConvergenceService进程完成")


if __name__ == '__main__':
    run()


