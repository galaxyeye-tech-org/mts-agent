#-*- encoding: utf-8 -*-
__author__ = 'Jianggb'
import json
import optparse
import re
import sys
import traceback

from base.agent_public.agent_log import logger


def package_response_ws(gpt_ret:str, prompt_type):
    "解析返回内容"
    try:
        resp = public_response_ws(gpt_ret)
        # match prompt_type:
        #     case "关注度":
        #         resp = package_attention_ws(gpt_ret)
        #     case "分流":
        #         resp = package_divide_ws(gpt_ret)
        #     case "问题分解":
        #         resp = package_diffusion_ws(gpt_ret)
        #     case "响应":
        #         resp = package_gpt_response_ws(gpt_ret)
        #     case "回答判断":
        #         resp = package_judge_question_ws(gpt_ret)
        #     case "问题分类与工具":
        #         resp = package_divide_tool_ws(gpt_ret)
        #     case "搜索公共知识库":
        #         resp = package_gpt_response_ws(gpt_ret)
        #     case "任务分析":
        #         resp = package_task_response_ws(gpt_ret)
        #     case "提问":
        #         resp = package_gpt_response_ws(gpt_ret)
        #     case _:
        #         logger.error(f"prompt_type:{prompt_type} not support")
        return resp
    except Exception as e:
        logger.error(f"{traceback.format_exc()}")


def public_response_ws(gpt_ret:str):
    "公共返回内容"
    resp = gpt_ret
    try:
        if gpt_ret.find("```json") != -1:
            resp_ret = ""
            lines = gpt_ret.splitlines(keepends=True)
            for line in lines:
                if line.startswith("```json"):
                    resp_ret = line
                elif resp_ret:
                    resp_ret += line
                elif line.startswith("```"):
                    resp_ret += line
                    break
            resp = resp_ret.replace("```json", "")
            pox = resp.find("```")
            if pox != -1:
                resp = resp[:pox]
    except Exception as e:
        logger.error(f"{traceback.format_exc()}")
    return resp


def package_response(gpt_ret:dict, prompt_type):
    "生成内容分解返回"
    resp = ""
    if "code" in gpt_ret and gpt_ret["code"] == 1 and "data" in gpt_ret and "response" in gpt_ret["data"]:
        resp = gpt_ret["data"]["response"]
    resp = package_response_ws(resp, prompt_type)
    return resp


def package_attention_ws(gpt_ret:str):
    "关注度返回"
    numbers_in_string = re.findall(r'(\d+)', gpt_ret)
    resp = 10
    if numbers_in_string:
        resp = int(numbers_in_string[0])
    if resp > 100:
        resp = 100
    return resp


def package_divide_ws(gpt_ret:str):
    "分类器返回"
    resp = {}
    pattern =  r'(\d+)[\.。](.*)'
    re_list = re.findall(pattern, gpt_ret)
    resp = {match[0]: match[1].strip() for match in re_list}
    return resp


def package_diffusion_ws(gpt_ret:str):
    "问题扩散返回"
    resp = {}
    pattern =  r'(\d+)[\.。](.*)'
    re_list = re.findall(pattern, gpt_ret)
    resp = {match[0]: match[1].strip() for match in re_list}
    return resp


def package_gpt_response_ws(gpt_ret:str):
    "响应返回"
    resp = gpt_ret
    return resp


def package_judge_question_ws(gpt_ret:str):
    "问题判断返回"
    resp = {}
    pattern =  r'(\d+)[\.。](.*)'
    re_list = re.findall(pattern, gpt_ret)
    resp = {match[0]: match[1].strip() for match in re_list}
    return resp


def package_divide_tool_ws(gpt_ret:str):
    "问题分类工具返回"
    """
    {"function":"提问具体对象","parameter":{"问题":"你是谁","对象":"对话者"}}
    {"function":"搜索公共知识库","parameter":{"问题":"你是谁","侧重点":"对话者"}}
    """
    resp = []
    try:
        resp = json.loads(gpt_ret)
    except Exception as e:
        lines = gpt_ret.splitlines(keepends=True)
        for line in lines:
            try:
                json_ret = json.loads(line)
                if not isinstance(json_ret, list):
                    resp.append(json.loads(line))
                else:
                    resp.extend(json_ret)
            except Exception as e:
                logger.error(f"gpt_ret:{line} is not json")
    return resp


def package_task_response_ws(gpt_ret:str):
    "任务分析返回"
    """
    {"Ambition":"帮助小林处理他们的情绪困扰，提供应对家庭紧张和不稳定环境的策略，并寻找健康的方式来表达和管理他们的情感，特别是关注到他们自伤的行为，提供紧急的心理支持和专业的干预措施。"}
    """
    resp = {}
    try:
        resp = json.loads(gpt_ret)
    except Exception as e:
        logger.error(f"gpt_ret:{gpt_ret} is not json")
    return resp


if __name__ == '__main__':
    resp = public_response_ws("""输出：\n```json\n{\"type\":\"好奇\",\"content\":\"什么医学条件可能会导致持续>性的头晕和晕厉害？\"}\n```""")
    logger.info(resp)
    logger.info(json.loads(resp))
    resp = public_response_ws("您能分享一下是什么事情让您感到不开心吗？")
    logger.info(resp)
    resp = public_response_ws("""```json{"answer": "是的，管理层支持也参与了团队合作的增强。", "status": 1}```""")
    logger.info(resp)
