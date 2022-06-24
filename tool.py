# coding=utf-8

import os
import random
import time
import requests
import json
import platform
import configparser


# 当前版本
VERSION = "v1.2.2"
# 所需要的Cookie
COOKIES_NEEDED = [
    "stuid", "stoken", "ltoken", "ltuid", "account_id", "cookie_token",
    "login_ticket"
]
# Headers所需要的 User-Agent
USER_AGENT = "Mozilla/5.0 (iPhone; CPU iPhone OS 15_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) miHoYoBBS/2.25.1"


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


def goodTool() -> None:
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
            print("> 输入有误，请重新输入(回车以返回)\n")
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
            except KeyboardInterrupt:
                print("用户强制结束程序...")
                exit(1)
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

            if good["type"] != 1 and good["next_time"] == 0:
                print("兑换时间：任何时间")
            elif good["type"] != 1 and good["next_num"] == 0:
                print("库存：无限")
            else:
                print("兑换时间：{0}".format(
                    time.strftime("%Y-%m-%d %H:%M:%S",
                                  time.localtime(good["next_time"]))))
                print("库存：{0} 件".format(good["next_num"]))

            if good["account_cycle_type"] == "forever":
                print("限购：每人限购 {0}/{1}".format(good["account_exchange_num"],
                                               good["account_cycle_limit"]))
            elif good["account_cycle_type"] == "month":
                print("限购：本月限购 {0}/{1}".format(good["account_exchange_num"],
                                               good["account_cycle_limit"]))

            print("预览图：{0}".format(good["icon"]))

        print("\n> 请按回车返回上一页")
        input()
        clear()


def addressTool() -> None:
    conf = configparser.RawConfigParser()
    try:
        conf.read_file(open("config.ini", encoding="utf-8"))
        cookie = conf.get(
            "Config",
            "Cookie").strip("'''").strip("'").strip("\"\"\"").strip("\"")
    except KeyboardInterrupt:
        print("用户强制结束程序...")
        exit(1)
    except:
        print("> 读取Cookie失败，请手动输入Cookie信息：(返回上一页请直接回车)")
        print("> ", end="")
        cookie_input = input()
        if cookie_input != "":
            cookie = cookie_input.strip("'''").strip("'").strip(
                "\"\"\"").strip("\"")
            clear()
        else:
            clear()
            return

    headers = {
        "Host":
        "api-takumi.mihoyo.com",
        "Accept":
        "application/json, text/plain, */*",
        "Origin":
        "https://user.mihoyo.com",
        "Cookie":
        cookie,
        "Connection":
        "keep-alive",
        "x-rpc-device_id":
        "".join(random.sample('abcdefghijklmnopqrstuvwxyz0123456789',
                              32)).upper(),
        "x-rpc-client_type":
        "5",
        "User-Agent":
        USER_AGENT,
        "Referer":
        "https://user.mihoyo.com/",
        "Accept-Language":
        "zh-CN,zh-Hans;q=0.9",
        "Accept-Encoding":
        "gzip, deflate, br"
    }
    url = "https://api-takumi.mihoyo.com/account/address/list?t={time_now}".format(
        time_now=round(time.time() * 1000))
    retry_times = 0

    while True:
        try:
            address_list = json.loads(requests.get(
                url, headers=headers).text)["data"]["list"]
            break
        except KeyboardInterrupt:
            print("用户强制结束程序...")
            exit(1)
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
            print("联系电话：{0}".format(address["connect_areacode"] + " " +
                                    address["connect_mobile"]))
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
        except KeyboardInterrupt:
            print("用户强制结束程序...")
            exit(1)
        except:
            print("> 输入有误，请重新输入(回车以返回)\n")
            input()
            clear()
            continue

        try:
            conf.set("Config", "Address_ID", choice)
            with open("config.ini", "w", encoding="utf-8") as config_file:
                conf.write(config_file)
            print("> 配置文件写入成功(回车以返回功能选择界面)")
            input()
            break
        except KeyboardInterrupt:
            print("用户强制结束程序...")
            exit(1)
        except:
            print("> 配置文件写入失败(回车以返回)")
            input()
            clear()


