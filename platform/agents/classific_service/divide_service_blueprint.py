#-*- encoding: utf-8 -*-
__author__ = 'Jianggb'
import json
import re
import traceback, time, asyncio
from sanic import Blueprint
from sanic.response import json as sjson
from base.agent_public.agent_exception import MissingParamException
from base.agent_public.agent_log import logger
from base.large_model_client.agent_llm import request_llm
from base.agent_public.agent_tool import check_param
from base.thoughts_flow_client.thoughtsFlow import ThoughtFlow


divide_bp = Blueprint('mts_agent_divide_v1', url_prefix='/mts_agent/divide/v1')

thtFlow = ThoughtFlow()

@divide_bp.route('/divide_remark', methods=['POST'])
async def divide_remark(request):
    """
    "句式判断":{
        "11":"陈述",
        "12":"疑问",
        "13":"祈使"
    },
    "关联对象":{
        "20":"都无关",
        "21":"与assistant相关",
        "22":"与user相关",
        "23":"都相关"
    },
    "标签":{
        "30":"没有符合要求的标签",
        "31":"描述客观世界的知识",
        "32":"描述个人的感受、观念"
    }
    """
    resp = {"code":-1, "msg":""}
    try:
        query = request.json
        logger.info(f"divide_remark: {query}")
        check_param(query, ["uid", "content"])
        uid = query["uid"]
        seq = query["seq"] if "seq" in query else int(time.time()*1000)
        input_txt = query["content"]
        task = query["task_id"] if "task_id" in query else uid
        dialog_list, history_list = await thtFlow.get_dialogue_history(uid)
        ori_dialog_list = []
        quest_role = query["quest_role"] if "quest_role" in query else "assistant"
        for dialog in dialog_list:
            role = dialog["role"]
            if dialog["role"] != "user":
                role = "assistant"
            ori_dialog = {"content": dialog["content"], "role": role}
            ori_dialog_list.append(ori_dialog)
        llm_data = {'uid':uid, 'input':input_txt, "dialog_list":dialog_list, "history_list":history_list, 
                    "ori_dialog_list":ori_dialog_list, "quest_role":quest_role}

        divide_response = await request_llm(task, llm_data, "分流")
        divide_map = json.loads(divide_response)
        resp = {"code":0, "msg":"ok", "uid":uid, "seq":seq, "divide":divide_map}
    except MissingParamException as e:
        resp = {"code": 9446, "msg": f"参数错误,缺少{e}"}
    except Exception as e:
        resp = {"code":9444, "msg":f"{traceback.format_exc()}"}
    return sjson(resp)


@divide_bp.route('/attention_remark', methods=['POST'])
async def attention_remark(request):
    resp = {"code":-1, "msg":""}
    try:
        query = request.json
        logger.info(f"attention_remark: {query}")
        check_param(query, ["uid", "content"])
        uid = query["uid"]
        seq = query["seq"] if "seq" in query else int(time.time()*1000)
        input_txt = query["content"]
        task = query["task_id"] if "task_id" in query else uid
        dialog_list, history_list = await thtFlow.get_dialogue_history(uid)
        ori_dialog_list = []
        quest_role = query["quest_role"] if "quest_role" in query else None
        for dialog in dialog_list:
            role = dialog["role"]
            if dialog["role"] != "user":
                if not quest_role:
                    quest_role = dialog["role"]
                role = "assistant"
            ori_dialog = {"content": dialog["content"], "role": role}
            ori_dialog_list.append(ori_dialog)
        llm_data = {'uid':uid, 'input':input_txt, "dialog_list":dialog_list, "history_list":history_list, 
                    "ori_dialog_list":ori_dialog_list, "quest_role":quest_role}
        attention_response = await request_llm(task, llm_data, "关注度")
        numbers_in_string = re.findall(r'(\d+)', attention_response)
        attention = 10
        if numbers_in_string:
            attention = int(numbers_in_string[0])
        if attention > 100:
            attention = 100
        resp = {"code":0, "msg":"ok", "uid":uid, "seq":seq, "attention":attention}
    except MissingParamException as e:
        resp = {"code": 9446, "msg": f"参数错误,缺少{e}"}
    except Exception as e:
        resp = {"code":9444, "msg":f"{traceback.format_exc()}"}
    return sjson(resp)


mts_llm_bp = Blueprint('mts_agent_llm_v1', url_prefix='/mts_agent/llm/v1')


