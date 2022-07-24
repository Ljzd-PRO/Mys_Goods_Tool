# coding=utf-8

import os
import random
import time
import requests
import json
import platform
import configparser
import string
import requests.utils
import ntplib
import pyperclip

VERSION = "v1.4.1-beta"
"""程序当前版本"""
COOKIES_NEEDED = [
    "stuid", "stoken", "ltoken", "ltuid", "account_id", "cookie_token",
    "login_ticket", "mid", "login_uid"
]
"""需要获取的Cookies"""
USER_AGENT_MOBILE = "Mozilla/5.0 (iPhone; CPU iPhone OS 15_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) miHoYoBBS/2.25.1"
"""移动端 User-Agent"""
USER_AGENT_PC = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Safari/605.1.15"
"""桌面端 User-Agent"""
X_RPC_DEVICE_MODEL = "OS X 10.15.7"
"""Headers所用的 x-rpc-device_model"""
X_RPC_DEVICE_NAME = "Microsoft Edge 103.0.1264.62"
"""Headers所用的 x-rpc-device_name"""
UA = "\".Not/A)Brand\";v=\"99\", \"Microsoft Edge\";v=\"103\", \"Chromium\";v=\"103\""
"""Headers所用的 sec-ch-ua"""
NTP_SERVER = "ntp.aliyun.com"
"""NTP服务器，用于获取网络时间"""
MAX_RETRY_TIMES = 5
"""网络时间校对失败后最多重试次数"""
SLEEP_TIME = 3
"""网络时间校对后的等待时间(目的是预留时间查看日志)"""

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


class NtpTime():
    """
    >>> NtpTime.time() #获取校准后的时间（如果校准成功）
    """
    ntp_error_times = 0
    time_offset = 0
    while True:
        print("正在校对互联网时间...")
        try:
            time_offset = ntplib.NTPClient().request(
                NTP_SERVER).tx_time - time.time()
            break
        except KeyboardInterrupt:
            print("用户强制结束程序...")
            exit(1)
        except:
            ntp_error_times += 1
            if ntp_error_times == MAX_RETRY_TIMES:
                print("校对互联网时间失败，改为使用本地时间")
                break
            else:
                print("校对互联网时间失败，正在重试({})".format(ntp_error_times))
    print("互联网时间校对完成")
    for second in range(0, SLEEP_TIME):
        print("\r{} 秒后进入主菜单...".format(SLEEP_TIME - second), end="")
        time.sleep(1)

    def time() -> float:
        """
        获取校准后的时间（如果校准成功）
        """
        return time.time() + NtpTime.time_offset


def readConfig():
    """
    读取配置文件
    """
    conf = configparser.RawConfigParser()
    try:
        try:
            conf.read_file(open("config.ini", encoding="utf-8"))
        except:
            conf.read_file(open("config.ini", encoding="utf-8-sig"))
        return conf
    except KeyboardInterrupt:
        print("用户强制结束程序...")
        exit(1)
    except:
        return


def findCookiesInStr(cookiesStr: str, save: dict) -> None:
    """
    在Raw原始模式下的Cookies字符串中查找所需要的Cookie
    >>> cookiesStr: str #Raw Cookies 字符串
    >>> save: str #结果保存到的字典
    """
    for cookie_needed in COOKIES_NEEDED:
        if len(save) == len(COOKIES_NEEDED):
            return
        location = cookiesStr.find(cookie_needed)
        if location != -1:
            save.setdefault(cookie_needed, cookiesStr[cookiesStr.find(
                "=", location) + 1: cookiesStr.find(";", location)])


def generateDeviceID() -> str:
    """
    生成随机的x-rpc-device_id
    """
    return "".join(random.sample(string.ascii_letters + string.digits,
                                 8)).lower() + "-" + "".join(random.sample(string.ascii_letters + string.digits,
                                                                           4)).lower() + "-" + "".join(random.sample(string.ascii_letters + string.digits,
                                                                                                                     4)).lower() + "-" + "".join(random.sample(string.ascii_letters + string.digits,
                                                                                                                                                               4)).lower() + "-" + "".join(random.sample(string.ascii_letters + string.digits,
                                                                                                                                                                                                         12)).lower()


