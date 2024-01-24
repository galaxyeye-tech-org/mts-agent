#-*- encoding: utf-8 -*-
__author__ = 'Jianggb'
import asyncio
import time
import traceback
from rediscluster.pipeline import ClusterPipeline

from base.agent_public.agent_log import logger
from base.agent_public.agent_redis import AgentRedis
from base.agent_public.agent_tool import buildAllUserKey, buildOnlineKey, buildUserStatusKey


class UserStatus:
    "用户状态"

    @staticmethod
    async def add_user(uid, pip:ClusterPipeline=None):
        all_user_key = buildAllUserKey()
        if not pip:
            conn = AgentRedis().conn
            conn.sadd(all_user_key, uid)
        else:
            pip.sadd(all_user_key, uid)

    @staticmethod
    async def add_oneline_user(uid, pip:ClusterPipeline=None):
        online_user_key = buildOnlineKey()
        if not pip:
            conn = AgentRedis().conn
            conn.sadd(online_user_key, uid)
        else:
            pip.sadd(online_user_key, uid)

    @staticmethod
    async def del_oneline_user(uid, pip:ClusterPipeline=None):
        online_user_key = buildOnlineKey()
        if not pip:
            conn = AgentRedis().conn
            conn.srem(online_user_key, uid)
        else:
            pip.srem(online_user_key, uid)

    @staticmethod
    async def set_user_role(uid, role_data, robotid="agent001"):
        logger.info(f"设置用户角色:{uid} 角色:{role_data} 机器人id:{robotid}")
        stat_key = buildUserStatusKey(uid)
        AgentRedis().conn.hset(stat_key, mapping={"role":str(role_data)})

    @staticmethod
    async def clear_robot_role(uid, robotid="agent001"):
        logger.info(f"删除用户角色:{uid} 机器人id:{robotid}")
        stat_key = buildUserStatusKey(uid)
        AgentRedis().conn.hdel(stat_key, "role")

    @staticmethod
    async def get_user_role(uid, robotid="agent001"):
        """
        返回示例
        {
          "role": "消防员",
          "description": "作为一名消防员，我负责救火和执行紧急救援任务。我接受过专业的训练，能够处理各种紧急情况，包括火灾、交通事故和自然灾害。我还负责进行火灾预防宣传和检查建筑物的消防安全。在对话中，我会分享我的经验、提供安全建议，并回答有关消防安全和紧急响应的问题。"
        }
        """
        logger.info(f"查询用户角色:{uid} 机器人id:{robotid}")
        stat_key = buildUserStatusKey(uid)
        role_str = AgentRedis().conn.hget(stat_key, "role")
        if role_str:
            try:
                return eval(role_str)
            except Exception as e:
                logger.error(f"获取用户角色失败:{uid} 机器人id:{robotid} 错误信息:{traceback.format_exc()}")
                return None
        else:
            return None

    @staticmethod
    async def set_user_lasted_exp(uid):
        logger.info(f"设置用户最后活跃时间:{uid}")
        stat_key = buildUserStatusKey(uid)
        AgentRedis().conn.hset(stat_key, mapping={"lasted_exp":int(time.time())})

    @staticmethod
    async def set_AI_lasted_exp(uid):
        logger.info(f"设置AI最后活跃时间:{uid}")
        stat_key = buildUserStatusKey(uid)
        AgentRedis().conn.hset(stat_key, mapping={"AI_lasted_exp":int(time.time())})

    @staticmethod
    async def set_AI_second_exp(uid):
        logger.info(f"设置AI第二次活跃时间:{uid}")
        stat_key = buildUserStatusKey(uid)
        AgentRedis().conn.hset(stat_key, mapping={"AI_second_exp":int(time.time())})

    @staticmethod
    async def set_AI_second_task(uid):
        logger.info(f"设置AI第二次活跃任务时间:{uid}")
        stat_key = buildUserStatusKey(uid)
        AgentRedis().conn.hset(stat_key, mapping={"AI_second_task":int(time.time())})

    @staticmethod
    async def get_user_exp_time(uid):
        stat_key = buildUserStatusKey(uid)
        exp_time_map = AgentRedis().conn.hmget(stat_key, "lasted_exp", "AI_lasted_exp", "AI_second_exp", "AI_second_task")
        #logger.info(f"获取用户活跃时间:{uid} 活跃时间:{exp_time_map}")
        return exp_time_map

    @classmethod
    async def set_user_online(cls, uid):
        logger.info(f"用户上线:{uid}")
        stat_key = buildUserStatusKey(uid)
        pip = AgentRedis().conn.pipeline()
        pip.hset(stat_key, mapping={"onlien_stat":1})
        await cls.add_user(uid, pip)
        await cls.add_oneline_user(uid, pip)
        pip.execute()
        await cls.set_user_lasted_exp(uid)

    @classmethod
    async def set_user_offline(cls, uid, pipe:ClusterPipeline=None):
        logger.info(f"用户下线:{uid}")
        stat_key = buildUserStatusKey(uid)
        pip = pipe
        if not pipe:
            pip = AgentRedis().conn.pipeline()
        pip.hset(stat_key, mapping={"onlien_stat":0})
        await cls.del_oneline_user(uid, pip)
        if not pipe:
            pip.execute()

    @staticmethod
    async def get_online_user():
        online_user_key = buildOnlineKey()
        ret = AgentRedis().conn.smembers(online_user_key)
        if not ret:
            return set()
        else:
            return ret

    @classmethod
    async def clear_user_online(cls):
        logger.info(f"清除用户上线状态")
        online_user_key = buildOnlineKey()
        all_online_user = AgentRedis().conn.smembers(online_user_key)
        pip = AgentRedis().conn.pipeline()
        for uid in all_online_user:
            await cls.set_user_offline(uid, pip)
        pip.delete(online_user_key)
        pip.execute()


if __name__ == '__main__':
    async def main():
        user_stat = await UserStatus.get_user_exp_time("jgbtest2002")
        logger.info(user_stat)
    asyncio.run(main())
    
