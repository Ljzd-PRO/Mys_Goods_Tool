import hashlib
import json
import random
import string
import traceback
import requests
import configparser
import os
import sys
import time
import platform
import ntplib
from ping3 import ping

# 网络请求的超时时间（商品和游戏账户详细信息查询）
TIME_OUT = 5
# 兑换商品时 Headers 所用的 User-Agent
USER_AGENT_EXCHANGE = "Mozilla/5.0 (iPhone; CPU iPhone OS 15_1 like Mac OS X) AppleWebKit/605.1.15 (KHtimeL, like Gecko) miHoYoBBS/2.14.1"
# 获取用户 ActionTicket 时Headers所用的 User-Agent
USER_AGENT_GET_ACTION_TICKET = "Hyperion/177 CFNetwork/1331.0.7 Darwin/21.4.0"
# Headers所用的 x-rpc-device_model
X_RPC_DEVICE_MODEL = "iPhone10,2"
# Headers所用的 x-rpc-app_version
X_RPC_APP_VERSION = "2.14.1"
# Headers所用的 x-rpc-sys_version
X_RPC_SYS_VERSION = "15.1"
# 失败后最多重试次数（不是商品兑换）
MAX_RETRY_TIMES = 5
# NTP服务器，用于获取网络时间
NTP_SERVER = "ntp.aliyun.com"


def clear() -> None:
    """
    清屏
    """
    plat = platform.system()
    if plat == "Darwin":
        os.system("clear")
    elif plat == "Windows":
        os.system("cls")
    elif plat == "Linux":
        os.system("clear")
    else:
        pass


def get_file_path(file_name: str = "") -> str:
    """
    获取文件绝对路径, 防止在某些情况下报错
    >>> file_name: str #文件名
    """
    return os.path.join(os.path.split(sys.argv[0])[0], file_name)


def to_log(info_type: str = "", title: str = "", info: str = "") -> str:
    """
    储存日志
    >>> info_type: str #日志的等级
    >>> title: str #日志的标题
    >>> info: str #日志的信息
    """
    if not os.path.exists(get_file_path("logs")):
        os.mkdir(get_file_path("logs/"))
    try:
        now = time.strftime("%Y-%m-%d %H:%M:%S",
                            time.localtime(NtpTime.time()))
    except KeyboardInterrupt:
        print(to_log("ERROR", "用户强制结束程序"))
        exit(1)
    except:
        now = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    log = now + "  " + info_type + "  " + title + "  " + info
    with open(get_file_path("logs/mys_goods_tool.log"), "a",
              encoding="utf-8") as log_a_file_io:
        log_a_file_io.write(log + "\n")
    return log


class NtpTime():
    """
    >>> NtpTime.time() #获取校准后的时间（如果校准成功）
    """
    ntp_error_times = 0
    time_offset = 0
    while True:
        print(to_log("INFO", "正在校对互联网时间"))
        try:
            time_offset = ntplib.NTPClient().request(
                NTP_SERVER).tx_time - time.time()
            break
        except KeyboardInterrupt:
            print(to_log("ERROR", "用户强制结束程序"))
            exit(1)
        except:
            ntp_error_times += 1
            if ntp_error_times == MAX_RETRY_TIMES:
                print(to_log("WARN", "校对互联网时间失败，改为使用本地时间"))
                break
            else:
                print(to_log("WARN", traceback.format_exc()))
                print(
                    to_log("WARN",
                           "校对互联网时间失败，正在重试({0})".format(ntp_error_times)))

    def time() -> float:
        """
        获取校准后的时间（如果校准成功）
        """
        return time.time() + NtpTime.time_offset


## 读取配置文件
conf = configparser.RawConfigParser()
conf.read(get_file_path("config.ini"), encoding="utf-8")


