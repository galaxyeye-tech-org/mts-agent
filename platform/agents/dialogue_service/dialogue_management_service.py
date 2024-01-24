#-*- encoding: utf-8 -*-
__author__ = 'Jianggb'

import json
import traceback, asyncio

from base.agent_public.agent_exception import MissingParamException
from base.agent_public.agent_log import logger
from base.agent_public.agent_tool import check_param
from base.thoughts_flow_client.thoughtsFlow import ThoughtFlow
from base.large_model_client.agent_llm import request_llm

from setting import BaseConfig, PromptConfig


class DialogueManagement(ThoughtFlow):

    def __init__(self):
        super().__init__()
        self.model = "对话管理"
        super().init()

    async def read_msg(self):
        while True:
            try:
            
                msgs = self.subStream(["Main"], "DialogueManagement", "DialogueManagement", count=1)
                if not msgs:
                    await asyncio.sleep(0.1)
                    continue
                for msg in msgs:
                    if "target" not in msg or msg["target"] != self.model:
                        continue
                    # min_attention = self.get_attention_threshold()
                    # if "attention" in msg and msg["attention"] and int(msg["attention"]) < min_attention:
                    #     logger.info(f"{msg} 关注度小于最小关注度{min_attention} ，忽略")
                    #     continue
                    logger.info(f"DialogueManagement: {msg}")
                    await self.dialogue_management_service(msg)

            except MissingParamException as e:
                logger.info(f"消息处理出错,参数错误,缺少{e}")
            except Exception as e:
                logger.error(traceback.format_exc())


    async def dialogue_management_service(self, msg:dict):
        check_param(msg, ["uid", "content", "task_id", "msg_id"])
        input_content = msg["content"]
        task = msg["task_id"]
        uid = msg['uid']
        msg_id = msg['msg_id']
        try:
            if "content" in msg and "attention" not in msg:
                msg["attention"] = await self.attention_remark(msg)
            if "content" in msg and "divide" not in msg:
                 msg["divide"] = await self.divide_remark(msg)
            
            await self.save_context(task, {"对话管理":["开始处理", msg]})
            
            dialog_list, history_list = await self.get_dialogue_history(uid)

            q_map = await self.get_qa(uid, task, [input_content])
            question_answer_dict = {}
            question_unsolved_dict = {}
            unsolved_idx = 1
            embedding = ""
            question_map = {}
            unsolved_question = set()
            for qa_question in q_map:
                a_map:dict = q_map[qa_question]
                for task_item in a_map.values():
                    if "parentid" in task_item and str(task_item['parentid']) == str(None):
                        embedding += task_item['Q']
                    if task_item['A']:
                        question_answer_dict[task_item['Q']] = task_item['A']
                    elif task_item['Q'] not in unsolved_question:
                        question_unsolved_dict[str(unsolved_idx)] = task_item['Q']
                        unsolved_question.add(task_item['Q'])
                        question_map[str(unsolved_idx)] = (task_item['taskid'], task_item['nodeid'])
                        unsolved_idx += 1

            qa_work_dict = await self.get_qa_work_memory(uid)
            #{"question_answer_dict":question_answer_dict, "unsolved_question":unsolved_question}
            if "question_answer_dict" in qa_work_dict and qa_work_dict["question_answer_dict"]:
                question_answer_dict.update(qa_work_dict["question_answer_dict"])
            if "unsolved_question" in qa_work_dict and qa_work_dict["unsolved_question"]:
                unsolved_question.update(qa_work_dict["unsolved_question"])
                for unsolved_qs in qa_work_dict["unsolved_question"]:
                    question_unsolved_dict[str(unsolved_idx)] = unsolved_qs
                    unsolved_idx += 1

            p_task_map = {}
            if question_unsolved_dict: #匹配到问题
                llm_data = {'uid':uid, "question_answer_dict":question_answer_dict, 'input':msg['content'], 
                            "dialog_list":dialog_list, "question_unsolved_dict":question_unsolved_dict}

                answer_response = await request_llm(task, llm_data, "回答判断", history_list)
                """
                [{"question_id":"1", "response": "你昨晚一点多才睡，睡得不好。", "status": 1}, 
                {"question_id":"2", "response": "没有提到。", "status": 0}, 
                {"question_id":"3", "response": "没有提到。", "status": 0}, 
                {"question_id":"4", "response": "你今天很困，精神可能不太好。", "status": 1}]
                """
                answer_response_json = []
                try:
                    answer_response_json = json.loads(answer_response)
                    if answer_response_json:
                        task_list = []
                        for item in answer_response_json:
                            question_idx = str(item['question_id'])
                            question_response = item['response']
                            if item['status'] == 1 and question_idx in question_unsolved_dict and question_idx in question_map:
                                task_map = {"task_id":question_map[question_idx][0], "type":"A_用户回答",
                                            "content":question_response, "status":0, "parent_id":question_map[question_idx][1],
                                            "attention":int(msg["attention"])}
                                task_list.append(task_map)
                        nodeids = await self.save_qa(uid, task, task_list)
                        # idx = 0
                        # if nodeids:
                        #     for task_map in task_list:
                        #         p_task_map[task_map["task_id"]] = nodeids[idx]
                        #         idx += 1

                except Exception as e:
                    logger.error(traceback.format_exc())
            
            # task_content_map = {}
            # for p_task in p_task_map:
            #     task_content= await self.get_context(p_task)
            #     if task_content:
            #         task_content_map[p_task] = p_task_map[p_task]
            # p_task = task if not last_task else last_task
            # p_nodeid = None if not last_nodeid else last_nodeid
            # old_task_llm_response = None
            # if task_content_map: #匹配到老任务
            #     p_task = self.select_task(task_content_map, last_task)
            #     logger.info(f"选择任务:{p_task} {task_content_map}")
            #     p_nodeid = p_task_map[p_task]
            #     old_task_llm_response = await self.get_task_llm_result(p_task)

            # if not old_task_llm_response and last_task:
            #     old_task_llm_response = await self.get_task_llm_result(last_task)

            # llm_data = {'uid':uid, "dialog_list":dialog_list}
            # if old_task_llm_response:
            #     llm_data.update(old_task_llm_response)
            
            # old_task_response = None
            # if old_task_llm_response and "任务分析_response" in old_task_llm_response:
            #     old_task_response = old_task_llm_response["任务分析_response"]
            # task_resp = await request_llm(task, llm_data, "任务分析", history_list)
            # task_resp_dict = {}
            # role = "assistant"
            # try:
            #     if old_task_response:
            #         old_task_response_dict = json.loads(old_task_response)
            #         if old_task_response_dict and "prompt" in old_task_response_dict and "role" in old_task_response_dict["prompt"]:
            #             role = old_task_response_dict["prompt"]["role"]
            #     task_resp_dict = json.loads(task_resp)
            #     if "task_change" in task_resp_dict and task_resp_dict["task_change"] == 1:
            #         role = task_resp_dict["prompt"]["role"]
            #         p_task = task
            #         p_nodeid = None
            #         logger.info(f"任务发生变化")
            #         protocol_data = {"uid":uid, "task_id":p_task}
            #         protocol_data["表达类型"] = "发送协议"
            #         protocol_data["target"] = "表达管理"
            #         protocol_data["task_id"] = p_task
            #         protocol_data["response"] = {"type":"任务切换","data":{"task":task_resp_dict}}
            #         await self.writeMsgToMain(protocol_data, [msg_id])
            #         msg["task_change"] = "1"
            #     else:
            #         ContentResult.add_task_llm_result(p_task, "任务分析", task_resp)
            # except Exception as e:
            #     logger.error(traceback.format_exc())
                
            # msg["target"] = "问题分解"
            # msg["task_id"] = p_task
            # if p_nodeid:
            #     msg["node_id"] = p_nodeid
            # msg["embbeding"] = embedding
            # msg["role"] = role
            # await self.writeMsgToMain(msg, [msg_id])
            # self.thtredis.set_last_task(uid, p_task, p_nodeid)
            # await self.save_context(task, {"对话管理_发送问题分解":msg})
        except Exception as e:
            logger.error(traceback.format_exc())
            await self.save_context(task, {"对话管理":["处理出错", traceback.format_exc()]})

        
    def select_task(self, task_content_map, last_task):
        ret = None
        if last_task and last_task in task_content_map:
            ret = last_task
        else:
            for task in task_content_map:
                ret = task
        return ret


def run():
    logger.info(f"DialogueManagement进程启动")
    BaseConfig.open()
    PromptConfig.open()

    dialogue = DialogueManagement()
    lp = asyncio.get_event_loop()
    tk = [asyncio.ensure_future(dialogue.read_msg()) for i in range(BaseConfig.MaxQps)]
    try:
        lp.run_until_complete(asyncio.wait(tk))
    except Exception as e:
        pass

    PromptConfig.close()
    BaseConfig.close()

    logger.info(f"DialogueManagement进程完成")


if __name__ == '__main__':
    run()
