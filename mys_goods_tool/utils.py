import hashlib
import json
import os
import random
import string
import time
import uuid
from multiprocessing import Pool, pool
from socket import socket, AF_INET, SOCK_STREAM
from typing import Literal, Union, Dict, List, Any, Callable, Iterable, Optional
from urllib.parse import urlencode

import httpx
import ntplib
import tenacity
from loguru import logger
from pydantic import ValidationError

from mys_goods_tool.user_data import config as conf

LOG_FORMAT: str = (
    "<g>{time:MM-DD HH:mm:ss}</g> "
    "[<lvl>{level}</lvl>] "
    "<c><u>{name}</u></c> | "
    "{message}"
)
"""默认日志格式"""

logger.remove()
if conf.preference.log_path:
    logger.add(conf.preference.log_path, diagnose=True, format=LOG_FORMAT, level="DEBUG")


def custom_attempt_times(retry: bool):
    """
    自定义的重试机制停止条件\n
    根据是否要重试的bool值，给出相应的`tenacity.stop_after_attempt`对象

    :param retry: True - 重试次数达到偏好设置中 max_retry_times 时停止; False - 执行次数达到1时停止，即不进行重试
    """
    if retry:
        return tenacity.stop_after_attempt(
            conf.preference.max_retry_times + 1) if conf.preference.max_retry_times else tenacity.stop_after_attempt(1)
    else:
        return tenacity.stop_after_attempt(1)


def get_async_retry(retry: bool):
    """
    获取异步重试装饰器

    :param retry: True - 重试次数达到偏好设置中 max_retry_times 时停止; False - 执行次数达到1时停止，即不进行重试
    """
    return tenacity.AsyncRetrying(
        stop=custom_attempt_times(retry),
        retry=tenacity.retry_if_exception_type(BaseException),
        wait=tenacity.wait_fixed(conf.preference.retry_interval),
    )


class NtpTime:
    """
    NTP时间校准相关
    """
    time_offset = 0
    """本地时间与互联网时间的偏差"""

    @classmethod
    def sync(cls):
        """
        校准时间
        """
        if conf.preference.enable_ntp_sync:
            if not conf.preference.ntp_server:
                logger.error("开启了互联网时间校对，但未配置NTP服务器 preference.ntp_server，放弃时间同步")
                return False
            try:
                for attempt in get_async_retry(True):
                    with attempt:
                        cls.time_offset = ntplib.NTPClient().request(
                            conf.preference.ntp_server).tx_time - time.time()
            except tenacity.RetryError:
                logger.exception("校对互联网时间失败，改为使用本地时间")
                return False
            logger.info("互联网时间校对完成")
            return True
        else:
            logger.info("未开启互联网时间校对，跳过时间同步")
            return True

    @classmethod
    def time(cls) -> float:
        """
        获取校准后的时间（如果校准成功）
        """
        return time.time() + cls.time_offset


def generate_device_id() -> str:
    """
    生成随机的x-rpc-device_id
    """
    return str(uuid.uuid4()).upper()


def cookie_str_to_dict(cookie_str: str) -> Dict[str, str]:
    """
    将字符串Cookie转换为字典Cookie
    """
    cookie_str = cookie_str.replace(" ", "")
    # Cookie末尾缺少 ; 的情况
    if cookie_str[-1] != ";":
        cookie_str += ";"

    cookie_dict = {}
    start = 0
    while start != len(cookie_str):
        mid = cookie_str.find("=", start)
        end = cookie_str.find(";", mid)
        cookie_dict.setdefault(cookie_str[start:mid], cookie_str[mid + 1:end])
        start = end + 1
    return cookie_dict


def cookie_dict_to_str(cookie_dict: Dict[str, str]) -> str:
    """
    将字符串Cookie转换为字典Cookie
    """
    cookie_str = ""
    for key in cookie_dict:
        cookie_str += (key + "=" + cookie_dict[key] + ";")
    return cookie_str


def generate_ds(data: Union[str, dict, list, None] = None, params: Union[str, dict, None] = None,
                platform: Literal["ios", "android"] = "ios", salt: Optional[str] = None):
    """
    获取Headers中所需DS

    :param data: 可选，网络请求中需要发送的数据
    :param params: 可选，URL参数
    :param platform: 可选，平台，ios或android
    :param salt: 可选，自定义salt
    """
    if data is None and params is None or \
            salt is not None and salt != conf.salt_config.SALT_PROD:
        if platform == "ios":
            salt = salt or conf.salt_config.SALT_IOS
        else:
            salt = salt or conf.salt_config.SALT_ANDROID
        t = str(int(NtpTime.time()))
        a = "".join(random.sample(
            string.ascii_lowercase + string.digits, 6))
        re = hashlib.md5(
            f"salt={salt}&t={t}&r={a}".encode()).hexdigest()
        return f"{t},{a},{re}"
    else:
        if params:
            salt = conf.salt_config.SALT_PARAMS if not salt else salt
        else:
            salt = conf.salt_config.SALT_DATA if not salt else salt

        if not data:
            if salt == conf.salt_config.SALT_PROD:
                data = {}
            else:
                data = ""
        if not params:
            params = ""

        if not isinstance(data, str):
            data = json.dumps(data)
        if not isinstance(params, str):
            params = urlencode(params)

        t = str(int(time.time()))
        r = str(random.randint(100000, 200000))
        c = hashlib.md5(
            f"salt={salt}&t={t}&r={r}&b={data}&q={params}".encode()).hexdigest()
        return f"{t},{r},{c}"


