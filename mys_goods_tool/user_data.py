import os
import sys
import traceback
from pathlib import Path
from typing import List, Union, Optional, Tuple

from loguru import logger
from pydantic import BaseModel, Extra, ValidationError

ROOT_PATH = Path(sys.argv[0]).parent.absolute()
"""程序所在目录"""

if len(sys.argv) == 4 or len(sys.argv) == 2:
    CONFIG_PATH = sys.argv[-1]
else:
    CONFIG_PATH = ROOT_PATH / "config.json"
    """配置文件默认路径"""


class DeviceConfig(BaseModel, extra=Extra.ignore):
    """
    设备信息
    DS算法与设备信息有关联，非必要请勿修改
    """
    USER_AGENT_MOBILE: str = "Mozilla/5.0 (iPhone; CPU iPhone OS 15_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) miHoYoBBS/2.42.1"
    '''移动端 User-Agent(Mozilla UA)'''
    USER_AGENT_PC: str = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Safari/605.1.15"
    '''桌面端 User-Agent(Mozilla UA)'''
    USER_AGENT_OTHER: str = "Hyperion/275 CFNetwork/1402.0.8 Darwin/22.2.0"
    '''获取用户 ActionTicket 时Headers所用的 User-Agent'''
    USER_AGENT_ANDROID: str = "Mozilla/5.0 (Linux; Android 11; MI 8 SE Build/RQ3A.211001.001; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/104.0.5112.97 Mobile Safari/537.36 miHoYoBBS/2.36.1"
    '''安卓端 User-Agent(Mozilla UA)'''
    USER_AGENT_ANDROID_OTHER: str = "okhttp/4.9.3"
    '''安卓端 User-Agent(专用于米游币任务等)'''
    USER_AGENT_WIDGET: str = "WidgetExtension/231 CFNetwork/1390 Darwin/22.0.0"
    '''iOS 小组件 User-Agent(原神实时便笺)'''

    X_RPC_DEVICE_MODEL_MOBILE: str = "iPhone10,2"
    '''移动端 x-rpc-device_model'''
    X_RPC_DEVICE_MODEL_PC: str = "OS X 10.15.7"
    '''桌面端 x-rpc-device_model'''
    X_RPC_DEVICE_MODEL_ANDROID: str = "MI 8 SE"
    '''安卓端 x-rpc-device_model'''

    X_RPC_DEVICE_NAME_MOBILE: str = "iPhone"
    '''移动端 x-rpc-device_name'''
    X_RPC_DEVICE_NAME_PC: str = "Microsoft Edge 103.0.1264.62"
    '''桌面端 x-rpc-device_name'''
    X_RPC_DEVICE_NAME_ANDROID: str = "Xiaomi MI 8 SE"
    '''安卓端 x-rpc-device_name'''

    X_RPC_SYS_VERSION: str = "15.4"
    '''Headers所用的 x-rpc-sys_version'''
    X_RPC_SYS_VERSION_ANDROID: str = "11"
    '''安卓端 x-rpc-sys_version'''

    X_RPC_CHANNEL: str = "appstore"
    '''Headers所用的 x-rpc-channel'''
    X_RPC_CHANNEL_ANDROID: str = "miyousheluodi"
    '''安卓端 x-rpc-channel'''

    X_RPC_APP_VERSION: str = "2.28.1"
    '''Headers所用的 x-rpc-app_version'''
    X_RPC_PLATFORM: str = "ios"
    '''Headers所用的 x-rpc-platform'''
    UA: str = "\".Not/A)Brand\";v=\"99\", \"Microsoft Edge\";v=\"103\", \"Chromium\";v=\"103\""
    '''Headers所用的 sec-ch-ua'''
    UA_PLATFORM: str = "\"macOS\""
    '''Headers所用的 sec-ch-ua-platform'''


