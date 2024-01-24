#-*- encoding: utf-8 -*-
__author__ = 'Jianggb'

import json
import time
import traceback, asyncio
from base.agent_public.agent_log import logger
from base.agent_public.agent_tool import check_param
from base.thoughts_flow_client.thoughtsFlow import ThoughtFlow
from base.large_model_client.agent_llm import request_llm

from setting import BaseConfig, PromptConfig


class CognitionService(ThoughtFlow):

    def __init__(self):
        super().__init__()
        self.model = "植物认知"

    async def read_msg(self):
        while True:
            try:
            
                msgs = self.subStream(["Main"], "CognitionService", "CognitionService", count=1)
                if not msgs:
                    await asyncio.sleep(0.1)
                    continue
                min_attention = self.get_attention_threshold()
                for msg in msgs:
                    if "attention" not in msg or int(msg["attention"]) < min_attention or \
                        "divide" not in msg or ("11" not in msg["divide"] and "结论" not in msg["divide"]) or \
                        ("source" in msg and msg["source"] == self.model):
                        continue
                    #陈述/结论
                    logger.info(f"CognitionService: {msg}" )
                    await self.cognition_service(msg)
            except Exception as e:
                logger.error(traceback.format_exc())

    async def cognition_service(self, msg):
        check_param(msg, ["uid", "content",])
        uid = msg['uid']
        input_content = msg['content']
        task = msg["task_id"] if "task_id" in msg else f"{uid}_{int(time.time()*1000)}"
        msg["task_id"] = task
        role = msg["role"] if "role" in msg else "assistant"
        attention = int(msg["attention"])
        msg_id = msg['msg_id']
        quest_role = msg["quest_role"] if "quest_role" in msg else "assistant"
        if "source" in msg and msg["source"] == "用户输入":
            quest_role = "user"
        try:
            if quest_role == "assistant":
                logger.info(f"植物性认知 assistant 没有新知识，直接返回")
                #TODO 查询知识
                return
            work_knowledge_list = await self.get_knowledge_work_memory(uid)
            knowledge_list = await self.query_knowledge_by_content(uid, input_content, max_token=500)
            if work_knowledge_list:
                knowledge_list.extend(work_knowledge_list)
            knowledge_list = list(set(knowledge_list))
            dialog_list, history_list = await self.get_dialogue_history(uid)
            llm_data = {'uid':uid, 'input':input_content,"dialog_list":dialog_list, "quest_role":quest_role,
                         "knowledge_list":knowledge_list}
            cognition_content = await request_llm(task, llm_data, "植物性认知", history_list ,role=role)
            if cognition_content:
                cognition_map = json.loads(cognition_content)
                cognition_data = {"uid":uid, "content":input_content, "cognition":cognition_map, 
                                  "time":int(time.time()*1000), "attention":attention, "quest_role":quest_role}
                await self.save_context(task, {"植物性认知_存储":cognition_data})
                """
                {
                    "股权结构分散":{"解释": "CEO缺乏控制力，从而疲于内部关系协调，无法专心进行开拓性事务", 
                                    "什么问题可以帮助进一步证明该结论":"什么表现可以进一步证明该公司股权结构分散？",
                                    "置信度":4}
                }
                """
                cluster_list = []
                qestion_list = []
                for key in cognition_map:
                    cong_detail = cognition_map[key]
                    cluster_list.append((key, cong_detail["解释"], int(cong_detail["置信度"])))
                    for cong_key in cong_detail:
                        if cong_key in ["解释", "置信度"]:
                            continue
                        qestion_list.append(cong_detail[cong_key])
                
                # 保存植物性认知 发送陈述、一般疑问
                cluster_data_list = []
                impress_order_dict = {}
                idx = 1
                for item in cluster_list:
                    confidence = item[2] if len(item) > 2 else 1
                    state_msg = {"uid":uid, "content":item[1], "task_id": task}
                    #await self.writeMsgToMain(state_msg, [msg_id], "印象")
                    cluster_data_list.append({"uid":uid, "summarize":item[0], "describe":item[1], 
                                "attention":int(attention), "timeout":7*24*60*60, "confidence":confidence})
                    impress_order_dict[idx] = f"{item[0]}。{item[1]}"
                    idx += 1

                # 解析不合法的情况下默认7天
                llm_data = {'uid':uid, "impress_order_dict":impress_order_dict}
                timeout_content = await request_llm(task, llm_data, "信息时效性判断")
                unit_map = {"日":1*24*60*60, "月":30*24*60*60}
                if timeout_content:
                    try:
                        timeout_map = json.loads(timeout_content)
                        for idx in timeout_map:
                            timeout_data = timeout_map[idx]
                            timeout_unit = timeout_data["单位"] if "单位" in timeout_data else "日"
                            if timeout_unit not in ["日", "月"]:
                                timeout_unit = "日"
                            timeout_time = int(timeout_data["时效性评估"]) if "时效性评估" in timeout_data else 7
                            idx_int = int(idx) - 1
                            if 0 <= idx_int < len(cluster_data_list):
                                cluster_data_list[idx_int]["timeout"] = timeout_time*unit_map[timeout_unit]
                    except Exception as e:
                        logger.error(traceback.format_exc())

                await self.add_cluster(uid, cluster_data_list)

                task_list = []
                for quesion in qestion_list:
                    task_map = {"task_id":task, "type":"Q", "content":quesion,"status":1, 
                                'parent_id': "None", "attention":int(attention)}
                    task_list.append(task_map)
                nodeids = await self.save_qa(uid, task, task_list)
                #保存问题到redis
                idx = 0
                for quesion in qestion_list:
                    p_nodeid = nodeids[idx] if 0 <= idx < len(nodeids) else "None"
                    idx += 1
                    if p_nodeid == "None":
                        continue
                    qestion_msg = {"uid": uid, "content": quesion, "p_nodeid": p_nodeid, "task_id": task}
                    await self.writeMsgToMain(qestion_msg, [msg_id], msg_divide=12)
                    qa_attention = int(qestion_msg["attention"]) if "attention" in qestion_msg else attention
                    #logger.info(f"写入qa工作记忆: {uid} {p_nodeid} {qa_attention}")
                    await self.save_work_memory(qestion_msg["uid"], p_nodeid, int(time.time()*1000), 
                                qa_attention, 0.1, **{"type":"qa"})

        except Exception as e:
            logger.error(traceback.format_exc())
            await self.save_context(task, {"植物性认知":["处理出错", traceback.format_exc()]})


def run():

    logger.info(f"CognitionService进程启动")

    BaseConfig.open()
    PromptConfig.open()

    cognitionserv = CognitionService()
    lp = asyncio.get_event_loop()
    tk = [asyncio.ensure_future(cognitionserv.read_msg()) for i in range(BaseConfig.MaxQps)]
    try:
        lp.run_until_complete(asyncio.wait(tk))
    except Exception as e:
        pass

    PromptConfig.close()
    BaseConfig.close()

    logger.info(f"CognitionService进程完成")


if __name__ == '__main__':
    run()