def generate_seed_id(length: int = 8) -> str:
    """
    生成随机的 seed_id（即长度为8的十六进制数）

    :param length: 16进制数长度
    """
    max_num = int("FF" * length, 16)
    return hex(random.randint(0, max_num))[2:]


def generate_fp_locally(length: int = 13):
    """
    于本地生成 device_fp

    :param length: device_fp 长度
    """
    characters = string.digits + "abcdef"
    return ''.join(random.choices(characters, k=length))


async def get_file(url: str, retry: bool = True):
    """
    下载文件

    :param url: 文件URL
    :param retry: 是否允许重试
    :return: 文件数据
    """
    try:
        async for attempt in get_async_retry(retry):
            with attempt:
                async with httpx.AsyncClient() as client:
                    res = await client.get(url, timeout=conf.preference.timeout, follow_redirects=True)
                return res.content
    except tenacity.RetryError:
        logger.exception(f"下载文件 - {url} 失败")


PORT_RANGE = (1024, 49151)
"""
随机选择的端口所在范围

端口范围说明：https://www.rfc-editor.org/rfc/rfc6335.html#section-6
为何选择这个端口范围：https://www.rfc-editor.org/rfc/rfc6335.html#section-8.1.2
"""


def get_free_port(host: str = "localhost"):
    """
    在范围内随机获取一个空闲端口
    """
    used_port = set()
    while len(used_port) != PORT_RANGE[1] - PORT_RANGE[0] + 1:
        port = random.randint(PORT_RANGE[0], PORT_RANGE[1])
        with socket(AF_INET, SOCK_STREAM) as sock:
            res = sock.connect_ex((host, port))
            if res:
                return port
            else:
                used_port.add(port)
    logger.error("获取随机可用端口 - 未找到可用端口")
    return


class Subscribe:
    """
    在线配置相关(需实例化)
    """
    FILE_URL = "https://github.com/Ljzd-PRO/Mys_Goods_Tool/raw/dev/subscribe/configs.json"
    CONFIG_URL = os.path.join(conf.preference.github_proxy, FILE_URL) if conf.preference.github_proxy else FILE_URL
    conf_list: List[Dict[str, Any]] = []
    '''当前插件版本可用的配置资源'''

    def __init__(self):
        self.index = 0

    @classmethod
    async def download(cls) -> bool:
        """
        读取在线配置资源
        :return: 是否成功
        """
        try:
            for attempt in get_async_retry(True):
                with attempt:
                    file = await get_file(cls.CONFIG_URL)
                    file = json.loads(file.decode())
                    if not file:
                        return False
                    cls.conf_list = list(
                        filter(lambda co: ..., file))
                    cls.conf_list.sort(
                        key=lambda co: conf["time"], reverse=True)
                    return True
        except (json.JSONDecodeError, KeyError):
            logger.error(f"获取在线配置资源 - 解析文件失败")
            return False

    async def load(self, force: bool = False) -> bool:
        """
        优先加载来自网络的配置，若获取失败，则返回本地默认配置。\n
        若下载失败返回`False`

        :param force: 是否强制在线读取配置，而不使用本地缓存的
        """
        success = True
        if not Subscribe.conf_list or force or self.index >= len(Subscribe.conf_list):
            logger.info(f"读取配置 - 开始下载配置...")
            success = await self.download()
            self.index = 0
        if not success:
            return False
        else:
            try:
                conf.device_config.parse_obj(Subscribe.conf_list[self.index]["config"])
            except ValidationError:
                logger.exception(f"获取在线配置资源 - 加载配置失败")
                return False

            self.index += 1
            return True


class ProcessManager:
    """
    异步进程管理器
    """

    def __init__(self, callback: Optional[Callable] = None, error_callback: Optional[Callable] = None):
        """
        创建进程池，初始化异步进程管理器，包含进程池对象

        :param callback: 线程任务正常执行结束后的回调函数
        :param error_callback: 线程任务执行发生错误后的回调函数
        """
        self.pool: Optional[pool.Pool] = None
        """进程池"""
        self.callback = callback
        """线程任务正常执行结束后的回调函数"""
        self.error_callback = error_callback
        """线程任务执行发生错误后的回调函数"""

    def start(self, process_func: Callable, process_params: Iterable):
        """
        并启动线程任务
        """
        self.pool = Pool(1)
        self.pool.apply_async(process_func, process_params, callback=self.callback, error_callback=self.error_callback)
        self.pool.close()
