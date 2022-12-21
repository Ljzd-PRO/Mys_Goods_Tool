# coding=utf-8

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
import copy
import threading
import uuid
from ping3 import ping

VERSION = "v1.4.3-beta"
"""程序当前版本"""
TIME_OUT = 5
"""网络请求的超时时间（商品和游戏账户详细信息查询）"""
USER_AGENT_EXCHANGE = "Mozilla/5.0 (iPhone; CPU iPhone OS 15_1 like Mac OS X) AppleWebKit/605.1.15 (KHtimeL, like Gecko) miHoYoBBS/2.36.1"
"""兑换商品时 Headers 所用的 User-Agent"""
USER_AGENT_GET_ACTION_TICKET = "Hyperion/177 CFNetwork/1331.0.7 Darwin/21.4.0"
"""获取用户 ActionTicket 时Headers所用的 User-Agent"""
X_RPC_DEVICE_MODEL = "iPhone10,2"
"""Headers所用的 x-rpc-device_model"""
X_RPC_APP_VERSION = "2.36.1"
"""Headers所用的 x-rpc-app_version"""
X_RPC_SYS_VERSION = "15.1"
"""Headers所用的 x-rpc-sys_version"""
MAX_RETRY_TIMES = 5
"""失败后最多重试次数（不是商品兑换）"""
NTP_SERVER = "ntp.aliyun.com"
"""NTP服务器，用于获取网络时间"""

if __name__ != "__main__":
    exit(0)


# 清屏指令
PLATFORM = platform.system()
if PLATFORM == "Darwin":
    CLEAR_COMMAND = "clear"
elif PLATFORM == "Windows":
    CLEAR_COMMAND = "cls"
elif PLATFORM == "Linux":
    CLEAR_COMMAND = "clear"
else:
    CLEAR_COMMAND = None


def clear() -> None:
    """
    清屏
    """
    if CLEAR_COMMAND != None:
        os.system(CLEAR_COMMAND)


def get_file_path(file_name: str = "") -> str:
    """
    获取文件绝对路径, 防止在某些情况下报错
    >>> file_name: str #文件名
    """
    return os.path.join(os.path.split(sys.argv[0])[0], file_name)


def to_log(info_type: str = "", info: str = "") -> str:
    """
    储存日志
    >>> info_type: str #日志的等级
    >>> info: str #日志的信息
    """
    try:
        if not os.path.exists(get_file_path("logs")):
            os.mkdir(get_file_path("logs/"))
        try:
            now = time.strftime("%Y-%m-%d %H:%M:%S",
                                time.localtime(NtpTime.time()))
        except KeyboardInterrupt:
            print(to_log("WARN", "用户强制结束程序"))
            exit(1)
        except:
            now = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        log = now + "  " + info_type + "  " + info
        with open(get_file_path("logs/mys_goods_tool.log"), "a",
                  encoding="utf-8") as log_a_file_io:
            log_a_file_io.write(log + "\n")
        return log
    except KeyboardInterrupt:
        print(to_log("WARN", "用户强制结束程序"))
        exit(1)
    except:
        print("日志输出失败")
        traceback.print_exc()


def generateDeviceID() -> str:
    """
    生成随机的x-rpc-device_id
    """
    return str(uuid.uuid4()).upper()


print(to_log("程序当前版本: {}".format(VERSION)))


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
            print(to_log("WARN", "用户强制结束程序"))
            exit(1)
        except:
            ntp_error_times += 1
            if ntp_error_times == MAX_RETRY_TIMES:
                print(to_log("WARN", "校对互联网时间失败，改为使用本地时间"))
                to_log("WARN", traceback.format_exc())
                break
            else:
                print(
                    to_log("WARN",
                           "校对互联网时间失败，正在重试({})".format(ntp_error_times)))
                to_log("WARN", traceback.format_exc())

    def time() -> float:
        """
        获取校准后的时间（如果校准成功）
        """
        return time.time() + NtpTime.time_offset


# 读取配置文件
try:
    conf = configparser.RawConfigParser()
    try:
        conf.read(get_file_path("config.ini"), encoding="utf-8")
    except:
        conf.read(get_file_path("config.ini"), encoding="utf-8-sig")
