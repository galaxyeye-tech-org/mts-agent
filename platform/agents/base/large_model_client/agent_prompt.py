#-*- encoding: utf-8 -*-
__author__ = 'Jianggb'
import json
import optparse
import sys
import traceback

from base.agent_public.agent_log import logger

from setting import PromptConfig


def get_prompt(prompt_type):
    "获取prompt"
    ret = None
    if prompt_type not in PromptConfig:
        logger.info(f"没有{prompt_type}的配置")
        return ret
    return PromptFile(prompt_type)


class PromptFile:
    def __init__(self, prompt_type):
        self.system_prompt = ""
        self.user_prompt = ""
        self.assistant_prompt = ""
        self.script_prompt = ""
        self.script_result_map = {}
        self.prompt_list = []
        self.prompt_param_list = []
        self.parameter = {}
        self.prompt_type = prompt_type
        self.read_prompt()

    def read_prompt(self):
        now_section = ""
        config:str = PromptConfig[self.prompt_type]
        if not config:
            logger.info(f"没有{self.prompt_type}的配置")
            return
        lines :list[str]= config.splitlines(keepends=True)
        tmp_prompt = ""
        for line in lines:
            line = line.replace("\r", "")
            param_beg_pos = line.find("{{{")
            param_end_pos = line.find("}}}")
            while param_beg_pos != -1 and param_end_pos != -1:
                if param_beg_pos != -1 and param_end_pos != -1:
                    param_name = line[param_beg_pos+3:param_end_pos]
                    if param_name not in self.prompt_param_list:
                        self.prompt_param_list.append(param_name)
                param_beg_pos = line.find("{{{", param_end_pos+3)
                param_end_pos = line.find("}}}", param_end_pos+3)

            if line.startswith("---prompt:"):
                tmp_section = line[10:-4]
                if tmp_prompt:
                    tmp_prompt = tmp_prompt.strip("\n")
                    if now_section == "system":
                        self.system_prompt = tmp_prompt
                    elif now_section == "user":
                        if not self.user_prompt:
                            self.user_prompt = tmp_prompt
                        else:
                            self.prompt_list.append(tmp_prompt)
                    elif now_section == "assistant":
                        if not self.assistant_prompt:
                            self.assistant_prompt = tmp_prompt
                        else:
                            self.prompt_list.append(tmp_prompt)
                    elif now_section == "script":
                        self.script_prompt = tmp_prompt
                tmp_prompt = ""
                now_section = tmp_section
            else:
                if now_section == "parameter":
                    line = line.strip("\n")
                    param_list = line.split(":")
                    if len(param_list) > 1:
                        self.parameter[param_list[0]] = float(param_list[1])
                else:
                    tmp_prompt += line

        if tmp_prompt:
            tmp_prompt = tmp_prompt.strip("\n")
            if now_section == "system":
                self.system_prompt = tmp_prompt
            elif now_section == "user":
                if not self.user_prompt:
                    self.user_prompt = tmp_prompt
                else:
                    self.prompt_list.append(tmp_prompt)
            elif now_section == "assistant":
                if not self.assistant_prompt:
                    self.assistant_prompt = tmp_prompt
                else:
                    self.prompt_list.append(tmp_prompt)
        
    def get_script_prompt(self, param:dict):
        ret_prompt = self.script_prompt
        ret_prompt = self.replace_prompt(ret_prompt, param, defualt_value="None")
        self.script_result_map = self.exec_code(ret_prompt)
        param.update(self.script_result_map)
        return self.script_result_map

    def get_system_prompt(self, param):
        ret_prompt = self.system_prompt
        ret_prompt = self.replace_prompt(ret_prompt, param)
        return ret_prompt

    def get_user_prompt(self, param):
        ret_prompt = self.user_prompt
        ret_prompt = self.replace_prompt(ret_prompt, param)
        return ret_prompt

    def get_assistant_prompt(self, param):
        ret_prompt = self.assistant_prompt
        ret_prompt = self.replace_prompt(ret_prompt, param)
        return ret_prompt

    def get_other_prompt(self, param):
        ret_prompt_list = []
        prompt_list = self.prompt_list
        for ret_prompt in prompt_list:
            tmp_prompt = self.replace_prompt(ret_prompt, param)
            ret_prompt_list.append(tmp_prompt)
        return ret_prompt_list

    def replace_prompt(self, prompt, param:dict, defualt_value=""):

        param_list = self.prompt_param_list

        ret_prompt:str = prompt
        if self.script_result_map:
            param.update(self.script_result_map)

        for p in param_list:
            prompt_key = "{{{" + p + "}}}"
            if prompt_key in ret_prompt:
                p_idx = p
                if p_idx in param and param[p_idx] is not None:
                    replace_obj = param[p_idx]
                    try:
                        if replace_obj and not isinstance(replace_obj, str):
                            replace_obj = json.dumps(param[p_idx], indent=4, ensure_ascii=False)
                    except Exception as e:
                        replace_obj = str(param[p_idx])
                    ret_prompt = ret_prompt.replace(prompt_key, str(replace_obj))
                else:
                    ret_prompt = ret_prompt.replace(prompt_key, defualt_value)
                    logger.info(f"{self.prompt_type} 存在 {prompt_key} ，但参数中没有 {p_idx}")

        return ret_prompt


    def get_parameter(self):
        ret_param = self.parameter
        if "presencePenalty" in ret_param:
            ret_param["presence_penalty"] = ret_param["presencePenalty"]
        return self.parameter


    def exec_code(self, code_str:str):
        "执行代码"
        ret = {}
        try:
            logger.info(f"脚本执行代码：{code_str}")
            global_vars = {}
            local_vars = {}
            exec(code_str, global_vars, local_vars)
            ret = local_vars
        except Exception as e:
            logger.error(f"exec_code:{traceback.format_exc()}")
        return ret


if __name__ == '__main__':
    prompt = get_prompt("响应")
    param = {'uid': 'cmrtest021', 'dialog_list': [{'role': 'user', 'content': '你好。'}, {'role': 'assistant', 'content': '你好！有什么可以帮助你的吗？'}, {'role': 'user', 'content': '哎，开公司好难。'}, {'role': 'assistant', 'content': '确实，开公司是一个充满挑战的过程。遇到了什么具体困难吗？'}, {'role': 'user', 'content': '和合伙人意见不统一。'}, {'role': 'assistant', 'content': '这是常见的问题。试着找到共同点，或者考虑聘请第三方顾问来帮助调解意见分歧。'}, {'role': 'user', 'content': '没啥共同的>。'}], 'question_answer_dict': {}, 'work_memory': {'用户陈述': ['哎，开公司好难。', '我和合伙人意见不统一。']}, 'embedding_memory': {'用户陈述': ['哎，开公司好难。', '我和合伙人意见不统一。']}, 'strategy_memory': [], 'input': '没啥共同的。', 'question_unsolved_dict': {'1': '开公司过程中哪一个方面让你感觉最为困难？'}}


    prompt.get_script_prompt(param)

    system_prompt = prompt.get_system_prompt(param)
    parameter = prompt.get_parameter()

    user_prompt = prompt.get_user_prompt(param)
    assistant_prompt = prompt.get_assistant_prompt(param)
    other_prompt = prompt.get_other_prompt(param)
    print(system_prompt)
    print(user_prompt)
    print(assistant_prompt)
    print(other_prompt)