class Good:
    """
    商品兑换相关
    """
    global conf
    cookie = conf.get("Config", "Cookie").strip("\"").strip("'")
    stoken = conf.get("Config", "stoken").replace(" ", "")
    address = conf.get("Config", "Address_ID")
    uid = conf.get("Config", "UID")

    # 若 Cookie 中不存在stoken，且配置中 stoken 不为空，则进行字符串相加
    if stoken != "..." and stoken != "" and "stoken" not in cookie:
        cookie += ("stoken=" + stoken + ";")
    # 若 Cookie 中存在stoken，获取其中的stoken信息
    elif "stoken" in cookie:
        stoken = cookie.replace("=", "").replace(
            " ", "").split("stoken")[1].split(";")[0]
    else:
        stoken = None

    bbs_uid = ""
    if "ltuid" in cookie:
        bbs_uid = cookie.replace("=", "").replace(
            " ", "").split("ltuid")[1].split(";")[0]
    elif "account_id" in cookie:
        bbs_uid = cookie.replace("=", "").replace(
            " ", "").split("account_id")[1].split(";")[0]
    elif "stuid" in cookie:
        bbs_uid = cookie.replace("=", "").replace(
            " ", "").split("stuid")[1].split(";")[0]

    def get_DS():
        """
        获取Headers中所需DS
        """
        ## DS 加密算法:
        # 1. https://github.com/lhllhx/miyoubi/issues/3
        # 2. https://github.com/jianggaocheng/mihoyo-signin/blob/master/lib/mihoyoClient.js
        t = int(NtpTime.time())
        a = "".join(random.sample(string.ascii_lowercase + string.digits, 6))
        re = hashlib.md5(
            f"salt=b253c83ab2609b1b600eddfe974df47b&t={t}&r={a}".encode(
                encoding="utf-8")).hexdigest()
        return f"{t},{a},{re}"

    def __init__(self, id: str) -> None:
        """
        针对每个目标商品进行初始化
        >>> id: str #商品ID(Good_ID)
        """
        self.id = id
        self.result = None
        self.req = requests.Session()
        self.url = "https://api-takumi.mihoyo.com/mall/v1/web/goods/exchange"
        getActionTicket = "https://api-takumi.mihoyo.com/auth/api/getActionTicketBySToken?action_type=game_role&stoken={stoken}&uid={bbs_uid}".format(
            stoken=Good.stoken, bbs_uid=Good.bbs_uid)
        checkGame = "https://api-takumi.mihoyo.com/binding/api/getUserGameRoles?point_sn=myb&action_ticket={actionTicket}&game_biz={game_biz}"
        checkGood = "https://api-takumi.mihoyo.com/mall/v1/web/goods/detail?app_id=1&point_sn=myb&goods_id={0}".format(
            self.id)
        self.data = {
            "app_id": 1,
            "point_sn": "myb",
            "goods_id": self.id,
            "exchange_num": 1,
            "address_id": Good.address
        }
        self.headers = {
            "Accept":
            "application/json, text/plain, */*",
            "Accept-Encoding":
            "gzip, deflate, br",
            "Accept-Language":
            "zh-CN,zh-Hans;q=0.9",
            "Connection":
            "keep-alive",
            "Content-Type":
            "application/json;charset=utf-8",
            "Cookie":
            Good.cookie,
            "Host":
            "api-takumi.mihoyo.com",
            "User-Agent":
            USER_AGENT_EXCHANGE,
            "x-rpc-app_version":
            X_RPC_APP_VERSION,
            "x-rpc-channel":
            "appstore",
            "x-rpc-client_type":
            "1",
            "x-rpc-device_id":
            "".join(random.sample(string.ascii_letters + string.digits,
                                  32)).upper(),
            "x-rpc-device_model":
            X_RPC_DEVICE_MODEL,
            "x-rpc-device_name":
            "".join(
                random.sample(string.ascii_letters + string.digits,
                              random.randrange(5))).upper(),
            "x-rpc-sys_version":
            X_RPC_SYS_VERSION
        }

        while True:
            try:
                print(to_log("INFO", "正在检查商品：{0} 的详细信息".format(self.id)))
                checkGood_data = json.loads(
                    self.req.get(checkGood, timeout=TIME_OUT).text)["data"]
                if checkGood_data == None:
                    print(
                        to_log("ERROR",
                               "无法找到商品：{0} 的信息，放弃兑换该商品".format(self.id)))
                    self.result = -1
                    return
                elif checkGood_data["type"] == 2:
                    if "stoken" not in Good.cookie:
                        print(
                            to_log(
                                "ERROR",
                                "商品：{0} 为游戏内物品，由于未配置 stoken，放弃兑换该商品".format(
                                    self.id)))
                        self.result = -1
                        return
                # 若商品非游戏内物品，则直接返回，不进行下面的操作
                else:
                    self.headers.setdefault("Content-Length", "88")
                    return
                break
            except KeyboardInterrupt:
                print(to_log("ERROR", "用户强制结束程序"))
                exit(1)
            except:
                print(to_log("ERROR", traceback.format_exc()))
                print(to_log("ERROR", "检查商品：{0} 失败，正在重试".format(self.id)))
                continue

        error_times = 0
        while True:
            try:
                print(to_log("INFO", "正在获取用户ActionTicket"))
                getActionTicket_headers = self.headers.copy()
                getActionTicket_headers[
                    "User-Agent"] = USER_AGENT_GET_ACTION_TICKET
                getActionTicket_headers.setdefault("DS", Good.get_DS())
                getActionTicket_req = self.req.get(
                    getActionTicket,
                    headers=getActionTicket_headers,
                    timeout=TIME_OUT)
                actionTicket = json.loads(
                    getActionTicket_req.text)["data"]["ticket"]
                break
            except KeyboardInterrupt:
                print(to_log("ERROR", "用户强制结束程序"))
                exit(1)
            except:
                error_times += 1
                if error_times == MAX_RETRY_TIMES:
                    print(
                        to_log(
                            "ERROR",
                            "商品：{0} 为游戏内物品，由于获取用户ActionTicket失败，放弃兑换该商品".
                            format(self.id)))
                    self.result = -1
                    return
                print(to_log("ERROR", traceback.format_exc()))
                print(
                    to_log("ERROR",
                           "获取用户ActionTicket失败，正在重试({0})".format(error_times)))
                continue

        game_biz = checkGood_data["game_biz"]
        error_times = 0
        while True:
            try:
                print(to_log("INFO", "正在检查游戏账户：{0} 的详细信息".format(Good.uid)))
                user_list = json.loads(
                    self.req.get(checkGame.format(actionTicket=actionTicket,
                                                  game_biz=game_biz),
                                 headers=self.headers,
                                 timeout=TIME_OUT).text)["data"]["list"]
                break
            except KeyboardInterrupt:
                print(to_log("ERROR", "用户强制结束程序"))
                exit(1)
            except:
                error_times += 1
                if error_times == MAX_RETRY_TIMES:
                    print(
                        to_log(
                            "ERROR",
                            "商品：{0} 为游戏内物品，由于获取用户ActionTicket失败，放弃兑换该商品".
                            format(self.id)))
                    self.result = -1
                    return
                print(to_log("ERROR", traceback.format_exc()))
                print(
                    to_log(
                        "ERROR", "检查游戏账户：{0} 失败，正在重试({1})".format(
                            Good.uid, error_times)))
                continue

        for user in user_list:
            if user["game_biz"] == game_biz and user["game_uid"] == Good.uid:
                self.data.setdefault("uid", Good.uid)
                self.data.setdefault("region", user["region"])
                self.data.setdefault("game_biz", game_biz)

        self.headers.setdefault("Content-Length", "88")

    def start(self) -> None:
        """
        执行兑换操作
        """
        if self.result == -1:
            print(to_log("WARN", "商品：{0} 未初始化完成，放弃兑换".format(self.id)))
            return
        self.req = requests.Session()
        while True:
            try:
                self.result = self.req.post(self.url,
                                            headers=self.headers,
                                            json=self.data)
            except KeyboardInterrupt:
                print(to_log("ERROR", "用户强制结束程序"))
                exit(1)
            except:
                print(to_log("ERROR", traceback.format_exc()))
                print(to_log("ERROR", "兑换商品：{0} 失败，正在重试".format(self.id)))
                continue
            print(
                to_log(
                    "INFO",
                    "兑换商品：{0} 返回结果：\n{1}\n".format(self.id, self.result.text)))
            break