except KeyboardInterrupt:
    print(to_log("WARN", "用户强制结束程序"))
    exit(1)
except:
    print(to_log("ERROR", "读取配置文件失败"))
    to_log("ERROR", traceback.format_exc())
    exit(1)


class Good:
    """
    商品兑换相关
    """
    # 记录已成功兑换的商品
    success_task = []

    def findCookieInStr(target: str, cookiesStr: str, location: int = None) -> str:
        """
        在Raw原始模式下的Cookies字符串中查找所需要的Cookie
        >>> target: str #查找目标
        >>> cookiesStr: str #Raw Cookies 字符串
        >>> location: int #目标Cookie字符串所在位置，若为None则自动查找
        >>> return str #返回目标Cookie对应的值
        """
        if location is None:
            location = cookiesStr.find(target)
        return cookiesStr[cookiesStr.find(
            "=", location) + 1: cookiesStr.find(";", location)]

    global conf
    try:
        cookie = conf.get("Config", "Cookie").replace(
            " ", "").strip("\"").strip("'")
        address = conf.get("Config", "Address_ID")
        try:
            stoken = conf.get("Config", "stoken").replace(
                " ", "").strip("\"").strip("'")
        except configparser.NoOptionError:
            stoken = ""
        try:
            uid = conf.get("Config", "UID")
        except configparser.NoOptionError:
            uid = ""
    except KeyboardInterrupt:
        print(to_log("WARN", "用户强制结束程序"))
        exit(1)
    except:
        print(to_log("ERROR", "从配置文件中读取[Config]失败，可能是没有正确配置"))
        to_log("ERROR", traceback.format_exc())
        exit(1)

    try:
        # 若 Cookie 中不存在stoken，且配置中 stoken 不为空，则进行字符串相加
        location = cookie.find("stoken")
        if stoken != "..." and stoken != "" and location == -1:
            cookie += ("stoken=" + stoken + ";")
        # 若 Cookie 中存在stoken，获取其中的stoken信息
        elif location != -1:
            stoken = findCookieInStr("stoken", cookie, location)
        else:
            stoken = None

        # 从 Cookie 中获取游戏UID
        bbs_uid = findCookieInStr("ltuid", cookie)
        for target in ("ltuid", "account_id", "stuid"):
            bbs_uid = findCookieInStr(target, cookie)
            if bbs_uid != "":
                break
    except KeyboardInterrupt:
        print(to_log("WARN", "用户强制结束程序"))
        exit(1)
    except:
        print(to_log("ERROR", "处理配置信息失败"))
        to_log("ERROR", traceback.format_exc())
        exit(1)

    def get_DS():
        try:
            """
            获取Headers中所需DS
            """
            # DS 加密算法:
            # 1. https://github.com/lhllhx/miyoubi/issues/3
            # 2. https://github.com/jianggaocheng/mihoyo-signin/blob/master/lib/mihoyoClient.js
            t = int(NtpTime.time())
            a = "".join(random.sample(
                string.ascii_lowercase + string.digits, 6))
            re = hashlib.md5(
                f"salt=b253c83ab2609b1b600eddfe974df47b&t={t}&r={a}".encode(
                    encoding="utf-8")).hexdigest()
            return f"{t},{a},{re}"
        except KeyboardInterrupt:
            print(to_log("WARN", "用户强制结束程序"))
            exit(1)
        except:
            print(to_log("ERROR", "生成Headers所需DS失败"))
            to_log("ERROR", traceback.format_exc())
            raise

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
        checkGood = "https://api-takumi.mihoyo.com/mall/v1/web/goods/detail?app_id=1&point_sn=myb&goods_id={}".format(
            self.id)
        self.data = {
            "app_id": 1,
            "point_sn": "myb",
            "goods_id": self.id,
            "exchange_num": 1,
            "address_id": Good.address
        }
        try:
            if int(Good.address):
                self.data.setdefault("address_id", Good.address)
        except:
            pass
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
            "x-rpc-device_id": generateDeviceID(),
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
                print(to_log("INFO", "正在检查商品：{} 的详细信息".format(self.id)))
                checkGood_data = json.loads(
                    self.req.get(checkGood, timeout=TIME_OUT).text)["data"]
                if checkGood_data is None:
                    print(
                        to_log("ERROR",
                               "无法找到商品：{} 的信息，放弃兑换该商品".format(self.id)))
                    self.result = -1
                    return
                elif checkGood_data["type"] == 2 and checkGood_data["game_biz"] != "bbs_cn":
                    if Good.cookie.find("stoken") == -1:
                        print(
                            to_log(
                                "ERROR",
                                "商品：{} 为游戏内物品，由于未配置 stoken，放弃兑换该商品".format(
                                    self.id)))
                        self.result = -1
                        return
                    if Good.stoken.find("v2__") == 0 and Good.cookie.find("mid") == -1:
                        print(
                            to_log(
                                "ERROR",
                                "商品：{} 为游戏内物品，由于stoken为\"v2\"类型，且未配置mid，放弃兑换该商品".format(
                                    self.id)))
                        self.result = -1
                        return
                # 若商品非游戏内物品，则直接返回，不进行下面的操作
                else:
                    return
                break
            except KeyboardInterrupt:
                print(to_log("WARN", "用户强制结束程序"))
                exit(1)
            except:
                print(to_log("ERROR", "检查商品：{} 失败，正在重试".format(self.id)))
                to_log("ERROR", traceback.format_exc())
                continue

        error_times = 0
        while True:
            try:
                print(to_log("INFO", "正在获取用户ActionTicket"))
                getActionTicket_headers = self.headers.copy()
                getActionTicket_headers[
                    "User-Agent"] = USER_AGENT_GET_ACTION_TICKET
                try:
                    getActionTicket_headers.setdefault("DS", Good.get_DS())
                except:
                    print(to_log("ERROR", "初始化商品兑换任务失败，放弃兑换"))
                    to_log("ERROR", traceback.format_exc())
                    self.result = -1
                    return
                getActionTicket_req = self.req.get(
                    getActionTicket,
                    headers=getActionTicket_headers,
                    timeout=TIME_OUT)
                getActionTicket_res = json.loads(
                    getActionTicket_req.text)
                actionTicket = getActionTicket_res["data"]["ticket"]
                break
            except KeyboardInterrupt:
                print(to_log("WARN", "用户强制结束程序"))
                exit(1)
            except:
                error_times += 1
                if error_times == MAX_RETRY_TIMES:
                    print(
                        to_log(
                            "ERROR",
                            "商品：{} 为游戏内物品，由于获取用户ActionTicket失败，放弃兑换该商品".
                            format(self.id)))
                    self.result = -1
                    return
                print(
                    to_log("ERROR",
                           "获取用户ActionTicket失败，正在重试({})".format(error_times)))
                try:
                    print("获取ActionTicket返回: {}".format(
                        getActionTicket_res["message"]))
                except:
                    pass
                to_log("ERROR", traceback.format_exc())
                to_log("DEBUG", "getActionTicket_url: {}".format(
                    getActionTicket))
                to_log("DEBUG", "getActionTicket_headers: {}".format(
                    getActionTicket_headers))
                try:
                    to_log("DEBUG", "getActionTicket_response: {}".format(
                        getActionTicket_res))
                except:
                    pass
                continue

        game_biz = checkGood_data["game_biz"]
        error_times = 0
        while True:
            try:
                print(to_log("INFO", "正在检查游戏账户：{} 的详细信息".format(Good.uid)))
                checkGame_url = checkGame.format(actionTicket=actionTicket, game_biz=game_biz)
                res = self.req.get(checkGame_url,
                                 headers=self.headers,
                                 timeout=TIME_OUT).text
                user_list = json.loads(res)["data"]["list"]
                break
            except KeyboardInterrupt:
                print(to_log("WARN", "用户强制结束程序"))
                exit(1)
            except:
                error_times += 1
                if error_times == MAX_RETRY_TIMES:
                    print(
                        to_log(
                            "ERROR",
                            "商品：{} 为游戏内物品，由于检查游戏账户失败，放弃兑换该商品".
                            format(self.id)))
                    self.result = -1
                    return
                print(
                    to_log(
                        "ERROR", "检查游戏账户：{0} 失败，正在重试({1})".format(
                            Good.uid, error_times)))
                to_log("DEBUG", "checkGame_url: " + checkGame_url)
                to_log("DEBUG", "checkGame_response: " + res)
                to_log("ERROR", traceback.format_exc())
                continue

        for user in user_list:
            if user["game_biz"] == game_biz and user["game_uid"] == Good.uid:
                self.data.setdefault("uid", Good.uid)
                self.data.setdefault("region", user["region"])
                self.data.setdefault("game_biz", game_biz)


    def start(self) -> None:
        """
        执行兑换操作
        """
        if self.result == -1:
            print(to_log("WARN", "商品：{} 未初始化完成，放弃兑换".format(self.id)))
            return
        self.req = requests.Session()
        while True:
            try:
                print(to_log("INFO", "开始发送商品 {} 的兑换请求...".format(self.id)))
                self.result = self.req.post(self.url,
                                            headers=self.headers,
                                            json=self.data)
            except KeyboardInterrupt:
                print(to_log("WARN", "用户强制结束程序"))
                exit(1)
            except:
                print(to_log("ERROR", "兑换商品：{} 失败，正在重试".format(self.id)))
                to_log("ERROR", traceback.format_exc())
                continue
            print(
                to_log(
                    "INFO",
                    "兑换商品：{0} 返回结果：\n{1}\n".format(self.id, self.result.text)))
            try:
                if json.loads(self.result.text)["message"] == "OK" or self.id in Good.success_task:
                    print(to_log("INFO", "商品 {} 兑换成功！可以自行确认。".format(self.id)))
                    if self.id not in Good.success_task:
                        Good.success_task.append(self.id)
                else:
                    print(to_log("INFO", "商品 {} 兑换失败，可以自行确认。".format(self.id)))
            except KeyboardInterrupt:
                print(to_log("WARN", "用户强制结束程序"))
                exit(1)
            except:
                pass
            self.result = 1
            break


