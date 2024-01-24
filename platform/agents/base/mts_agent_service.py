#-*- encoding: utf-8 -*-
__author__ = 'Jianggb'
import optparse
import sys
import traceback
from sanic import Sanic
from sanic.server.protocols.websocket_protocol import WebSocketProtocol
from base.agent_public.agent_log import logger
from base.agent_storage_client.user_status import UserStatus
from base.service import DataSource
from classific_service.divide_service_blueprint import divide_bp, mts_llm_bp
from dialogue_service.gm_command_blueprint import gm_bp
from dialogue_service.dialogue_service_blueprint import dialogue_bp, expression
from base.thoughts_flow_client.thoughtsFlow import ThoughtFlow
from summarize_service.summarize_service_blueprint import summarize_bp
from strategy_service.strategy_service_blueprint import strategy_bp

from setting import EnvConfig, BaseConfig, PromptConfig


thtflow = ThoughtFlow()

app = Sanic("mts_agent")
app.blueprint(divide_bp)
app.blueprint(dialogue_bp)
app.blueprint(gm_bp)
app.blueprint(summarize_bp)
app.blueprint(mts_llm_bp)
app.blueprint(strategy_bp)

# 在应用启动时启动工作协程
@app.listener('before_server_start')
async def start_background_task(app:Sanic, loop):

    await UserStatus.clear_user_online()
    BaseConfig.open()
    PromptConfig.open()

    await DataSource.initialize()

    for i in range(2):
        app.add_task(expression())


@app.listener(r'before_server_stop')
async def system_release():

    await DataSource.release()

    PromptConfig.close()
    BaseConfig.close()


if __name__ == '__main__':
    if len(sys.argv) == 1:

        app.run(host="0.0.0.0", port=EnvConfig.PORT, protocol=WebSocketProtocol, single_process=True)
    else:
        usage = "Usage: %prog [options]"
        parser = optparse.OptionParser(usage=usage)
        parser.add_option('-T', '--think', action="store_true", dest="think", help='主动思维')
        parser.add_option('-S', '--speed', action="store_true", dest="speed", help='快速消费挤压消息,不处理')
        try:
            options, args = parser.parse_args()
            logger.info(args)
            if len(args) > 0:
                parser.print_help()
                exit(4)
            if getattr(options, 'speed'):
                parser.print_help()
                exit(4)
        except Exception as e:
            traceback.print_exc()
            parser.print_help()
            exit(4)
    