## 检测运行环境（Windows与macOS清屏指令不同）
system = platform.system()

## 将配置文件中目标商品ID读入列表
good_list = conf.get("Config", "Good_ID")
good_list = good_list.replace(" ", "")
good_list = good_list.split(",")

## 初始化每个目标商品ID的对象
queue = []
for id in good_list:
    queue.append(Good(id))


class CheckNetwork:
    """
    检查网络连接和显示剩余时间
    """
    global conf

    timeUp_Str = conf.get("Config", "Time")  # 获取配置文件中的兑换开始时间
    checkTime = conf.get("Preference", "Check_Time")  # 每隔多久检查一次网络连接情况
    stopCheck = conf.get("Preference", "Stop_Check")  # 距离开始兑换还剩多久停止检查网络
    isCheck = conf.get("Preference", "Check_Network")  # 是否自动检测网络连接情况

    checkTime = int(checkTime)
    stopCheck = int(stopCheck)
    isCheck = int(isCheck)

    timeUp = time.mktime(time.strptime(timeUp_Str, "%Y-%m-%d %H:%M:%S"))

    lastCheck = 0  # 上一次检测网络连接情况的时间
    result = -1  # 上一次的检测结果
    isTimeUp = False  # 是否接近兑换时间
    ip = 'api-takumi.mihoyo.com'

    def __init__(self) -> None:
        if CheckNetwork.isTimeUp == False and CheckNetwork.isCheck == True:  # 若配置文件设置为要进行网络检查，才进行检查
            if CheckNetwork.timeUp - NtpTime.time(
            ) < CheckNetwork.stopCheck:  # 若剩余时间不到30秒，停止之后的网络检查
                CheckNetwork.isTimeUp = True

            if (
                    NtpTime.time() - CheckNetwork.lastCheck
            ) >= CheckNetwork.checkTime and CheckNetwork.isTimeUp == False:  # 每隔10秒检测一次网络连接情况
                print("正在检查网络连接...")
                CheckNetwork.result = ping(CheckNetwork.ip)
                CheckNetwork.lastCheck = NtpTime.time()
                print("\n")
                if CheckNetwork.result == None:
                    print(to_log("WARN", "检测到网络连接异常！\n"))
                else:
                    CheckNetwork.result = CheckNetwork.result * 1000
                    print(
                        to_log(
                            "INFO", "网络连接正常，延时 {0} ms\n".format(
                                round(CheckNetwork.result, 2))))