def goodTool() -> None:
    while True:
        print("""\
> 请选择要查看的游戏：
-- 1. 崩坏3
-- 2. 原神
-- 3. 崩坏学园2
-- 4. 未定事件簿
-- 5. 米游社
\n-- 0. 返回功能选择界面\
""")

        choice = input("\n> ")
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
            print("商品名称：{}".format(good["goods_name"]))
            print("商品ID(Good_ID)：{}".format(good["goods_id"]))
            print("商品价格：{} 米游币".format(good["price"]))

            if good["type"] != 1 and good["next_time"] == 0:
                print("兑换时间：任何时间")
            elif good["type"] != 1 and good["next_num"] == 0:
                print("库存：无限")
            else:
                print("兑换时间：{}".format(
                    time.strftime("%Y-%m-%d %H:%M:%S",
                                  time.localtime(good["next_time"]))))
                print("库存：{} 件".format(good["next_num"]))

            if good["account_cycle_type"] == "forever":
                print("限购：每人限购 {0}/{1}".format(good["account_exchange_num"],
                                               good["account_cycle_limit"]))
            elif good["account_cycle_type"] == "month":
                print("限购：本月限购 {0}/{1}".format(good["account_exchange_num"],
                                               good["account_cycle_limit"]))

            print("预览图：{}".format(good["icon"]))

        print("\n> 请按回车返回上一页")
        input()
        clear()


def addressTool() -> None:
    conf = readConfig()
    try:
        if conf is None:
            raise
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
        clear()
        if cookie_input != "":
            cookie = cookie_input.strip("'''").strip("'").strip(
                "\"\"\"").strip("\"")
        else:
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
        "x-rpc-device_id": generateDeviceID(),
        "x-rpc-client_type":
            "5",
        "User-Agent":
            USER_AGENT_MOBILE,
        "Referer":
            "https://user.mihoyo.com/",
        "Accept-Language":
            "zh-CN,zh-Hans;q=0.9",
        "Accept-Encoding":
            "gzip, deflate, br"
    }
    url = "https://api-takumi.mihoyo.com/account/address/list?t={time_now}".format(
        time_now=round(NtpTime.time() * 1000))

    try:
        address_list_req = requests.get(url, headers=headers)
        address_list = address_list_req.json()["data"]["list"]
    except KeyboardInterrupt:
        print("用户强制结束程序...")
        exit(1)
    except:
        print("获取地址信息失败（回车以返回）")
        try:
            print("服务器返回: " + address_list_req.json())
        except:
            pass
        input()
        return

    while True:
        print("\n> 查询结果：")
        for address in address_list:
            print("----------")
            print("省：{}".format(address["province_name"]))
            print("市：{}".format(address["city_name"]))
            print("区/县：{}".format(address["county_name"]))
            print("详细地址：{}".format(address["addr_ext"]))
            print("联系电话：{}".format(address["connect_areacode"] + " " +
                                   address["connect_mobile"]))
            print("联系人：{}".format(address["connect_name"]))
            print("地址ID(Address_ID)：{}".format(address["id"]))

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
            try:
                with open("config.ini", "w", encoding="utf-8") as config_file:
                    conf.write(config_file)
            except:
                with open("config.ini", "w", encoding="utf-8-sig") as config_file:
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

    print("""\
> 请选择抓包导出文件类型：
-- 1. 使用 HttpCanary 导出的文件夹
-- 2. .har 文件
\n-- 0. 返回主菜单\
    """)

    choice = input("\n> ")
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
                try:
                    file_data = json.load(
                        open(os.path.join(file_path, req_dir, "request.json"), "r", encoding="utf-8"))
                except:
                    file_data = json.load(
                        open(os.path.join(file_path, req_dir, "request.json"), "r", encoding="utf-8-sig"))
                print("> 开始分析抓包数据")
                try:
                    file_cookies = file_data["headers"]["Cookie"]
                except KeyError:
                    try:
                        file_cookies = file_data["headers"]["cookie"]
                    except KeyError:
                        continue
                findCookiesInStr(file_cookies, cookies)
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
        clear()

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
            try:
                file_data = json.load(open(file_path, "r", encoding="utf-8"))
            except:
                file_data = json.load(
                    open(file_path, "r", encoding="utf-8-sig"))
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
                for header in data["request"]["headers"]:
                    if len(cookies) == len(COOKIES_NEEDED):
                        break
                    if header["name"] == "Cookie" or header["name"] == "cookie":
                        findCookiesInStr(header["value"], cookies)
        except KeyboardInterrupt:
            print("用户强制结束程序...")
            exit(1)
        except:
            print("> 文件错误或损坏，要求 .har 文件(回车以返回)")
            input()
            clear()
            return

    elif choice == "0":
        return

    else:
        print("> 输入有误(回车以返回)\n")
        input()
        clear()
        cookieTool()
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
        print("""\
\n> 是否将分析得到的Cookies数据(包括stoken)写入配置文件？
-- 输入 y 并回车以确认
-- 注意：将对 config.ini 配置文件进行写入，文件中的注释和排版将被重置
-- 注意：将覆盖现有Cookies数据
-- 按回车键跳过并返回功能选择界面\
        """)

        choice = input("\n> ")
        clear()

        if choice == "y":
            try:
                conf = readConfig()
                current_cookies = ""
                for key in cookies:
                    current_cookies += (key + "=" + cookies[key] + ";")
                conf.set("Config", "Cookie", current_cookies)

                try:
                    with open("config.ini", "w", encoding="utf-8") as config_file:
                        conf.write(config_file)
                except:
                    with open("config.ini", "w", encoding="utf-8-sig") as config_file:
                        conf.write(config_file)

                print("> 配置文件写入成功(回车以返回功能选择界面)")
                input()
                return
            except KeyboardInterrupt:
                print("用户强制结束程序...")
                exit(1)
            except:
                print("> 配置文件写入失败，检查config.ini是否存在且有权限读写(回车以返回)")
                input()
                return
        elif choice != "":
            print("> 输入有误，请重新输入(回车以返回)\n")
            input()
            clear()
            continue
        else:
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
    except KeyboardInterrupt:
        print("用户强制结束程序...")
        exit(1)
    except:
        print("\n> 检查更新失败，回车以返回\n")
        input()


