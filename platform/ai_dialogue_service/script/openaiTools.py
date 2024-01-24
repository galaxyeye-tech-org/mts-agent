# -*- coding: utf-8 -*-
# @FileName  : openaiTools.py
# @Description TODO
# @Author： yangmingxing
# @Email: yangmingxing@galaxyeye-tech.com
# @Date 11/9/22 2:20 PM 
# @Version 1.0

import requests
import json
import time
from settings import *


def reply_detection(new_result, reserve_origin=False):
    if not reserve_origin:
        new_result = new_result.strip().replace("\n", "")
        ret_response = new_result.replace("[", "").replace("]", "")
    else:
        ret_response = new_result
    return ret_response

def api_openai_text(checked_param):

    api_key = openai_info.get("openai_api_key")
    if api_key is None:
        openai_dict = {
            "code": -2,
            "response_text": "api_key can not be null",
            "prompt_completion": None,
            "prompt_completion_len": None,
            "data": None
        }
        return openai_dict

    openai_base_url = openai_info.get("openai_url")

    if checked_param["request_source"] == "chat":
        request_timeout = openai_info.get("chat_request_timeout")
    else:
        request_timeout = openai_info.get("text_request_timeout")

    openai_dict = {}
    if checked_param["stop"] is not None and len(checked_param["stop"]) <= 0:
        stop = None
    else:
        stop = checked_param["stop"]

    data = {
        "model": checked_param["model"],
        "prompt": checked_param["query"],
        "messages": checked_param["messages"],
        "temperature" : checked_param["temperature"],
        "max_tokens" : checked_param["max_tokens"],
        "stop": stop,
        "top_p": checked_param["top_p"],
        "frequency_penalty": checked_param["frequency_penalty"],
        "presence_penalty": checked_param["presence_penalty"],
        "best_of": checked_param["best_of"]
    }

    if checked_param["model"] == "text-davinci-003":
        openai_url = openai_base_url + "/v1/completions"
        data.pop("messages")
    else:
        openai_url = openai_base_url + "/v1/chat/completions"
        data.pop("best_of")
        data.pop("prompt")

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }

    try:
        response = requests.post(openai_url, headers=headers, data=json.dumps(data), timeout=request_timeout)
    except Exception as e:
        openai_dict = {
            "code": 500,
            "response_text": str(e),
            "prompt_completion": {},
            "prompt_completion_len": {},
            "data": data
        }
        return openai_dict

    if response.status_code != 200:
        openai_dict = {
            "code": response.status_code,
            "response_text": json.loads(response.text),
            "prompt_completion": {},
            "prompt_completion_len": {},
            "data": data
        }
        return openai_dict

    result_data = json.loads(response.text)
    response = result_data["choices"][0]

    if checked_param["model"] == "text-davinci-003":
        result = response.get("text", "")
    else:
        result = response.get("message", {}).get("content")

    usage = result_data.get("usage", {})
    prompt_tokens = usage.get("prompt_tokens", 0)
    completion_tokens = usage.get("completion_tokens", 0)
    total_tokens = usage.get("total_tokens", 0)
    prompt_completion = {"prompt_tokens": prompt_tokens,
                         "completion_tokens": completion_tokens,
                         "total_tokens": total_tokens}

    try:
        messages_json = json.dumps(checked_param["messages"], ensure_ascii=False)
        message_len = len(messages_json)
    except Exception as e:
        message_len = 0

    prompt_completion_len = {"prompt_len": message_len,
                             "completion_len": len(result),
                             "total_len": len(checked_param["query"]) + len(result)}

    openai_dict = {
        "code": 200,
        "response_text": reply_detection(result, checked_param["reserve_origin"]),
        "prompt_completion": prompt_completion,
        "prompt_completion_len": prompt_completion_len,
        "data": None
    }

    return openai_dict

