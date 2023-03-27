import json
import os
import traceback
from http.server import HTTPServer, SimpleHTTPRequestHandler
from threading import Thread
from typing import Callable, Any, Optional
from urllib import parse

from mys_goods_tool.data_model import GeetestResult
from user_data import ROOT_PATH
from user_data import config as conf
from utils import logger, get_free_port

STATIC_DIRECTORY = ROOT_PATH / "geetest-webui"


class GeetestHandler(SimpleHTTPRequestHandler):
    get_result: Callable[[GeetestResult], Any]

    def log_message(self, format: str, *args: Any) -> None:
        """
        重写父类方法，更改日志输出到loguru

        Log an arbitrary message.

        This is used by all other logging functions.  Override
        it if you have specific logging wishes.

        The first argument, FORMAT, is a format string for the
        message to be logged.  If the format string contains
        any % escapes requiring parameters, they should be
        specified as subsequent arguments (it's just like
        printf!).

        The client ip and current date/time are prefixed to
        every message.
        """
        logger.debug(f"HttpServer: {self.address_string()} - - {format % args}")

    def do_GET(self):
        try:
            if self.path == "/" or not self.path:
                # 重定向到默认文件
                self.path = "/index.html" if not conf.preference.geetest_localized else "/localized.html"
            elif self.path.startswith("/result"):
                # 接收验证结果
                params = parse.parse_qs(parse.urlparse(self.path).query)
                seccode = params.get("seccode")
                validate = params.get("validate")
                if not seccode or not validate:
                    logger.error(f"HTTP服务器 - 收到 {self.address_string()} 的验证结果，但URL参数缺少 seccode 和 validate")
                    self.send_error(400, "Bad request, missing URL params `seccode` and `validate`")
                else:
                    geetest_result = GeetestResult(seccode=seccode[0], validate=validate[0])
                    self.get_result(geetest_result)
                    response = {"code": 200, "message": "OK. Server received"}
                    self.send_response(200, response["message"])
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(json.dumps(response).encode())
                return

            # 构建文件路径
            file_path = STATIC_DIRECTORY / parse.urlparse(self.path).path[1:]

            # 检查文件是否存在并且可读
            if not os.path.isfile(file_path) or not os.access(file_path, os.R_OK):
                raise FileNotFoundError

            # 发送响应头
            self.send_response(200)
            self.send_header("Content-Type", self.guess_type(file_path))
            self.end_headers()

            # 发送文件内容
            with open(file_path, "rb") as file:
                self.wfile.write(file.read())

        except FileNotFoundError:
            logger.error(f"HTTP服务器 - 收到 {self.address_string()} 的请求，但请求文件不存在或不可读")
            logger.debug(traceback.format_exc())
            self.send_error(404)

        except:
            logger.error(f"HTTP服务器 - 收到 {self.address_string()} 的请求，但处理请求时发生错误")
            logger.debug(traceback.format_exc())
            self.send_error(500)


class GeetestServerThread(Thread):
    """
    后台启动GEETEST行为验证HTTP服务器的线程
    """

    def __init__(self):
        super().__init__()
        self.httpd: Optional[HTTPServer] = None

    @classmethod
    def __set_listen_address(cls):
        """
        设置HTTP服务器监听地址
        """
        if conf.preference.geetest_listen_address:
            if conf.preference.geetest_listen_address[1] == 0:
                __port = get_free_port(conf.preference.geetest_listen_address[0])
                return conf.preference.geetest_listen_address[0], __port
            else:
                return conf.preference.geetest_listen_address
        else:
            return "localhost", get_free_port()

    def run(self):
        try:
            listen_address = self.__set_listen_address()
            self.httpd = HTTPServer(listen_address, GeetestHandler)
            logger.info(
                f"HTTP服务器 - 监听地址：http://{listen_address[0]}:{listen_address[1]}")
            self.httpd.serve_forever()
        except:
            logger.error("HTTP服务器 - 启动失败")
            logger.debug(traceback.format_exc())

    def stop_server(self):
        """
        关闭HTTP服务器
        """
        self.httpd.shutdown()
        logger.info("HTTP服务器 - 已关闭")


def __get_result_demo(_: GeetestHandler, geetest_result: GeetestResult):
    """
    用于演示的验证结果处理函数

    :param _: GeetestHandler 实例
    :param geetest_result: 验证结果数据
    """
    logger.info(str(geetest_result))