def completeCookie() -> None:
    while True:
        print("""\
将自动补上Cookie中兑换游戏内物品所需的stoken
> 进行选择：
-- 1. 从浏览器获取的网页版米游社Cookie中补全
-- 2. 从配置文件中读取Cookie值进行补全

-- 0. 返回功能选择界面\
        """)
        choice = input("\n> ")
        clear()
        conf = readConfig()

        if choice == "1":
            command = "var cookie=document.cookie;var ask=confirm('是否保存到剪切板?\\nCookie查找结果：'+cookie);if(ask==true){copy(cookie);msg=cookie}else{msg='Cancel'}"
            print("""\
请进行以下操作：
> 1. 登录: https://user.mihoyo.com/ 和 https://bbs.mihoyo.com/dby/
> 2. 在浏览器两个页面分别打开开发者模式，进入控制台，输入下面的语句并回车\n\
            """)
            print(command)
            try:
                pyperclip.copy(command)
                print("-- 已自动拷贝至剪切板，若没有成功，需要手动复制。")
            except:
                pass
            print("\n> 3. 粘贴第一次查找到的Cookie:")
            origin_cookie = input("> ")
            try:
                if origin_cookie.split()[-1] != ";":
                    origin_cookie += ";"
                print("\n> 4. 粘贴第二次查找到的Cookie:")
                origin_cookie += input("> ")
                clear()
                if origin_cookie.split()[-1] != ";":
                    origin_cookie += ";"
            except:
                clear()
                print("输入有误，回车以返回")
                input()
                clear()
                continue
        elif choice == "2":
            try:
                if conf is None:
                    raise
                origin_cookie = conf.get(
                    "Config",
                    "Cookie").strip("'''").strip("'").strip("\"\"\"").strip("\"")
            except KeyboardInterrupt:
                print("用户强制结束程序...")
                exit(1)
            except:
                print("> 读取Cookie失败，请手动输入Cookie信息：(返回上一页请直接回车)")
                print("> ", end="")
                cookie_input = input()
                clear()
                if cookie_input != "":
                    origin_cookie = cookie_input.strip("'''").strip("'").strip(
                        "\"\"\"").strip("\"")
                else:
                    continue
        elif choice == "0":
            break
        else:
            print("> 输入有误，请重新输入(回车以返回)\n")
            input()
            clear()
            continue

        cookies = {}
        if origin_cookie.split()[-1] != ";":
            origin_cookie += ";"
        findCookiesInStr(origin_cookie, cookies)

        # 开头为"v2__"的stoken还需要搭配"mid"才行
        if "stoken" in cookies:
            if cookies["stoken"].find("v2__") == 0:
                cookies.pop("stoken")
            else:
                print("Cookie是完整的，无需补全，回车以返回\n")
                input()
                clear()
                continue

        if "mid" in cookies:
            cookies.pop("mid")

        if "login_ticket" not in cookies:
            print("> 由于缺少login_ticket，无法补全，回车以返回\n")
            input()
            clear()
            continue

        bbs_uid = None
        for cookie in ("login_uid", "stuid", "ltuid", "account_id"):
            if cookie in cookies:
                bbs_uid = cookies[cookie]
                break
        if bbs_uid is None:
            print("> 由于Cookie缺少uid，无法补全，回车以返回\n")
            input()
            clear()
            continue

        print("正在获取stoken...")
        try:
            get_stoken_req = requests.get(
                "https://api-takumi.mihoyo.com/auth/api/getMultiTokenByLoginTicket?login_ticket={0}&token_types=3&uid={1}".format(cookies["login_ticket"], bbs_uid))
            stoken = list(filter(
                lambda data: data["name"] == "stoken", get_stoken_req.json()["data"]["list"]))[0]["token"]
        except KeyboardInterrupt:
            print("用户强制结束程序...")
            exit(1)
        except:
            clear()
            print("> 获取stoken失败，一种可能是登录失效，回车以返回\n")
            input()
            clear()
            continue

        origin_cookie += ("stoken=" + stoken + ";")
        print("""\
> 补全后: {}

-- 输入 y 并回车以写入 config.ini 配置文件
-- 注意：将对 config.ini 配置文件进行写入，文件中的注释和排版将被重置
-- 按回车键跳过并返回功能选择界面\
        """.format(origin_cookie))
        choice = input("> ")
        clear()
        if choice != "y":
            break

        try:
            if conf is None:
                raise
            conf.set("Config", "Cookie", origin_cookie)
            try:
                with open("config.ini", "w", encoding="utf-8") as config_file:
                    conf.write(config_file)
            except:
                with open("config.ini", "w", encoding="utf-8-sig") as config_file:
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


