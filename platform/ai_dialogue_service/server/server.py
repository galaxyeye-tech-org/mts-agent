# -*- coding: utf-8 -*-
# @FileName  : server.py
# @Description TODO
# @Author： yangmingxing
# @Email: yangmingxing@galaxyeye-tech.com
# @Date 11/9/22 2:14 PM 
# @Version 1.0
import requests
import tornado.web
from abc import ABC
import time
import json
import tornado.gen
import tornado.web
import tornado.concurrent
import threading
import openai

from openai import OpenAI
from settings import *
from tools.logger_utils import get_logger_conf
from concurrent.futures import ThreadPoolExecutor
from script.openaiTools import api_openai_text


module_name = str(os.path.basename(__file__)).split('.')[0]
logger = get_logger_conf(log_path, module_name, 'INFO')
embedding_dict = {}

class OpenaiService(tornado.web.RequestHandler, ABC):
    # 定义线程池数量一定叫executor
    executor = ThreadPoolExecutor(1000)  # 并发数量

    def check_params(self, params):
        reserve_origin = params.get("reserve_origin", False)
        robot_id = params.get("robot_id", "").strip()
        query = params.get("query", "").strip()
        system = params.get("system", "").strip()
        messages = params.get("messages", [])
        task = params.get("task", "往后写200字").strip()
        openai_parameter = params.get("openai_parameter", "no").strip()
        model = params.get("model", "gpt-3.5-turbo").strip()
        max_tokens = params.get("max_tokens", 512)
        temperature = params.get("temperature", 0.0)
        top_p = params.get("top_p", 1)
        frequency_penalty = params.get("frequency_penalty", 0.0)
        presence_penalty = params.get("presence_penalty", 0.0)
        stop = params.get("stop", ["Human:"])
        best_of = params.get("best_of", 1)
        penalty_score = float(params.get("penalty_score", 1.0))
        request_source = params.get("request_source", "chat")

        if model == "CPM-Bee":
            if not isinstance(task, str) or len(task) <= 0:
                raise ValueError(f"param task error")

        if "ernieBot" in model:
            if not isinstance(messages, list) or len(messages) <= 0:
                raise ValueError(f"param messages error")

            if system is not None and len(system) >= 1024:
                raise ValueError(f"param system error")

            query = params.get("query", "not content").strip()
            temperature = params.get("temperature", 0.95)
            top_p = params.get("top_p", 0.8)

            messages_roles = [tmp_role["role"] for tmp_role in messages]
            if "system" in messages_roles:
                raise ValueError(f"param messages error: Messgames cannot contain role: system")

            if len(messages) % 2 != 1:
                raise ValueError(f"the length of messages must be an odd number")

            for index in range(len(messages_roles)):
                if (index) % 2 == 0 and messages_roles[index] != "user":
                    raise ValueError(f"the odd digit role of messages must be user")

                if (index) % 2 == 1 and messages_roles[index] != "assistant":
                    raise ValueError(f"even numbered roles in the message must be assistants")

            last_content = messages[-1]["content"]
            if len(last_content) >= 2000:
                raise ValueError(f"param messages error: The content length of the last round of user exceeds 2000")

            last_role = messages[-1]["role"]
            if last_role != "user":
                raise ValueError(f"param messages error: messages must end with role as user")

            if penalty_score < 1.0 or penalty_score > 2.0:
                raise ValueError(f"param penalty_score error")

            if temperature == 0.0:
                temperature = 0.1

        if model == "text-davinci-003" and (not isinstance(query, str) or len(query) <= 0):
            raise ValueError(f"param query error")

        if not isinstance(openai_parameter, str) or openai_parameter not in ["yes", "no"]:
            raise ValueError(f"param openaiParameter error")

        if not isinstance(model, str) or len(model) <= 0:
            raise ValueError(f"param model error")

        if not isinstance(max_tokens, int) or (max_tokens < 1 or max_tokens > 4097):
            raise ValueError(f"param maxTokens out of range(0~4097): {max_tokens}")

        if not isinstance(float(temperature), float) or (temperature < 0.0 or temperature > 1.0):
            raise ValueError(f"param temperature out of range(0~1.0): {temperature}")

        if not isinstance(float(top_p), float) or (top_p < 0.0 or top_p > 1.0):
            raise ValueError(f"param topP out of range(0.0~1.0): {top_p}")

        if not isinstance(float(frequency_penalty), float) or (frequency_penalty < 0.0 or frequency_penalty > 2.0):
            raise ValueError(f"param frequencyPenalty out of range(0.0~2.0): {frequency_penalty}")

        if not isinstance(float(presence_penalty), float) or (presence_penalty < 0.0 or presence_penalty > 2.0):
            raise ValueError(f"param presencePenalty out of range(0.0~2.0): {presence_penalty}")

        if not isinstance(best_of, int) or (best_of < 0 or best_of > 20):
            raise ValueError(f"param bestOf out of range(0~20): {best_of}")

        if not isinstance(stop, list) or len(stop) <= 0 or len(stop) > 4:
            raise ValueError("param stop error, supports up to 4 groups")

        stop = [tmp.strip() for tmp in stop if tmp != None and len(tmp.strip()) > 0]

        checked_param = {
            "robot_id": robot_id,
            "query": query,
            "system": system,
            "messages": messages,
            "task": task,
            "model": model,
            "openai_parameter": openai_parameter,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "top_p": top_p,
            "frequency_penalty": frequency_penalty,
            "presence_penalty": presence_penalty,
            "stop": stop,
            "best_of": best_of,
            "penalty_score": penalty_score,
            "reserve_origin": reserve_origin,
            "request_source": request_source
        }
        return checked_param

    @tornado.concurrent.run_on_executor
    def query_match(self, checked_param):
        openai_dict = api_openai_text(checked_param)
        return openai_dict

    def get_human_query(self, query, response_text):
        # 二次请求追加文本处理
        if query[-27:] == "AI:嗯嗯,你继续说\n Human:我说完了\n AI:":
            query = query[:-27]

        tmp_human_query = query.split("Human:")[-1]
        tmp_human_query.replace("\n", "")
        human_query = tmp_human_query.split("AI:")[0].strip()

        match_query = f'“{human_query}”'
        for i in range(10):
            match_ret = response_text.startswith(match_query)
            if match_ret:
                response_text = response_text[len(match_query):].strip()
            if not match_ret:
                break

        response__text = f'“{human_query}” {response_text}'
        return response__text

    @tornado.gen.coroutine
    def post(self):
        response_ = {}
        logger_info = {}

        try:
            request_js = json.loads(str(self.request.body, encoding='utf-8'))
            logger.info('rcv: {} {}'.format(self.request.uri, request_js))

            if self.request.uri == '/gptService/v1/sentenceZH':
                s_time = time.time()
                checked_param = self.check_params(request_js)
                openai_dict = yield self.query_match(checked_param)

                logger_info = {
                            "code": openai_dict["code"],
                            "param": checked_param,
                            "response": openai_dict["response_text"],
                            "request_tokens": openai_dict["prompt_completion"],
                            "request_len": openai_dict.get("prompt_completion_len", 0)
                }
                if openai_dict["code"] != 200:
                    logger_info["error"] = f'{openai_dict["code"]}:{openai_dict["data"]}'
                    response_ = {
                        "code": openai_dict["code"],
                        "msg": f'{openai_dict["response_text"]}'
                    }
                else:
                    response__text = logger_info["response"]

                    if checked_param["robot_id"] and checked_param["robot_id"] == "robot013":
                        response__text = self.get_human_query(checked_param["query"], response__text)

                    response_ = {
                        "code": 1,
                        "msg": "success",
                        "data": {
                            "tokens": openai_dict["prompt_completion"],
                            "response": response__text}
                    }

                e_time = time.time()
                diff_time = "%.3f" % (e_time - s_time)
                logger_info["request_time"] = diff_time
                logger.info(json.dumps(logger_info, ensure_ascii=False))

        except json.decoder.JSONDecodeError:
            response_ = {
                "code": -4,
                "msg": "JSONDecodeError",
            }
            logger.error(response_)

        except KeyError as e:
            response_ = {
                "code": -1,
                "msg": f'param error:{e.args[0]}'
            }
            logger.error(response_)

        except ValueError as e:
            response_ = {
                "code": -2,
                "msg": f'param error:{e.args[0]}'
            }
            logger.error(response_)

        except EOFError:
            response_ = {
                "code": -3,
                "msg": "EOFError",
            }
            logger.error(response_)

        except Exception as e:
            response_ = {
                "code": -100,
                "msg": e.args[0]
            }
            logger.error(response_)

        finally:
            self.set_header("Content-type", "application/json;charset=UTF-8")
            self.write(json.dumps(response_, ensure_ascii=False, indent=None))
            self.flush()
