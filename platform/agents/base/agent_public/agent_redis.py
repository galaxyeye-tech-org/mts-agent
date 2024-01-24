#!/usr/bin/python3
from rediscluster import RedisCluster
import redis,traceback,sys,optparse
import threading
from base.agent_public.agent_log import logger

from setting import BaseConfig


class AgentRedis(object):
    _instance_lock = threading.Lock()
    nodes = [{"host": BaseConfig.RedisIp, "port": BaseConfig.RedisPort}]
    logger.info(nodes)
    conn = None
    def __init__(self):
        if AgentRedis.conn != None:
            pass
        else:
            if BaseConfig.RedisCluster:
                if BaseConfig.RedisPwd:
                    AgentRedis.conn = RedisCluster(startup_nodes=AgentRedis.nodes, password=BaseConfig.RedisPwd, decode_responses=True, 
                                                cluster_down_retry_attempts=3)
                else:
                    AgentRedis.conn = RedisCluster(startup_nodes=AgentRedis.nodes, decode_responses=True, cluster_down_retry_attempts=3)
            else:
                AgentRedis.conn = redis.Redis(BaseConfig.RedisIp, BaseConfig.RedisPort, password=BaseConfig.RedisPwd, decode_responses=True)
        self.conn = AgentRedis.conn


def test():
    nodes = [{"host": "127.0.0.1", "port": 6379}]
    redisIp = "127.0.0.1"
    redisPort = 6379
    conn = redis.Redis(redisIp, redisPort, password=BaseConfig.RedisPwd, decode_responses=True)
    logger.info(conn)
    

    
if __name__ == '__main__':
    if len(sys.argv) == 1:
        test()
    else:
        usage = "Usage: %prog [options]"
        parser = optparse.OptionParser(usage=usage)
        parser.add_option('-F', '--flush', action="store_true", dest="flush", help='清数据')
        try:
            options, args = parser.parse_args()
            print(args)
            if len(args) > 0:
                parser.print_help()
                exit(4)
            if getattr(options, 'flush'):
                print(AgentRedis().conn.flushall())
            else:
                parser.print_help()
                exit(4)
        except Exception as e:
            traceback.print_exc()
            parser.print_help()
            exit(4)
    for h in logger.logger.handlers:
        h.close()