@mts_llm_bp.route('/match_question', methods=['POST'])
async def match_question(request):
    resp = {"code":-1, "msg":""}
    try:
        query = request.json
        logger.info(f"match_question: {query}")
        check_param(query, ["uid", "content"])
        uid = query["uid"]
        input_txt = query["content"]
        task = query["task_id"] if "task_id" in query else uid
        seq = query["seq"] if "seq" in query else int(time.time()*1000)

        qa_map:dict = query["qa_map"]
        memory_list:list[dict] = query["memory_list"]

        memory_content_map:dict[str, list] = {}
        for memory_map in memory_list:
            if "otherData" in memory_map:
                memory_map.update(memory_map["otherData"])
                del memory_map["otherData"]
            tp = memory_map["type"] if "type" in memory_map else "text"
            if tp not in memory_content_map:
                memory_content_map[tp] = []
            if memory_map['content'] not in memory_content_map[tp]:
                memory_content_map[tp].append(memory_map['content'])

        answer_list = []
        for question in qa_map:
            for qa_node_map in qa_map[question]:
                if "content" in qa_node_map and qa_node_map["content"] not in answer_list:
                    answer_list.append(qa_node_map["content"])

        infer_answer_dict = {"已知信息":answer_list}
        infer_answer_dict.update(memory_content_map)
        question_input_dict = {"1":input_txt}
        llm_data = {'uid':uid, 'question_input_dict':question_input_dict, "infer_answer_dict":infer_answer_dict,}
        answer_response = await request_llm(task, llm_data, "问答匹配")
        answer_map = json.loads(answer_response)

        answer = ""
        for idx in answer_map:
            tmp_answer = answer_map[idx]
            if "status" in tmp_answer and tmp_answer["status"] == 1:
                answer = tmp_answer["answer"]
        code = 0
        msg = "ok"
        if not answer:
            code = -1
            msg = answer_response
        resp = {"code":code, "msg":msg, "uid":uid, "seq":seq, "answer":answer}
    except MissingParamException as e:
        resp = {"code": 9446, "msg": f"参数错误,缺少{e}"}
    except Exception as e:
        resp = {"code":9444, "msg":f"{traceback.format_exc()}"}
    return sjson(resp)


@mts_llm_bp.route('/batch_match_question', methods=['POST'])
async def batch_match_question(request):
    resp = {"code":-1, "msg":""}
    try:
        query = request.json
        logger.info(f"match_question: {query}")
        check_param(query, ["uid", "content_list"])
        uid = query["uid"]
        input_txt_list = query["content_list"]
        task = query["task_id"] if "task_id" in query else uid
        seq = query["seq"] if "seq" in query else int(time.time()*1000)

        qa_map:dict = query["qa_map"]
        memory_list:list[dict] = query["memory_list"]

        memory_content_map:dict[str, list] = {}
        for memory_map in memory_list:
            if "otherData" in memory_map:
                memory_map.update(memory_map["otherData"])
                del memory_map["otherData"]
            tp = memory_map["type"] if "type" in memory_map else "text"
            if tp not in memory_content_map:
                memory_content_map[tp] = []
            if memory_map['content'] not in memory_content_map[tp]:
                memory_content_map[tp].append(memory_map['content'])

        answer_list = []
        for question in qa_map:
            for qa_node_map in qa_map[question]:
                if "content" in qa_node_map and qa_node_map["content"] not in answer_list:
                    answer_list.append(qa_node_map["content"])

        infer_answer_dict = {"已知信息":answer_list}
        infer_answer_dict.update(memory_content_map)
        question_input_dict = {}
        for idx, input_txt in enumerate(input_txt_list):
            question_input_dict[str(idx)] = input_txt
        llm_data = {'uid':uid, 'question_input_dict':question_input_dict, "infer_answer_dict":infer_answer_dict,}
        answer_response = await request_llm(task, llm_data, "问答匹配")
        answer_map = json.loads(answer_response)

        ret_answer_map = {}
        for idx in question_input_dict:
            tmp_question = question_input_dict[idx]
            if idx in answer_map:
                tmp_answer = answer_map[idx]
                if "status" in tmp_answer and tmp_answer["status"] == 1:
                    answer = tmp_answer["answer"]
                    ret_answer_map[tmp_question] = answer
                else:
                    ret_answer_map[tmp_question] = ""
            else:
                ret_answer_map[tmp_question] = ""
        code = 0
        msg = "ok"
        if not ret_answer_map:
            code = -1
            msg = answer_response
        resp = {"code":code, "msg":msg, "uid":uid, "seq":seq, "answer":ret_answer_map}
    except MissingParamException as e:
        resp = {"code": 9446, "msg": f"参数错误,缺少{e}"}
    except Exception as e:
        resp = {"code":9444, "msg":f"{traceback.format_exc()}"}
    return sjson(resp)


if __name__ == '__main__':
    async def main():
        answer_response = """{"1": {"answer": "用户可能会因为事物没有完全按照计划进行而感到极度不安或沮丧，这表明用户不喜欢不确定性和意外，可能会因为无法控制所有细节而感到沮丧或焦虑。因此，可以推测用户有因为事物不完美而避免某些活动或情况的行为。","status": 1}}"""
        question_input_dict = {"1": "用户是否有因为事物不完美而避免某些活动或情况的行为？"}
        answer_map = json.loads(answer_response)

        ret_answer_map = {}
        for idx in question_input_dict:
            tmp_question = question_input_dict[idx]
            if idx in answer_map:
                tmp_answer = answer_map[idx]
                if "status" in tmp_answer and tmp_answer["status"] == 1:
                    answer = tmp_answer["answer"]
                    ret_answer_map[tmp_question] = answer
                else:
                    ret_answer_map[tmp_question] = ""
            else:
                ret_answer_map[tmp_question] = ""

    asyncio.run(main())
    
