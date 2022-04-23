import json
import random
import requests
import configparser
import os
import sys
import time
import platform
from ping3 import ping

# 网络请求的超时时间（商品和游戏账户详细信息查询）
TIME_OUT = 5

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


## 获取程序运行目录绝对路径
def get_file_path(file_name: str = "") -> str:
    """
    获取文件绝对路径, 防止在某些情况下报错
    file_name: 文件名
    """
    return os.path.join(os.path.split(sys.argv[0])[0], file_name)


## 储存日志
def to_log(info_type: str = "", title: str = "", info: str = "") -> str:
    """
    info_type: 日志的等级
    title: 日志的标题
    info: 日志的信息
    """
    if not os.path.exists(get_file_path("logs")):
        os.mkdir(get_file_path("logs/"))
    now = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    log = now + "  " + info_type + "  " + title + "  " + info
    with open(get_file_path("logs/mys_goods_tool.log"), "a",
              encoding="utf-8") as log_a_file_io:
        log_a_file_io.write(log + "\n")
    return log

## 读取配置文件
conf = configparser.RawConfigParser()
conf.read(get_file_path("config.ini"), encoding="utf-8")

## 商品兑换相关
class Good:
    global conf
    cookie = conf.get("Config", "Cookie").strip("\"").strip("'")
    stoken = conf.get("Config", "stoken")
    address = conf.get("Config", "Address_ID")
    uid = conf.get("Config", "UID")

    if stoken == "...":
        stoken = ""
    else:
        cookie += ("stoken=" + stoken + ";")

    def __init__(self, id: str) -> None:
        self.id = id
        self.result = None
        self.req = None
        self.url = "https://api-takumi.mihoyo.com/mall/v1/web/goods/exchange"
        checkGame = "https://api-takumi.mihoyo.com/binding/api/getUserGameRolesByStoken"
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
            "Content-Length":
            "88",
            "Content-Type":
            "application/json;charset=utf-8",
            "Cookie":
            Good.cookie,
            "Host":
            "api-takumi.mihoyo.com",
            "Origin":
            "https://webstatic.mihoyo.com",
            "Referer":
            "https://webstatic.mihoyo.com/",
            "User-Agent":
            "Mozilla/5.0 (iPhone; CPU iPhone OS 15_1 like Mac OS X) AppleWebKit/605.1.15 (KHtimeL, like Gecko) miHoYoBBS/2.14.1",
            "x-rpc-app_version":
            "2.14.1",
            "x-rpc-channel":
            "appstore",
            "x-rpc-client_type":
            "1",
            "x-rpc-device_id":
            "".join(random.sample('abcdefghijklmnopqrstuvwxyz0123456789',
                                  32)).upper(),
            "x-rpc-device_model":
            "iPhone10,2",
            "x-rpc-device_name":
            "".join(
                random.sample('abcdefghijklmnopqrstuvwxyz0123456789',
                              random.randrange(5))).upper(),
            "x-rpc-sys_version":
            "15.1"
        }

        while True:
            try:
                print(to_log("INFO", "正在检查商品：{0} 的详细信息".format(self.id)))
                checkGood_data = json.loads(
                    requests.get(checkGood, timeout=TIME_OUT).text)["data"]
                break
            except:
                print(to_log("ERROR", "检查商品：{0} 服务器连接失败，正在重试".format(self.id)))
                continue

        if checkGood_data["type"] == 2:
            game_biz = checkGood_data["game_biz"]
            while True:
                try:
                    print(to_log("INFO",
                                 "正在检查游戏账户：{0} 的详细信息".format(Good.uid)))
                    user_list = json.loads(
                        requests.get(checkGame,
                                     headers=self.headers,
                                     timeout=TIME_OUT).text)["data"]["list"]
                    break
                except:
                    print(
                        to_log("ERROR",
                               "检查游戏账户：{0} 服务器连接失败，正在重试".format(Good.uid)))
                    continue
            for user in user_list:
                if user["game_biz"] == game_biz and user[
                        "game_uid"] == Good.uid:
                    self.data.setdefault("uid", Good.uid)
                    self.data.setdefault("region", user["region"])
                    self.data.setdefault("game_biz", game_biz)


    def start(self) -> None:
        self.req = requests.Session()
        while True:
            try:
                self.result = self.req.post(self.url,
                                            headers=self.headers,
                                            json=self.data)
            except:
                print(to_log("INFO", "兑换商品：{0} 服务器连接失败，正在重试".format(self.id)))
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

## 检查网络连接和显示剩余时间
class CheckNetwork:
    global conf

    timeUp_Str = conf.get("Config", "Time")
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
            if CheckNetwork.timeUp - time.time() < CheckNetwork.stopCheck:  # 若剩余时间不到30秒，停止之后的网络检查
                CheckNetwork.isTimeUp = True

            if (
                    time.time() - CheckNetwork.lastCheck
            ) >= CheckNetwork.checkTime and CheckNetwork.isTimeUp == False:  # 每隔10秒检测一次网络连接情况
                print("正在检查网络连接...")
                CheckNetwork.result = ping(CheckNetwork.ip)
                CheckNetwork.lastCheck = time.time()
                print("\n")
                if CheckNetwork.result == None:
                    print(to_log("ERROR", "检测到网络连接异常！\n"))
                else:
                    CheckNetwork.result = CheckNetwork.result * 1000
                    print(
                        to_log(
                            "INFO", "网络连接正常，延时 {0} ms\n".format(
                                round(CheckNetwork.result, 2))))


# 时间戳转字符串时间（无传入参数则返回当前时间）
def timeStampToStr(timeStamp: float = None) -> str:
    return time.strftime("%H:%M:%S", time.localtime(timeStamp))

temp_time = 0
while __name__ == '__main__':
    if time.time() >= CheckNetwork.timeUp:  # 执行兑换操作
        for task in queue:
            task.start()
        break

    elif int(time.time()) != int(temp_time):  # 每隔一秒刷新一次
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
            int((CheckNetwork.timeUp - time.time()) / 3600),
            int((CheckNetwork.timeUp - time.time()) / 60),
            int((CheckNetwork.timeUp - time.time()) % 60)))

        temp_time = time.time()