# 检测运行环境（Windows与macOS清屏指令不同）
system = platform.system()

# 将配置文件中目标商品ID读入列表
try:
    good_list = conf.get("Config", "Good_ID")
except KeyboardInterrupt:
    print(to_log("WARN", "用户强制结束程序"))
    exit(1)
except:
    print(to_log("ERROR", "从配置文件中读取商品ID失败，可能是没有正确配置"))
    to_log("ERROR", traceback.format_exc())
    exit(1)
try:
    good_list = good_list.replace(" ", "")
    good_list = good_list.split(",")
except KeyboardInterrupt:
    print(to_log("WARN", "用户强制结束程序"))
    exit(1)
except:
    print(to_log("ERROR", "处理配置信息失败"))
    to_log("ERROR", traceback.format_exc())
    exit(1)
# 初始化每个目标商品ID的对象
tasks = []
for id in good_list:
    tasks.append(Good(id))


class CheckNetwork:
    """
    检查网络连接和显示剩余时间
    """
    global conf
    try:
        try:
            timeUp_Str = conf.get("Config", "Time")  # 获取配置文件中的兑换开始时间
            timeUp = time.mktime(time.strptime(
                timeUp_Str, "%Y-%m-%d %H:%M:%S"))

        except KeyboardInterrupt:
            print(to_log("WARN", "用户强制结束程序"))
            exit(1)
        except:
            print(to_log("ERROR", "读取配置文件中兑换时间失败，可能是没有正确配置"))
            to_log("ERROR", traceback.format_exc())
            exit(1)
        checkTime = conf.get("Preference", "Check_Time")  # 每隔多久检查一次网络连接情况
        stopCheck = conf.get("Preference", "Stop_Check")  # 距离开始兑换还剩多久停止检查网络
        isCheck = conf.get("Preference", "Check_Network")  # 是否自动检测网络连接情况
    except KeyboardInterrupt:
        print(to_log("WARN", "用户强制结束程序"))
        exit(1)
    except:
        print(to_log("ERROR", "从配置文件中读取[Preference]失败，可能是没有正确配置"))
        to_log("ERROR", traceback.format_exc())
        checkTime = 0
        stopCheck = 0
        isCheck = 0

    isCheck = int(isCheck)
    if isCheck:
        try:
            checkTime = int(checkTime)
            stopCheck = int(stopCheck)
            lastCheck = 0  # 上一次检测网络连接情况的时间
            result = -1  # 上一次的检测结果
            isTimeUp = False  # 是否接近兑换时间
            ip = 'api-takumi.mihoyo.com'
        except KeyboardInterrupt:
            print(to_log("WARN", "用户强制结束程序"))
            exit(1)
        except:
            print(to_log("WARN", "无法进行网络检查"))
            isCheck = 0

    def __init__(self) -> None:
        try:
            if not CheckNetwork.isTimeUp and CheckNetwork.isCheck:  # 若配置文件设置为要进行网络检查，才进行检查
                if CheckNetwork.timeUp - NtpTime.time(
                ) < CheckNetwork.stopCheck:  # 若剩余时间不到30秒，停止之后的网络检查
                    CheckNetwork.isTimeUp = True

                if (
                        NtpTime.time() - CheckNetwork.lastCheck
                ) >= CheckNetwork.checkTime and not CheckNetwork.isTimeUp:  # 每隔10秒检测一次网络连接情况
                    print("正在检查网络连接...", end="")
                    CheckNetwork.result = ping(CheckNetwork.ip)
                    CheckNetwork.lastCheck = NtpTime.time()
                    if CheckNetwork.result is None:
                        to_log("WARN", "检测到网络连接异常！")
                    else:
                        CheckNetwork.result = CheckNetwork.result * 1000
                        to_log(
                            "INFO", "网络连接正常，延时 {} ms".format(
                                    round(CheckNetwork.result, 2)))
        except KeyboardInterrupt:
            print(to_log("WARN", "用户强制结束程序"))
            exit(1)
        except:
            print(to_log("WARN", "执行网络检查失败"))


