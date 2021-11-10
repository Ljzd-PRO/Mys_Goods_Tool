import requests
import configparser
import os
import sys
import time as tm
import platform

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

## 商品兑换相关
class Good:
    def __init__(self, cookie, id, address):
        self.id = id
        self.address = address
        self.cookie = cookie
        self.result = None
        self.req = None
        self.url = "https://api-takumi.mihoyo.com/mall/v1/web/goods/exchange"
        self.data = {
        "app_id": 1,
        "point_sn": "myb",
        "goods_id": id,
        "exchange_num": 1,
        "address_id": address
        }
        self.headers = {
        "Accept": "application/json, text/plain, */*",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "zh-CN,zh-Hans;q=0.9",
        "Connection": "keep-alive",
        "Content-Length": "88",
        "Content-Type": "application/json;charset=utf-8",
        "Cookie": cookie,
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
            print(to_log("兑换商品：\n{0}\n服务器连接失败，正在重试\n".format(self.id)))
            self.start()
        print(to_log("兑换商品：\n{0}\n返回结果：\n{1}\n".format(self.id, self.result.text)))

## 检测运行环境（Windows与macOS清屏指令不同）
system = platform.system().lower()

## 读取配置文件
conf = configparser.ConfigParser()
conf.read(get_file_path("config.ini"))

cookie = conf.get("Config", "Cookie")
address = conf.get("Config", "Address_ID")
time = conf.get("Config", "Time")

## 将配置文件中目标商品ID读入列表
good_list = conf.get("Config", "Good_ID")
good_list = good_list.replace(" ", "")
good_list = good_list.split(",")

## 初始化每个目标商品ID的对象
num = 0
for id in good_list:
    num += 1
    locals()["good_" + str(num)] = Good(cookie, id, address)

time_now = None
while True:
    temp = time_now
    time_now = tm.strftime("%H:%M:%S", tm.localtime())

    if time_now == time:    # 执行兑换操作
        for i in range(1, num+1):
            locals()["good_" + str(i)].start()
        break

    elif time_now != temp:  # 显示当前时间
        if system == "windows":
            os.system("cls")
        if system == "darwin":
            os.system("clear")
        print("当前时间：", time_now, "\n")
