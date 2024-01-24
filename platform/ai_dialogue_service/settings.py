# -*- coding: utf-8 -*-
# @FileName  : settings.py
# @Description TODO
# @Author： yangmingxing
# @Email: yangmingxing@galaxyeye-tech.com
# @Date 11/9/22 2:11 PM 
# @Version 1.0
# 项目主目录
import os

def project_dir(project_name):
    cwd = os.getcwd()
    pro_list = cwd.split("/")[::-1]

    pro_index = 0
    for index in range(len(pro_list)):
        if project_name in pro_list[index]:
            pro_index = index
            break

    project_path_list = pro_list[pro_index:]
    return "/".join(project_path_list[::-1])


project_path = project_dir("ai_dialogue_service")
# 日志目录
log_path = f'{project_path}/logs'

openai_info = {
            "openai_url": "https://api.openai.com",
            "openai_api_key":os.environ.get("openai_api_key", None),
            "openai_type": "api",
            "chat_request_timeout": 300,
            "text_request_timeout": 600
            }