def timeStampToStr(timeStamp: float = None) -> str:
    """
    时间戳转字符串时间（无传入参数则返回当前时间）
    >>> timeStamp: float #时间戳
    """
    if timeStamp is None:
        timeStamp = NtpTime.time()
    return time.strftime("%H:%M:%S", time.localtime(timeStamp))


# 读取线程数
try:
    thread_num = int(conf.get("Preference", "Thread"))
except:
    print(to_log("WARN", "读取配置文件中的[Preference]-Thread 线程数失败"))
    thread_num = 3

# 为每个兑换任务增加多个线程
queue = []
tasks_copy = []
for task in tasks:
    queue.append(threading.Thread(target=task.start))
    for num in range(0, thread_num - 1):
        task_copy = copy.deepcopy(task)
        tasks_copy.append(task_copy)
        queue.append(threading.Thread(target=task_copy.start))

temp_time = 0
while True:
    try:
        if NtpTime.time() >= CheckNetwork.timeUp:  # 执行兑换操作
            for task in queue:
                task.start()

            # 当检测到所有的线程都结束时，finished为True，跳出循环
            finished = False
            while not finished:
                finished = True
                for task in queue:
                    if task.is_alive():
                        finished = False
                        break
            break

        elif int(NtpTime.time()) != int(temp_time):  # 每隔一秒刷新一次
            clear()

            print("当前时间：", timeStampToStr(), "\n")
            if CheckNetwork.isCheck:
                CheckNetwork()
                if CheckNetwork.result != -1:  # 排除初始化值

                    if CheckNetwork.result is None or CheckNetwork.result == 0:
                        print("\r{} - 检测到网络连接异常！\n".format(
                            timeStampToStr(CheckNetwork.lastCheck)))
                    else:
                        print("\r{0} - 网络连接正常，延时 {1} ms\n".format(
                            timeStampToStr(CheckNetwork.lastCheck),
                            round(CheckNetwork.result, 2)))

            print("距离兑换开始还剩：{0} 小时 {1} 分 {2} 秒".format(
                int((CheckNetwork.timeUp - NtpTime.time()) / 3600),
                int((CheckNetwork.timeUp - NtpTime.time()) % 3600 / 60),
                int((CheckNetwork.timeUp - NtpTime.time()) % 60)))

            temp_time = NtpTime.time()
    except KeyboardInterrupt:
        print(to_log("WARN", "用户强制结束程序"))
        exit(1)
    except:
        print(to_log("ERROR", "主程序出现错误"))
        to_log("ERROR", traceback.format_exc())

to_log("INFO", "程序运行结束")
input("程序运行结束，按下回车键以关闭...")
