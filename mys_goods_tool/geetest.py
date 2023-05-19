import asyncio
import json
import os
import threading
import traceback
from http.server import HTTPServer, ThreadingHTTPServer, CGIHTTPRequestHandler
from json import JSONDecodeError
from multiprocessing import Pipe, Manager, connection
from pathlib import Path
from queue import Queue
from threading import Thread
from typing import Any, Optional, Callable, Tuple, Union
from urllib import parse

from pydantic import ValidationError

from mys_goods_tool.data_model import GeetestResult, GeetestResultV4
from mys_goods_tool.user_data import config as conf
from mys_goods_tool.utils import logger, get_free_port, ProcessManager

STATIC_DIRECTORY = Path(__file__).resolve().with_name(
    "geetest-webui") if not conf.preference.geetest_statics_path else conf.preference.geetest_statics_path


class GeetestHandler(CGIHTTPRequestHandler):
    result_callback: Callable[[Union[GeetestResult, GeetestResultV4]], Any]
    """接收验证结果数据的回调函数"""
    error_content_type = "application/json"

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

    def response_ok(self):
        response = {"code": 200, "message": "OK. Server received"}
        self.send_response(200, response["message"])
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(response).encode())

    def send_error(self, code: int, message: str = None, explain: str = None, to_json: bool = False) -> None:
        """
        重写父类方法，返回json格式的错误信息
        """
        if to_json:
            self.send_response(code, message)
            self.send_header("Content-Type", self.error_content_type)
            self.end_headers()
            response = {"code": code, "msg": message, "desc": explain}
            self.wfile.write(json.dumps(response).encode())
        else:
            super().send_error(code, message, explain)

    def do_GET(self):
        file_path = self.path
        try:
            if self.path == "/" or not self.path:
                # 重定向到默认文件
                self.path = "/index.html"
            elif self.path.startswith("/result"):
                # 接收验证结果
                params = parse.parse_qs(parse.urlparse(self.path).query)
                seccode = params.get("seccode")
                validate = params.get("validate")
                if not seccode or not validate:
                    logger.error(
                        f"HTTP服务器 - 收到 {self.address_string()} 的验证结果，但URL参数缺少 seccode 和 validate")
                    self.send_error(400, "Bad request, missing URL params `seccode` and `validate`", to_json=True)
                else:
                    geetest_result = GeetestResult(seccode=seccode[0], validate=validate[0])
                    logger.info(f"HTTP服务器 - 收到 {self.address_string()} 的验证结果 - {geetest_result}")
                    self.result_callback(geetest_result)
                    self.response_ok()
                return

            # 构建文件路径
            file_path = STATIC_DIRECTORY / parse.urlparse(self.path).path[1:]

            # 检查文件是否存在并且可读
            if not os.path.isfile(file_path):
                raise FileNotFoundError(f"文件 {file_path} 不存在")
            if not os.access(file_path, os.R_OK):
                raise FileNotFoundError(f"文件 {file_path} 不可读")

            # 发送响应头
            self.send_response(200)
            self.send_header("Content-Type", self.guess_type(file_path))
            self.end_headers()

            # 发送文件内容
            with open(file_path, "rb") as file:
                self.wfile.write(file.read())
        except FileNotFoundError:
            logger.warning(f"HTTP服务器 - 收到 {self.address_string()} 的请求，但请求文件 {file_path} 不存在或不可读")
            logger.debug(traceback.format_exc())
            self.send_error(404)
        except Exception:
            logger.error(f"HTTP服务器 - 收到 {self.address_string()} 的请求，但处理请求时发生错误")
            logger.debug(traceback.format_exc())
            self.send_error(500)

    def do_POST(self) -> None:
        if self.path.startswith("/result"):
            try:
                content_length = int(self.headers["Content-Length"])
                geetest_result = GeetestResultV4.parse_raw(self.rfile.read(content_length))
            except (ValidationError, JSONDecodeError):
                logger.exception(
                    f"HTTP服务器 - 收到 {self.address_string()} 的 gt4 验证结果，但传入数据不符合 GeetestResultV4 模型")
                self.send_error(400, "Bad request, data not match GeetestResultV4 model", to_json=True)
            else:
                logger.info(f"HTTP服务器 - 收到 {self.address_string()} 的 gt4 验证结果")
                self.result_callback(geetest_result)
                self.response_ok()