def cookieTool() -> None:
    strip_char = ["'", "\"", " "]
    replace_char = [("\:", ":"), ("\ ", " "), ("\~", "~")]

    # 查找结果
    cookies = {}

    print("> 请选择抓包导出文件类型：")
    print("- (1) 使用 HttpCanary 导出的文件夹")
    print("- (2) .har 文件")
    print("\n> ", end="")
    choice = input()
    clear()
    if choice == "1":
        print("> 请输入 HttpCanary 导出文件夹路径：")
        print("\n> ", end="")
        file_path = input()
        clear()

        # 去除两边自动添加的无关符号
        for char in strip_char:
            if not os.path.isdir(file_path):
                file_path = file_path.strip(char)
            else:
                break
        # 替换自动添加的无关符号
        for chars in replace_char:
            if not os.path.isdir(file_path):
                file_path = file_path.replace(chars[0], chars[1])
            else:
                break

        try:
            req_dirs = os.listdir(file_path)
            for req_dir in req_dirs:
                if os.path.isfile(req_dir):
                    continue
                file_data = json.load(
                    open(os.path.join(file_path, req_dir, "request.json"), "r"))
                print("> 开始分析抓包数据")
                try:
                    file_cookies = file_data["headers"]["Cookie"]
                except KeyError:
                    try:
                        file_cookies = file_data["headers"]["cookie"]
                    except KeyError:
                        continue
                for cookie_needed in COOKIES_NEEDED:
                    if file_cookies.find(cookie_needed) != -1:
                        cookies.setdefault(cookie_needed, file_cookies.replace("=", "").replace(
                            " ", "").split(cookie_needed)[1].split(";")[0])
        except KeyboardInterrupt:
            print("用户强制结束程序...")
            exit(1)
        except FileNotFoundError:
            print("> 打开文件失败！请检查权限以及指定路径是否存在文件(回车以返回)。")
            input()
            clear()
            return
        except:
            print("> 文件错误或损坏(回车以返回)")
            input()
            clear()
            return

    elif choice == "2":
        print("> 请输入 .har 文件路径：")
        print("\n> ", end="")
        file_path = input()

        # 去除两边自动添加的无关符号
        for char in strip_char:
            if not os.path.isfile(file_path):
                file_path = file_path.strip(char)
            else:
                break
        # 替换自动添加的无关符号
        for chars in replace_char:
            if not os.path.isfile(file_path):
                file_path = file_path.replace(chars[0], chars[1])
            else:
                break

        try:
            file_data = json.load(open(file_path, "r"))
        except KeyboardInterrupt:
            print("用户强制结束程序...")
            exit(1)
        except FileNotFoundError:
            print("> 打开文件失败！请检查权限以及指定路径是否存在文件(回车以返回)。")
            input()
            clear()
            return
        except:
            print("> 文件错误或损坏，要求 .har 文件(回车以返回)")
            input()
            clear()
            return

        print("> 开始分析抓包数据")
        try:
            file_data = file_data["log"]["entries"]
            for data in file_data:
                if len(cookies) == len(COOKIES_NEEDED):
                    break
                for cookie in data["request"]["cookies"]:
                    if len(cookies) == len(COOKIES_NEEDED):
                        break
                    if cookie["name"] in COOKIES_NEEDED:
                        cookies.setdefault(cookie["name"], cookie["value"])
        except KeyboardInterrupt:
            print("用户强制结束程序...")
            exit(1)
        except:
            print("> 文件错误或损坏，要求 .har 文件(回车以返回)")
            input()
            clear()
            return

    else:
        print("> 输入有误(回车以返回)\n")
        input()
        clear()
        return

    clear()
    print("\n> 分析完毕，结果如下：")
    print("----------")
    for key in COOKIES_NEEDED:
        if key not in cookies:
            value = "未找到"
        else:
            value = cookies[key]
        print("{0}: {1}".format(key, value))
    print("----------")

    while True:
        print("\n> 是否将分析得到的Cookies数据(包括stoken)写入配置文件？")
        print("-- 输入 y 并回车以确认")
        print("-- 注意：将对 config.ini 配置文件进行写入，文件中的注释和排版将被重置")
        print("-- 注意：只会增加配置文件中Cookies没有的项，已有的项不会被覆盖更新")
        print("-- 按回车键跳过并返回功能选择界面")
        print("\n> ", end="")
        choice = input()
        clear()

        if choice == "y":
            try:
                conf = configparser.RawConfigParser()
                conf.read("config.ini", encoding="utf-8")
                current_cookies = conf.get("Config", "Cookie").replace(
                    " ", "").strip("\"").strip("'")

                for key in cookies:
                    if key + "=...;" in current_cookies:
                        current_cookies = current_cookies.replace(
                            key + "=...;", key + "=" + cookies[key] + ";")
                    if key + "=" not in current_cookies:
                        current_cookies += (key + "=" + cookies[key] + ";")

                conf.set("Config", "Cookie", "\"" + current_cookies + "\"")
                if "stoken" in cookies and conf.get("Config",
                                                    "stoken") != None:
                    conf.set("Config", "stoken", cookies["stoken"])
                with open("config.ini", "w", encoding="utf-8") as config_file:
                    conf.write(config_file)

                print("> 配置文件写入成功(回车以返回功能选择界面)")
                input()
                clear()
                return
            except KeyboardInterrupt:
                print("用户强制结束程序...")
                exit(1)
            except:
                print("> 配置文件写入失败，检查config.ini是否存在且有权限读写(回车以返回)")
                input()
                clear()
                return
        elif choice != "":
            print("> 输入有误，请重新输入(回车以返回)\n")
            input()
            clear()
            continue
        else:
            clear()
            return


def checkUpdate() -> None:
    try:
        latest_url = requests.get(
            "https://github.com/Ljzd-PRO/Mys_Goods_Tool/releases/latest", allow_redirects=False).headers["Location"]
        latest_tag = os.path.basename(latest_url)
        if VERSION != latest_tag:
            print("-- 有新版本可用\n")
        else:
            print("-- 已经是最新版本\n")
        print("- 当前版本: {}".format(VERSION))
        print("- 最新版本: {}".format(latest_tag))
        print("- 链接: {}".format(latest_url))
        print("\n> 回车以返回\n")
        input()
    except:
        print("\n> 检查更新失败，回车以返回\n")
        input()


while __name__ == '__main__':
    clear()
    print("> 选择功能：")
    print("-- 1. 查询商品ID(Good_ID)")
    print("-- 2. 查询送货地址ID(Address_ID)")
    print("-- 3. 从抓包导出文件分析获取Cookies(包括stoken)")
    print("-- 4. 检查更新")
    print("\n-- 0. 退出")
    print("\n> ", end="")

    choice = input()
    clear()
    if choice == "1":
        goodTool()
    elif choice == "2":
        addressTool()
    elif choice == "3":
        cookieTool()
    elif choice == "4":
        checkUpdate()
    elif choice == "0":
        break
    else:
        print("> 输入有误，请重新输入(回车以返回)\n")
        input()
