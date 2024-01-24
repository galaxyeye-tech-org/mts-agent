#!/usr/bin/python3
import subprocess
from functools import lru_cache
from base.agent_public.agent_log import logger
from base.agent_public.agent_exception import MissingParamException

from setting import BaseConfig

# main_flow = "Main"
# msg_id = "msg_id"
# parent_id = "parent_id"
# attention = "关注度"
# remark = "remark"
# task_id = "task_id"
# target = "目标"
# content = "content"
# uid = "uid"
# role = "role"
# context = "context"
# seq = "seq"
# method = "method"
# data = "data"


@lru_cache(10)
def get_local_ip():
    "获取本机IP地址"
    ip_dict:dict[str, str] = {}
    result = subprocess.check_output(['ifconfig'])
    result = result.decode('utf-8')
    lines = result.split('\n')
    net = ""
    for line in lines:
        if "Link encap" in line:
            net = line.split()[0]
            continue
        if 'inet ' in line:
            ip = line.split()[1].split(":")[1]
            if net:
                ip_dict[net] = ip
    logger.info(f"获取ip:{ip_dict}")
    ret_ip = ""
    for net in ip_dict:
        if not net.startswith("docker") and not ip_dict[net].startswith("127"):
            ret_ip = ip_dict[net]
    return ret_ip


def redis_prefix(key):
    return f"{BaseConfig.RedisKeyPrefix}_{key}"


def trip_redis_prefix(key:str):
    return key.strip(f"{BaseConfig.RedisKeyPrefix}_")


def GenStreamKey(stream):
    "添加stream名称前缀{ConsciousFlow}"
    return redis_prefix(f"{{ConsciousFlow}}_{stream}")


def GenMainStreamKey():
    "主stream名称"
    return GenStreamKey("Main")


def buildSubMsgListKey():
    "模块订阅消息列表key"
    return redis_prefix("register_mode")


def buildTransChatModel(robotid):
    "透传暂存key"
    return redis_prefix(f"trans_chatModel_{robotid}")


def buildTransKey(msgid):
    "透传暂存key"
    return redis_prefix(f"trans_{msgid}")


def buildAttentionRatioKey(model):
    "获取model模块的专注度系数key"
    return redis_prefix(f"attention_ratio_{model}")


def buildMinAttentionKey(model):
    "获取model模块的专注度系数key"
    return redis_prefix(f"min_attention_{model}")


def buildExpStatusKey(uid):
    "获取表达状态key"
    return redis_prefix(f"expression_status_{uid}")


def buildDialogueHistoryKey(uid):
    "对话历史key"
    return redis_prefix(f"{{dialogue_history}}_{uid}")


def buildOutputMapKey(uid):
    "输出格式化key"
    return redis_prefix(f"{{output_history}}_{uid}")


def buildLastTaskKey(uid):
    "最近任务key"
    return redis_prefix(f"last_task_{uid}")


def buildAllUserKey():
    "所有用户key"
    return redis_prefix(f"all_user")


def buildOnlineKey():
    "在线用户key"
    return redis_prefix(f"online_user")


def buildUserStatusKey(uid):
    "用户状态key"
    return redis_prefix(f"user_status_{uid}")


def buildTaskContentKey(uid):
    "任务上下文key"
    return redis_prefix(f"{{task_content}}_{uid}")


def get_task_result_key(task_id):
    "任务结果key"
    return redis_prefix(f"{task_id}_result")


def get_task_llm_response_key(task_id):
    "大模型返回key"
    return redis_prefix(f"{task_id}_llm_response")


def get_second_task_key():
    "主动表达任务key"
    return redis_prefix(f"second_task")


def TTL(hour=12):
    return hour*60*60


def cut_object(result:object, cut=True):
    ret_result = result
    try:
        if isinstance(result, str):
            ret_result = eval(result)
    except Exception as e:
        ret_result = result

    if isinstance(ret_result, list):
        ret_result = cut_list(ret_result, cut)
    elif isinstance(ret_result, dict):
        ret_result = cut_dict(ret_result, cut)
    elif isinstance(ret_result, str):
        ret_result = cut_str(ret_result, cut)
    return ret_result


def cut_dict(result:dict, cut=True):
    ret_result = {}
    for key in result:
        if key not in ("msg_id", "parent_id"):
            ret_result[key] = cut_object(result[key], cut)
        else:
            ret_result[key] = result[key]
    return ret_result


def cut_list(result:list, cut=True):
    ret_result = []
    for key in result:
        ret_result.append(cut_object(key, cut))
    return ret_result


def cut_str(result:str, cut=True):
    cut_len = 256
    if not cut:
        cut_len = len(result)
    ret_result = f"{result[:cut_len]}"
    if len(result) > cut_len:
        ret_result += f"...({len(result)})"
    return ret_result


def check_param(param:dict, key_list:list):
    for key in key_list:
        if not param.get(key):
            raise MissingParamException(f"缺少参数:{key} {param}")


if __name__ == '__main__':
    a = {'uid': 'jgbtest1234', 'seq': '99099', 'content': '你好', '目标': '对话管理', 'task_id': 'jgbtest1234_1701918423219', '写入函数': 'dialogue_service.py:34:input_request', 'parent_id': "['0-0']"}
    logger.info(cut_object(a))
    