def set_listen_address():
    """
    设置HTTP服务器监听地址
    """
    if conf.preference.geetest_listen_address:
        if conf.preference.geetest_listen_address[1] == 0:
            port = get_free_port(conf.preference.geetest_listen_address[0])
            if port is None:
                return
            else:
                return conf.preference.geetest_listen_address[0], port
        else:
            return conf.preference.geetest_listen_address
    else:
        port = get_free_port()
        if port is None:
            return
        else:
            return "localhost", get_free_port()


class GeetestProcess:
    """
    GEETEST行为验证HTTP服务器 进程相关
    （可被pickle序列化的对象类型有限，给该类引入新的数据时需要注意）
    """
    httpd: ThreadingHTTPServer
    """GEETEST行为验证HTTP服务器实例"""
    pipe: Tuple[connection.Connection]
    """进程间通信管道，用于终止HTTP服务器"""
    geetest_result_queue: Queue[GeetestResult]
    """由Manager管理的验证结果数据"""
    wait_thread: Thread

    @classmethod
    def result_callback(cls, result: Union[GeetestResult, GeetestResultV4]):
        """
        给主进程发送验证结果
        """
        cls.geetest_result_queue.put(result)

    @classmethod
    def wait_until_stop(cls):
        connection.wait([cls.pipe[0]])
        cls.httpd.shutdown()
        logger.info(f"HTTP服务器 - 运行于 {cls.httpd.server_address} 的服务器已停止")

    @classmethod
    def run(cls, listen_address: Tuple[str, int], pipe: Tuple[connection.Connection],
            geetest_result_queue: Queue[GeetestResult]):
        """
        进程所执行的任务，被阻塞（启动HTTP服务器）

        :param listen_address HTTP服务器监听地址
        :param pipe 进程间通信管道，用于终止HTTP服务器
        :param geetest_result_queue 由Manager管理的验证结果数据
        """
        cls.pipe = pipe
        cls.geetest_result_queue = geetest_result_queue
        GeetestHandler.result_callback = cls.result_callback
        cls.httpd = ThreadingHTTPServer(listen_address, GeetestHandler)
        cls.wait_thread = threading.Thread(target=cls.wait_until_stop, daemon=True)
        cls.wait_thread.start()
        logger.info(
            f"HTTP服务器 - 监听地址：http://{listen_address[0]}:{listen_address[1]}")
        cls.httpd.serve_forever()


class GeetestProcessManager(ProcessManager):
    """
    异步GEETEST验证服务器，包含进程池对象
    """

    def __init__(self, listen_address: Tuple[str, int], httpd_close_callback: Optional[Callable] = None,
                 error_httpd_callback: Optional[Callable] = None):
        """
        创建进程池，初始化异步GEETEST验证服务器，包含进程池对象

        :param listen_address: HTTP服务器监听地址
        :param httpd_close_callback: HTTP服务器正常结束后的回调函数
        :param error_httpd_callback: HTTP服务器发生错误后的回调函数
        """
        self.listen_address = listen_address
        self.pipe: Tuple[connection.Connection] = Pipe(duplex=False)
        self.result_queue: Queue[GeetestResult] = Manager().Queue()

        super().__init__(httpd_close_callback, error_httpd_callback)

    def start(self, *_):
        """
        启动HTTP服务器
        """
        super().start(GeetestProcess.run, [self.listen_address, self.pipe, self.result_queue])

    async def force_stop_later(self, delay: float):
        """
        延迟一段时间后强制停止HTTP服务器
        """
        asyncio.get_event_loop().call_later(delay, self.pool.terminate)


class SetAddressProcessManager(ProcessManager):
    def start(self, *_):
        """
        开始寻找可用的地址
        """
        super().start(set_listen_address, [])


class GeetestServerThread(Thread):
    """
    后台启动GEETEST行为验证HTTP服务器的线程
    """

    def __init__(self):
        super().__init__()
        self.httpd: Optional[HTTPServer] = None

    def run(self):
        try:
            listen_address = set_listen_address()
            self.httpd = HTTPServer(listen_address, GeetestHandler)
            logger.info(
                f"HTTP服务器 - 监听地址：http://{listen_address[0]}:{listen_address[1]}")
            self.httpd.serve_forever()
        except Exception:
            logger.error("HTTP服务器 - 启动失败")
            logger.debug(traceback.format_exc())

    def stop_server(self):
        """
        关闭HTTP服务器
        """
        self.httpd.shutdown()
        logger.info(f"HTTP服务器 - 运行于 {self.httpd.server_address} 的服务器已停止")


def __get_result_demo(_: GeetestHandler, geetest_result: GeetestResult):
    """
    用于演示的验证结果处理函数

    :param _: GeetestHandler 实例
    :param geetest_result: 验证结果数据
    """
    logger.info(str(geetest_result))