def onekeyCookie() -> None:
    login_1_headers = {
        "Host": "webapi.account.mihoyo.com",
        "Connection": "keep-alive",
        "Content-Length": "79",
        "sec-ch-ua": UA,
        "DNT": "1",
        "x-rpc-device_model": X_RPC_DEVICE_MODEL,
        "sec-ch-ua-mobile": "?0",
        "User-Agent": USER_AGENT_PC,
        "x-rpc-device_id": generateDeviceID(),
        "Accept": "application/json, text/plain, */*",
        "x-rpc-device_name": X_RPC_DEVICE_NAME,
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "x-rpc-client_type": "4",
        "sec-ch-ua-platform": "\"macOS\"",
        "Origin": "https://user.mihoyo.com",
        "Sec-Fetch-Site": "same-site",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Dest": "empty",
        "Referer": "https://user.mihoyo.com/",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6"
    }
    login_2_headers = {
        "Host": "api-takumi.mihoyo.com",
        "Content-Type": "application/json;charset=utf-8",
        "Origin": "https://bbs.mihoyo.com",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Accept": "application/json, text/plain, */*",
        "User-Agent": USER_AGENT_PC,
        "Referer": "https://bbs.mihoyo.com/",
        "Content-Length": "95",
        "Accept-Language": "zh-CN,zh-Hans;q=0.9"
    }

    while True:
        print("请进行以下操作：")
        url = "https://user.mihoyo.com/#/login/captcha"
        print("> 1. 进入 {}".format(url))
        try:
            pyperclip.copy(url)
            print("-- 已自动拷贝至剪切板，若没有成功，需要手动复制。\n")
        except:
            pass
        print("""\
> 2. 在浏览器中输入手机号并获取验证码，但不要使用验证码登录")

> 3. 在此输入手机号 - 用于获取login_ticket (不会发送给任何第三方服务器，项目开源安全):
-- (回车返回主菜单)\
        """)
        phone = input("> ")
        if phone == "":
            break
        print("\n> 4. 在此输入验证码 - 用于获取login_ticket (不会发送给任何第三方服务器，项目开源安全):")
        captcha = input("> ")

        print("正在登录...")
        try:
            login_1_req = requests.post(
                "https://webapi.account.mihoyo.com/Api/login_by_mobilecaptcha", headers=login_1_headers, data="mobile={0}&mobile_captcha={1}&source=user.mihoyo.com".format(phone, captcha))
        except KeyboardInterrupt:
            print("用户强制结束程序...")
            exit(1)
        except:
            print("> 登录失败，回车以返回\n")
            input()
            clear()
            continue
        login_1_cookie = requests.utils.dict_from_cookiejar(
            login_1_req.cookies)

        if "login_ticket" not in login_1_cookie:
            print("> 由于Cookie缺少login_ticket，无法继续，回车以返回\n")
            input()
            clear()
            continue

        for cookie in ("login_uid", "stuid", "ltuid", "account_id"):
            if cookie in login_1_cookie:
                bbs_uid = login_1_cookie[cookie]
                break
        if bbs_uid is None:
            print("> 由于Cookie缺少uid，无法继续，回车以返回\n")
            input()
            clear()
            continue

        print("正在获取stoken...")
        try:
            get_stoken_req = requests.get(
                "https://api-takumi.mihoyo.com/auth/api/getMultiTokenByLoginTicket?login_ticket={0}&token_types=3&uid={1}".format(login_1_cookie["login_ticket"], bbs_uid))
            stoken = list(filter(
                lambda data: data["name"] == "stoken", get_stoken_req.json()["data"]["list"]))[0]["token"]
        except KeyboardInterrupt:
            print("用户强制结束程序...")
            exit(1)
        except:
            clear()
            print("> 获取stoken失败，一种可能是登录失效，回车以返回\n")
            input()
            clear()
            continue

        print("> 5. 刷新页面，再次进入 {}".format(url))
        try:
            pyperclip.copy(url)
            print("-- 已自动拷贝至剪切板，若没有成功，需要手动复制。\n")
        except:
            pass
        print("> 6. 在浏览器中输入刚才所用的手机号并获取验证码，但不要使用验证码登录")
        print("\n> 7. 在此输入验证码 - 用于获取cookie_token等 (不会发送给任何第三方服务器，项目开源安全):")
        captcha = input("> ")

        print("正在登录...")
        try:
            login_2_req = requests.post(
                "https://api-takumi.mihoyo.com/account/auth/api/webLoginByMobile", headers=login_2_headers, json={
                    "is_bh2": False,
                    "mobile": phone,
                    "captcha": captcha,
                    "action_type": "login",
                    "token_type": 6
                })
        except KeyboardInterrupt:
            print("用户强制结束程序...")
            exit(1)
        except:
            print("> 登录失败，回车以返回\n")
            input()
            clear()
            continue
        login_2_cookie = requests.utils.dict_from_cookiejar(
            login_2_req.cookies)

        if "cookie_token" not in login_2_cookie:
            print("> 由于Cookie缺少cookie_token，无法继续，回车以返回\n")
            input()
            clear()
            continue

        result_cookie = ""
        for cookie in login_2_cookie:
            result_cookie += (cookie + "=" + login_2_cookie[cookie] + ";")
        result_cookie += ("login_ticket=" +
                          login_1_cookie["login_ticket"] + ";")
        result_cookie += ("stoken=" + stoken + ";")

        print("""\
> 成功获取Cookie:
{}

-- 输入 y 并回车以写入 config.ini 配置文件
-- 注意：将对 config.ini 配置文件进行写入，文件中的注释和排版将被重置
-- 按回车键跳过并返回功能选择界面\
        """.format(result_cookie))
        choice = input("> ")
        clear()
        if choice != "y":
            break

        try:
            conf = readConfig()
            if conf is None:
                raise
            conf.set("Config", "Cookie", result_cookie)
            try:
                with open("config.ini", "w", encoding="utf-8") as config_file:
                    conf.write(config_file)
            except:
                with open("config.ini", "w", encoding="utf-8-sig") as config_file:
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


while __name__ == '__main__':
    clear()
    print(
        """> 选择功能：
-- 1. 查询商品ID(Good_ID)
-- 2. 登录并一键获取Cookie(推荐)
-- 3. 从抓包导出文件分析获取Cookie
-- 4. 补全Cookie(从网页版或从配置文件中补全)
-- 5. 查询送货地址ID(Address_ID)
-- 6. 检查更新

-- 0. 退出""")

    choice = input("\n> ")
    clear()
    if choice == "1":
        goodTool()
    elif choice == "2":
        onekeyCookie()
    elif choice == "3":
        cookieTool()
    elif choice == "4":
        completeCookie()
    elif choice == "5":
        addressTool()
    elif choice == "6":
        checkUpdate()
    elif choice == "0":
        break
    else:
        print("> 输入有误，请重新输入(回车以返回)\n")
        input()
