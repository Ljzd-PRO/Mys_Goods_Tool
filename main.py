import requests
import configparser
import os
import sys
import time as tm
import platform
from ping3 import ping

def get_file_path(file_name=""):
    """
    获取文件绝对路径, 防止在某些情况下报错
    file_name: 文件名
    """
    return os.path.join(os.path.split(sys.argv[0])[0], file_name)

def to_log(info_type="", title="", info=""):
    """
    info_type: 日志的等级
    title: 日志的标题
    info: 日志的信息
    """
    if not os.path.exists(get_file_path("logs")):
        os.mkdir(get_file_path("logs/"))
    now = tm.strftime("%Y-%m-%d %H:%M:%S", tm.localtime())
    log = now + "  " + info_type + "  " + title + "  " + info
    with open(get_file_path("logs/mys_goods_tool.log"), "a", encoding="utf-8") as log_a_file_io:
        log_a_file_io.write(log + "\n")
    return log

## 读取配置文件
conf = configparser.ConfigParser()
conf.read(get_file_path("config.ini"))
time = conf.get("Config", "Time")

## 商品兑换相关
class Good:
    global conf
    cookie = conf.get("Config", "Cookie")
    address = conf.get("Config", "Address_ID")

    def __init__(self, id):
        self.id = id
        self.result = None
        self.req = None
        self.url = "https://api-takumi.mihoyo.com/mall/v1/web/goods/exchange"
        self.data = {
        "app_id": 1,
        "point_sn": "myb",
        "goods_id": id,
        "exchange_num": 1,
        "address_id": Good.address
        }
        self.headers = {
        "Accept": "application/json, text/plain, */*",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "zh-CN,zh-Hans;q=0.9",
        "Connection": "keep-alive",
        "Content-Length": "88",
        "Content-Type": "application/json;charset=utf-8",
        "Cookie": Good.cookie,
        "Host": "api-takumi.mihoyo.com",
        "Origin": "https://webstatic.mihoyo.com",
        "Referer": "https://webstatic.mihoyo.com/",
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 15_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) miHoYoBBS/2.14.1","x-rpc-app_version": "2.14.1",
        "x-rpc-channel": "appstore",
        "x-rpc-client_type": "1",
        "x-rpc-device_id": "35543DDE-7C18-4584-BF4B-51217D3C8670",
        "x-rpc-device_model": "iPhone10,2",
        "x-rpc-device_name": "%E4%B8%A4%E6%B1%9F%E6%80%BB%E7%9D%A3",
        "x-rpc-sys_version": "15.1"
        }

    def start(self):
        self.req = requests.Session()
        try:
            self.result = self.req.post(self.url, headers=self.headers, json=self.data)
        except:
            print(to_log("INFO", "兑换商品：\n{0}\n服务器连接失败，正在重试\n".format(self.id)))
            self.start()
        print(to_log("INFO", "兑换商品\n{0}\n返回结果：\n{1}\n".format(self.id, self.result.text)))


## 检测运行环境（Windows与macOS清屏指令不同）
system = platform.system().lower()


## 将配置文件中目标商品ID读入列表
good_list = conf.get("Config", "Good_ID")
good_list = good_list.replace(" ", "")
good_list = good_list.split(",")

## 初始化每个目标商品ID的对象
num = 0
for id in good_list:
    num += 1
    locals()["good_" + str(num)] = Good(id)

## 检查网络连接和显示剩余时间
class CheckNetwork:
    global conf
    global time

    checkTime = conf.get("Preference", "Check_Time")    # 每隔多久检查一次网络连接情况
    stopCheck = conf.get("Preference", "Stop_Check")    # 距离开始兑换还剩多久停止检查网络
    isCheck = conf.get("Preference", "Check_Network")   # 是否自动检测网络连接情况

    checkTime = int(checkTime)
    stopCheck = int(stopCheck)
    isCheck = int(isCheck)

    timeUp = time.split(":")
    timeUp = int(timeUp[0]) * 3600 + int(timeUp[1]) * 60 + int(timeUp[2])   # 兑换开始时间（不带:）
    lastCheck = 0   # 上一次检测网络连接情况的时间（不带:）
    lastCheckTime = ""  # 上一次检测网络连接情况的时间
    result = None   # 上一次的检测结果
    isTimeUp = False    # 是否接近兑换时间
    ip = 'api.mihoyo.com'

    def __init__(self, time_now):
        if (CheckNetwork.isTimeUp == False) and (CheckNetwork.isCheck == True):    # 若配置文件设置为要进行网络检查，才进行检查
            self.time_now = time_now.split(":")
            self.time_now = int(self.time_now[0]) * 3600 + int(self.time_now[1]) * 60 + int(self.time_now[2])  # 当前时间
            self.time_remian = CheckNetwork.timeUp - self.time_now

            if self.time_remian < CheckNetwork.stopCheck:    # 若剩余时间不到30秒，停止之后的网络检查
                CheckNetwork.isTimeUp == True

            else:
                self.time_H = self.time_remian // 3600
                self.time_M = (self.time_remian % 3600) // 60
                self.time_S = (self.time_remian % 3600) % 60
                print("距离兑换开始还剩：{0} 小时 {1} 分 {2} 秒".format(self.time_H, self.time_M, self.time_S))

            if (self.time_now - CheckNetwork.lastCheck) >= CheckNetwork.checkTime:  # 每隔10秒检测一次网络连接情况
                CheckNetwork.result = ping(CheckNetwork.ip)
                print("\n")
                if CheckNetwork.result == None:
                    print(to_log("ERROR", "检测到网络连接异常！\n"))
                    CheckNetwork.resultTime = self.time_now
                    CheckNetwork.lastCheckTime = time_now
                else:
                    CheckNetwork.result = CheckNetwork.result * 1000
                    print(to_log("INFO", "网络连接正常，延时 {0} ms\n".format(CheckNetwork.result)))
                    CheckNetwork.lastCheck = self.time_now
                    CheckNetwork.lastCheckTime = time_now

time_now = None
while True:
    temp = time_now
    time_now = tm.strftime("%H:%M:%S", tm.localtime())  # 获取当前时间

    if time_now == time:    # 执行兑换操作
        for i in range(1, num+1):
            locals()["good_" + str(i)].start()
        break

    elif time_now != temp:  # 显示当前时间
        if system == "windows":
            os.system("cls")
        elif system == "darwin":
            os.system("clear")

        print("当前时间：", time_now, "\n")
        if CheckNetwork.result == None:
            pass
        elif CheckNetwork.result == 0:
            print("{0} - 检测到网络连接异常！\n".format(CheckNetwork.lastCheckTime))
        else:
            print("{0} - 网络连接正常，延时 {1} ms\n".format(CheckNetwork.lastCheckTime, round(CheckNetwork.result, 2)))
        CheckNetwork(time_now)