class BBSCookies(BaseModel):
    """
    米游社Cookies数据
    """
    stuid: Optional[str]
    """米游社UID"""
    ltuid: Optional[str]
    """米游社UID"""
    account_id: Optional[str]
    """米游社UID"""
    stoken: Optional[str]
    cookie_token: Optional[str]
    login_ticket: Optional[str]
    mid: Optional[str]

    @property
    def is_correct(self) -> bool:
        """判断是否为正确的Cookies"""
        if (self.stuid or self.ltuid or self.account_id) and self.stoken and self.cookie_token:
            return True
        else:
            return False

    @property
    def bbs_uid(self):
        """
        获取米游社UID
        """
        uid = None
        for value in [self.stuid, self.ltuid, self.account_id]:
            if value:
                uid = value
                break
        return uid if uid else None


class UserAccount(BaseModel, extra=Extra.ignore):
    """
    米游社账户数据
    """
    phone_number: Optional[int]
    """手机号"""
    cookies: BBSCookies
    """Cookies"""
    device_id_ios = str
    """iOS设备用 deviceID"""
    device_id_android: str
    """安卓设备用 deviceID"""

    @property
    def bbs_uid(self):
        """
        获取米游社UID
        """
        return self.cookies.bbs_uid


class ExchangePlan(BaseModel, extra=Extra.ignore):
    """
    兑换计划数据类
    """
    good_id: int
    """商品ID"""
    address_id: int
    """地址ID"""
    account: Union[UserAccount, int]
    """米游社账号（可为UserAccount账号数据 或 账号数据在Config.accounts中的位置）"""
    game_uid: Optional[int]
    """商品对应的游戏的玩家账户UID"""


class Preference(BaseModel, extra=Extra.ignore):
    """
    偏好设置
    """
    github_proxy: Optional[str] = "https://ghproxy.com/"
    """GitHub加速代理"""
    enable_connection_test: bool = True
    """是否开启连接测试"""
    connection_test_interval: Optional[float] = 30
    """连接测试间隔（单位：秒）"""
    timeout: Optional[float] = 10
    """网络请求超时时间（单位：秒）"""
    max_retry_times: Optional[int] = 3
    """最大网络请求重试次数"""
    retry_interval: float = 2
    """网络请求重试间隔（单位：秒）（除兑换请求外）"""
    enable_ntp_sync: bool = True
    """是否开启NTP时间同步（将调整实际发出兑换请求的时间，而不是修改系统时间）"""
    ntp_server: Optional[str] = "ntp.aliyun.com"
    """NTP服务器地址"""
    geetest_localized: bool = False
    """登录时使用的 GEETEST行为验证 WEB服务 加载本地JS资源"""
    geetest_listen_address: Optional[Tuple[str, int]] = ("localhost", 0)
    """登录时使用的 GEETEST行为验证 WEB服务 本地监听地址"""
    exchange_thread_count: int = 3
    """兑换线程数"""
    exchange_thread_interval: float = 0.05
    """每个兑换线程之间等待的时间间隔（单位：秒）"""
    exchange_latency: float = 0.03
    """兑换时间延迟（单位：秒）（防止因为发出请求的时间过于精准而被服务器认定为非人工操作）"""
    enable_log_output: bool = True
    """是否保存日志"""
    log_path: Path = ROOT_PATH / "logs" / "mys_goods_tool.log"
    """日志保存路径"""


class Config(BaseModel, extra=Extra.ignore):
    """
    配置类
    """
    exchange_plans: List[ExchangePlan] = []
    """兑换计划列表"""
    preference: Preference = Preference()
    """偏好设置"""
    device_config: DeviceConfig = DeviceConfig()
    """设备信息"""
    accounts: List[UserAccount] = []
    """储存一些已绑定的账号数据"""


def write_config_file(conf: Config = Config()):
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        f.write(conf.json(indent=4))


config = Config()
if os.path.isfile(CONFIG_PATH):
    try:
        config = Config.parse_file(CONFIG_PATH)
    except ValidationError:
        logger.error(f"读取配置文件失败，请检查配置文件 {CONFIG_PATH} 格式是否正确。")
        logger.debug(traceback.format_exc())
        exit(1)
    except:
        logger.error(f"读取配置文件失败，请检查配置文件 {CONFIG_PATH} 是否存在且程序有权限读取和写入。")
        logger.debug(traceback.format_exc())
        exit(1)
else:
    write_config_file(config)
    logger.info(f"配置文件 {CONFIG_PATH} 不存在，已创建默认配置文件。")
