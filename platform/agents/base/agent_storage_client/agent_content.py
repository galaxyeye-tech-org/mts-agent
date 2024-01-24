#-*- encoding: utf-8 -*-
__author__ = 'Jianggb'
import asyncio
import time
import traceback

from base.agent_public.agent_log import logger
from base.agent_public.agent_redis import AgentRedis
from base.agent_public.agent_tool import get_task_result_key, TTL, cut_object, get_task_llm_response_key


class ContentResult:
    "大模型任务结果存储"
    def __init__(self):
        ""

    @staticmethod
    async def add_task_llm_result(task, prompt_type, response):
        llm_key = get_task_llm_response_key(task)
        conn = AgentRedis().conn
        conn.hset(llm_key, mapping={f"{prompt_type}_response":str(response)})
        conn.expire(llm_key, TTL(7*24))

    @staticmethod
    async def get_task_llm_result(task):
        llm_key = get_task_llm_response_key(task)
        llm_response =  AgentRedis().conn.hgetall(llm_key)
        if not llm_response:
            return {}
        return llm_response

    @staticmethod
    async def add_main_result(task, result:dict):
        logger.info(f"{task} 任务进度:{cut_object(result)}")
        task_result_key = get_task_result_key(task)
        now_time = int(time.time()*1000)
        task_result = {f"{now_time}_{k}":str(result[k]) for k in result}
        conn = AgentRedis().conn
        conn.hset(task_result_key, mapping=task_result)
        conn.expire(task_result_key, TTL(7*24))


    @staticmethod
    async def get_task_result(task):
        task_result_key = get_task_result_key(task)
        conn = AgentRedis().conn
        ret = conn.hgetall(task_result_key)
        ret = cut_object(ret)
        return ret

    @staticmethod
    async def clear_context(task):
        task_result_key = get_task_result_key(task)
        conn = AgentRedis().conn
        conn.delete(task_result_key)

    @staticmethod
    async def get_task_result_by_field(task, field):
        task_result_key = get_task_result_key(task)
        conn = AgentRedis().conn
        ret = conn.hgetall(task_result_key)
        for key in ret:
            if field in key:
                return ret[key]
        return ""

    @staticmethod
    async def set_task_diffuse_energy(task, diffuse_energy):
        llm_key = get_task_llm_response_key(task)
        logger.info(f"设置任务{task} 的扩散能量为 {diffuse_energy}")
        conn = AgentRedis().conn
        conn.hset(llm_key, mapping={"diffuse_energy":str(diffuse_energy)})
        conn.expire(llm_key, TTL(7*24))

    @staticmethod
    async def get_task_diffuse_energy(task):
        llm_key = get_task_llm_response_key(task)
        conn = AgentRedis().conn
        diffuse_energy = conn.hget(llm_key, "diffuse_energy")
        if diffuse_energy:
            try:
                diffuse_energy = float(diffuse_energy)
            except Exception as e:
                traceback.print_exc()
                diffuse_energy = None
        return diffuse_energy


if __name__ == '__main__':
    async def main():
        conn = AgentRedis().conn
        #ContentResult().add_main_result('test', {'a':1, 'b':2})
        task = 'cmrtest007_1702863248580'
        diffuse_energy = await ContentResult().get_task_diffuse_energy(task)
        print(diffuse_energy)
        await ContentResult().set_task_diffuse_energy(task, diffuse_energy*0.7)
        print(diffuse_energy)
        diffuse_energy = await ContentResult().get_task_diffuse_energy(task)
        print(diffuse_energy)
    asyncio.run(main())