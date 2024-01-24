#-*- encoding: utf-8 -*-
__author__ = 'Jianggb'
import asyncio
import json
from ssl import get_server_certificate

from base.agent_public.agent_log import logger
from base.agent_http.agent_http_client import sendRequestSync
from base.agent_storage_client.agent_storage import StorageClient
from base.large_model_client.agent_prompt import get_prompt
from base.large_model_client.agent_prompt_response import package_response_ws
from base.agent_storage_client.agent_content import ContentResult

from setting import BaseConfig


async def request_llm(section_taskid, param:dict, prompt_type, history_list=None, role="assistant", exp_status="绿灯"):
    """生成内容 
    """
    uid = param["uid"] if "uid" in param else "0"
    
    if exp_status == "红灯" and BaseConfig.DialoguePrompt and prompt_type in BaseConfig.DialoguePrompt:
        await ContentResult.add_main_result(section_taskid, {prompt_type: ("表达状态为红灯",f"{prompt_type} 不生成回复")})
        return None

    logger.info(f"request_llm {section_taskid=} {param=} {prompt_type=} {history_list=}")

    prompt = get_prompt(prompt_type)

    prompt.get_script_prompt(param)

    system_prompt = prompt.get_system_prompt(param)
    parameter = prompt.get_parameter()

    user_prompt = prompt.get_user_prompt(param)
    assistant_prompt = prompt.get_assistant_prompt(param)
    other_prompt = prompt.get_other_prompt(param)

    data_message = []
    if system_prompt:
        data_message.append({"content":system_prompt, "role": "system"})
    
    if BaseConfig.DialoguePrompt and prompt_type in BaseConfig.DialoguePrompt and history_list:
        message_history = []
        for history in history_list:
            role = history["role"] if history["role"] == "user" else "assistant"
            content = history["content"]
            try:
                content = json.dumps(eval(content), ensure_ascii=False)
            except Exception as e:
                content = history["content"]
            ori_dialog = {"content": content, "role": role}
            message_history.append(ori_dialog)
        data_message.extend(message_history)

    if user_prompt:
        data_message.append({"content":user_prompt, "role": "user"})
    if assistant_prompt:
        data_message.append({"content":assistant_prompt, "role": role})
    if other_prompt:
        role_list = ["user", role]
        count = 0
        for prompt in other_prompt:
            data_message.append({"content":prompt, "role": role_list[count%2]})
            count += 1
    
    data = {'stop': ['ASSISTANT：', 'USER：', 'Q：'], 'model': 'gpt-4-1106-preview', 'maxTokens':4000, 
            'max_tokens':4000, "reserveOrigin":True, "reserve_origin":True,"requestSource":"longtext"}
    if data_message:
        data["messages"] = data_message
    if parameter:
        data.update(parameter)

    # if prompt_type in ["关注度", "分流"]:
    ret = await sendRequestSync(BaseConfig.GptServer, data, uid, timeout=120)
    if "data" in ret and "response" in ret["data"]:
        ret = ret["data"]["response"]
    else:
        ret = ""
    # else:
    #     ret = await gptWebsocketSync(gpt_ws_server, data, uid, timeout=120)
    resp =  package_response_ws(ret, prompt_type)
    await ContentResult.add_task_llm_result(section_taskid, prompt_type, resp)
    await ContentResult.add_main_result(section_taskid, {prompt_type:{"请求":data, "返回":resp}})
    return resp


if __name__ == '__main__':

    import time
    async def main():
        now_time = int(time.time()*1000)
        uid = "jgbtest2003"
        formate_history_list = await StorageClient.get_output_history(uid)
        param = {'uid': 'jgbtest2003', 'dialog_list': [{'role': 'user', 'content': '最近很不开心。'}, {'role': 'assistant', 'content': '发生了什么事让你感到不开心呢？'}, {'role': 'user', 'content': '天气太冷了。'}], 'question_answer_dict': {}, 'work_memory': {}, 'embedding_memory': {}, 'strategy_memory': [], 'input': '天气太冷了。', 'question_unsolved_dict': {}, 'robot_role': None}
        ret = await request_llm(uid, param, "响应", history_list=formate_history_list)
        logger.info(f"{ret}")
    tmp = "{'selected_strategy': '引导', 'response': '发生了什么事让你感到不开心呢？'}"
    tmp = eval(tmp)
    print(tmp)
    tmp = json.dumps(tmp, ensure_ascii=False)
    print(tmp)
    asyncio.run(main())
    