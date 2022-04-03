import os
import random
import time
import requests
import json
import platform
import configparser

def clear():
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

def goodTool():
    while True:
        print("> 请选择要查看的游戏：")
        print("-- 1. 崩坏3")
        print("-- 2. 原神")
        print("-- 3. 崩坏学园2")
        print("-- 4. 未定事件簿")
        print("-- 5. 米游社")
        print("\n-- 0. 返回功能选择界面")
        print("\n> ", end="")

        choice = input()
        clear()
        if choice == "1":
            GAME = "bh3"
        elif choice == "2":
            GAME = "hk4e"
        elif choice == "3":
            GAME = "bh2"
        elif choice == "4":
            GAME = "nxx"
        elif choice == "5":
            GAME = "bbs"
        elif choice == "0":
            return
        else:
            print("> 输入有误，请重新输入(回车以继续)\n")
            input()
            clear()
            continue

        retry_times = 0
        good_list = []
        page = 1
        url = "https://api-takumi.mihoyo.com/mall/v1/web/goods/list?app_id=1&point_sn=myb&page_size=20&page={page}&game={game}"

        while True:
            try:
                get_list = json.loads(
                    requests.get(url.format(page=page,
                                            game=GAME)).text)["data"]["list"]
                # 判断是否已经读完所有商品
                if get_list == []:
                    break
                else:
                    good_list += get_list
                page += 1
            except:
                retry_times += 1
                clear()
                print("> 请求失败，正在重试({times})...".format(times=retry_times))

        print("\n> 查询结果：")
        for good in good_list:
            # "next_time" 为 0 表示任何时间均可兑换或兑换已结束
            # "type" 为 1 时商品只有在指定时间开放兑换；为 0 时商品任何时间均可兑换
            if good["next_time"] == 0 and good["type"] == 1:
                continue

            print("----------")
            print("商品名称：{0}".format(good["goods_name"]))
            print("商品ID(Good_ID)：{0}".format(good["goods_id"]))
            print("商品价格：{0} 米游币".format(good["price"]))

            if good["type"] == 2:
                print("兑换时间：任何时间")
            elif good["type"] == 1:
                print("兑换时间：{0}".format(
                    time.strftime("%Y-%m-%d %H:%M:%S",
                                time.localtime(good["next_time"]))))
                print("库存：{0} 件".format(good["next_num"]))

            if good["account_cycle_type"] == "forever":
                print("限购：每人限购 {0}/{1}".format(good["account_exchange_num"], good["account_cycle_limit"]))
            elif good["account_cycle_type"] == "month":
                print("限购：本月限购 {0}/{1}".format(good["account_exchange_num"], good["account_cycle_limit"]))

            print("预览图：{0}".format(good["icon"]))

        print("\n> 请按回车返回上一页")
        input()
        clear()

def addressTool():
    conf = configparser.ConfigParser()
    conf.read("config.ini", encoding = "utf-8")
    cookie = conf.get("Config", "Cookie")
    headers = {
            "Host": "api-takumi.mihoyo.com",
            "Accept": "application/json, text/plain, */*",
            "Origin": "https://user.mihoyo.com",
            "Cookie": cookie,
            "Connection": "keep-alive",
            "x-rpc-device_id": "".join(random.sample('abcdefghijklmnopqrstuvwxyz0123456789', 32)).upper(),
            "x-rpc-client_type": "5",
            "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 15_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) miHoYoBBS/2.25.1",
            "Referer": "https://user.mihoyo.com/",
            "Accept-Language": "zh-CN,zh-Hans;q=0.9",
            "Accept-Encoding": "gzip, deflate, br"
        }
    url = "https://api-takumi.mihoyo.com/account/address/list?t={time_now}".format(time_now=round(time.time() * 1000))
    retry_times = 0

    while True:
        try:
            address_list = json.loads(requests.get(url, headers=headers).text)["data"]["list"]
            break
        except:
            retry_times += 1
            clear()
            print("> 请求失败，正在重试({times})...".format(times=retry_times))

    while True:
        print("\n> 查询结果：")
        for address in address_list:
            print("----------")
            print("省：{0}".format(address["province_name"]))
            print("市：{0}".format(address["city_name"]))
            print("区/县：{0}".format(address["county_name"]))
            print("详细地址：{0}".format(address["addr_ext"]))
            print("联系电话：{0}".format(address["connect_areacode"] + " " + address["connect_mobile"]))
            print("联系人：{0}".format(address["connect_name"]))
            print("地址ID(Address_ID)：{0}".format(address["id"]))

        print("\n> 请输入你要选择的地址ID(Address_ID)：")
        print("-- 注意：将对 config.ini 配置文件进行写入，文件中的注释和排版将被重置")
        print("-- 按回车键跳过并返回功能选择界面")
        try:
            print("> ", end="")
            choice = input()
            clear()
            if choice == "":
                break
            int(choice)
        except:
            print("> 输入有误，请重新输入(回车以继续)\n")
            input()
            clear()
            continue

        try:
            conf.set("Config", "Address_ID", choice)
            conf.write(open("config.ini", "w"))
            print("> 配置文件写入成功(回车以返回功能选择界面)")
            input()
            break
        except:
            print("> 配置文件写入失败(回车以返回)")
            input()
            clear()

while __name__ == '__main__':
    clear()
    print("> 选择功能：")
    print("-- 1. 查询商品ID(Good_ID)")
    print("-- 2. 查询送货地址ID(Address_ID)")
    print("\n-- 0. 退出")
    print("\n> ", end="")

    choice = input()
    clear()
    if choice == "1":
        goodTool()
    elif choice == "2":
        addressTool()
    elif choice == "0":
        exit(0)
    else:
        print("> 输入有误，请重新输入(回车以继续)\n")
        input()