def timeStampToStr(timeStamp: float = NtpTime.time()) -> str:
    """
    时间戳转字符串时间（无传入参数则返回当前时间）
    >>> timeStamp: float #时间戳
    """
    return time.strftime("%H:%M:%S", time.localtime(timeStamp))


temp_time = 0
while __name__ == '__main__':
    if NtpTime.time() >= CheckNetwork.timeUp:  # 执行兑换操作
        for task in queue:
            task.start()
        break

    elif int(NtpTime.time()) != int(temp_time):  # 每隔一秒刷新一次
        clear()

        print("当前时间：", timeStampToStr(), "\n")
        if CheckNetwork.isCheck == True:
            CheckNetwork()
            clear()
            print("当前时间：", timeStampToStr(), "\n")

            if CheckNetwork.result != -1:  # 排除初始化值
                if CheckNetwork.result == None or CheckNetwork.result == 0:
                    print("{0} - 检测到网络连接异常！\n".format(
                        timeStampToStr(CheckNetwork.lastCheck)))
                else:
                    print("{0} - 网络连接正常，延时 {1} ms\n".format(
                        timeStampToStr(CheckNetwork.lastCheck),
                        round(CheckNetwork.result, 2)))

        print("距离兑换开始还剩：{0} 小时 {1} 分 {2} 秒".format(
            int((CheckNetwork.timeUp - NtpTime.time()) / 3600),
            int((CheckNetwork.timeUp - NtpTime.time()) % 3600 / 60),
            int((CheckNetwork.timeUp - NtpTime.time()) % 60)))

        temp_time = NtpTime.time()
