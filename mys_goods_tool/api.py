import traceback
from typing import List, Literal, Optional, Tuple

import httpx
import tenacity
from pydantic import ValidationError
from requests.utils import dict_from_cookiejar

from .data_model import GameRecord, GameInfo, Good, Address, BaseApiStatus, MmtData, GeetestResult, GetCookieStatus, \
    CreateMobileCaptchaStatus, GetGoodDetailStatus, MobileCaptchaResult, ExchangeStatus, ExchangeResult
from .user_data import config as conf, UserAccount, BBSCookies, ExchangePlan
from .utils import generate_device_id, logger, custom_attempt_times, generate_ds, check_login, Subscribe, check_ds, \
    NtpTime

URL_LOGIN_CAPTCHA = "https://webapi.account.mihoyo.com/Api/login_by_mobilecaptcha"
URL_LOGIN_STOKEN = "https://api-takumi.mihoyo.com/auth/api/getMultiTokenByLoginTicket?login_ticket={0}&token_types=3&uid={1}"
URL_LOGIN_COOKIE_TOKEN = "https://api-takumi.mihoyo.com/account/auth/api/webLoginByMobile"
URL_ACTION_TICKET = "https://api-takumi.mihoyo.com/auth/api/getActionTicketBySToken?action_type=game_role&stoken={stoken}&uid={bbs_uid}"
URL_GAME_RECORD = "https://api-takumi-record.mihoyo.com/game_record/card/wapi/getGameRecordCard?uid={}"
URL_GAME_LIST = "https://bbs-api.mihoyo.com/apihub/api/getGameList"
URL_MYB = "https://api-takumi.mihoyo.com/common/homutreasure/v1/web/user/point?app_id=1&point_sn=myb"
URL_DEVICE_LOGIN = "https://bbs-api.mihoyo.com/apihub/api/deviceLogin"
URL_DEVICE_SAVE = "https://bbs-api.mihoyo.com/apihub/api/saveDevice"
URL_GOOD_LIST = "https://api-takumi.mihoyo.com/mall/v1/web/goods/list?app_id=1&point_sn=myb&page_size=20&page={" \
                "page}&game={game} "
URL_CHECK_GOOD = "https://api-takumi.mihoyo.com/mall/v1/web/goods/detail?app_id=1&point_sn=myb&goods_id={}"
URL_EXCHANGE = "https://api-takumi.mihoyo.com/mall/v1/web/goods/exchange"
URL_ADDRESS = "https://api-takumi.mihoyo.com/account/address/list?t={}"
URL_REGISTRABLE = "https://webapi.account.mihoyo.com/Api/is_mobile_registrable?mobile={mobile}&t={t}"
URL_CREATE_MMT = "https://webapi.account.mihoyo.com/Api/create_mmt?scene_type=1&now={now}&reason=user.mihoyo.com%2523%252Flogin%252Fcaptcha&action_type=login_by_mobile_captcha&t={t}"
URL_CREATE_MOBILE_CAPTCHA = "https://webapi.account.mihoyo.com/Api/create_mobile_captcha"

HEADERS_WEBAPI = {
    "Host": "webapi.account.mihoyo.com",
    "Connection": "keep-alive",
    "sec-ch-ua": conf.device_config.UA,
    "DNT": "1",
    "x-rpc-device_model": conf.device_config.X_RPC_DEVICE_MODEL_PC,
    "sec-ch-ua-mobile": "?0",
    "User-Agent": conf.device_config.USER_AGENT_PC,
    "x-rpc-device_id": None,
    "Accept": "application/json, text/plain, */*",
    "x-rpc-device_name": conf.device_config.X_RPC_DEVICE_NAME_PC,
    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
    "x-rpc-client_type": "4",
    "sec-ch-ua-platform": conf.device_config.UA_PLATFORM,
    "Origin": "https://user.mihoyo.com",
    "Sec-Fetch-Site": "same-site",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Dest": "empty",
    "Referer": "https://user.mihoyo.com/",
    "Accept-Encoding": "gzip, deflate, br",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6"
}
HEADERS_LOGIN_STOKEN = {
    "Host": "api-takumi.mihoyo.com",
    "Content-Type": "application/json;charset=utf-8",
    "Origin": "https://bbs.mihoyo.com",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Accept": "application/json, text/plain, */*",
    "User-Agent": conf.device_config.USER_AGENT_PC,
    "Referer": "https://bbs.mihoyo.com/",
    "Accept-Language": "zh-CN,zh-Hans;q=0.9"
}
HEADERS_ACTION_TICKET = {
    "Host": "api-takumi.mihoyo.com",
    "x-rpc-device_model": conf.device_config.X_RPC_DEVICE_MODEL_MOBILE,
    "User-Agent": conf.device_config.USER_AGENT_OTHER,
    "Referer": "https://webstatic.mihoyo.com/",
    "x-rpc-device_name": conf.device_config.X_RPC_DEVICE_NAME_MOBILE,
    "Origin": "https://webstatic.mihoyo.com",
    "Content-Length": "66",
    "Connection": "keep-alive",
    "x-rpc-channel": conf.device_config.X_RPC_CHANNEL,
    "x-rpc-app_version": conf.device_config.X_RPC_APP_VERSION,
    "Accept-Language": "zh-CN,zh-Hans;q=0.9",
    "DS": None,
    "x-rpc-device_id": None,
    "x-rpc-client_type": "5",
    "Accept": "application/json, text/plain, */*",
    "Content-Type": "application/json;charset=utf-8",
    "Accept-Encoding": "gzip, deflate, br",
    "x-rpc-sys_version": conf.device_config.X_RPC_SYS_VERSION,
    "x-rpc-platform": conf.device_config.X_RPC_PLATFORM
}
HEADERS_GAME_RECORD = {
    "Host": "api-takumi-record.mihoyo.com",
    "Origin": "https://webstatic.mihoyo.com",
    "Connection": "keep-alive",
    "Accept": "application/json, text/plain, */*",
    "User-Agent": conf.device_config.USER_AGENT_MOBILE,
    "Accept-Language": "zh-CN,zh-Hans;q=0.9",
    "Referer": "https://webstatic.mihoyo.com/",
    "Accept-Encoding": "gzip, deflate, br"
}
HEADERS_GAME_LIST = {
    "Host": "bbs-api.mihoyo.com",
    "DS": None,
    "Accept": "*/*",
    "x-rpc-device_id": generate_device_id(),
    "x-rpc-client_type": "1",
    "x-rpc-channel": conf.device_config.X_RPC_CHANNEL,
    "Accept-Language": "zh-CN,zh-Hans;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "x-rpc-sys_version": conf.device_config.X_RPC_SYS_VERSION,
    "Referer": "https://app.mihoyo.com",
    "x-rpc-device_name": conf.device_config.X_RPC_DEVICE_NAME_MOBILE,
    "x-rpc-app_version": conf.device_config.X_RPC_APP_VERSION,
    "User-Agent": conf.device_config.USER_AGENT_OTHER,
    "Connection": "keep-alive",
    "x-rpc-device_model": conf.device_config.X_RPC_DEVICE_MODEL_MOBILE
}
HEADERS_MYB = {
    "Host": "api-takumi.mihoyo.com",
    "Origin": "https://webstatic.mihoyo.com",
    "Connection": "keep-alive",
    "Accept": "application/json, text/plain, */*",
    "User-Agent": conf.device_config.USER_AGENT_MOBILE,
    "Accept-Language": "zh-CN,zh-Hans;q=0.9",
    "Referer": "https://webstatic.mihoyo.com/",
    "Accept-Encoding": "gzip, deflate, br"
}
HEADERS_DEVICE = {
    "DS": None,
    "x-rpc-client_type": "2",
    "x-rpc-app_version": conf.device_config.X_RPC_APP_VERSION,
    "x-rpc-sys_version": conf.device_config.X_RPC_SYS_VERSION_ANDROID,
    "x-rpc-channel": conf.device_config.X_RPC_CHANNEL_ANDROID,
    "x-rpc-device_id": None,
    "x-rpc-device_name": conf.device_config.X_RPC_DEVICE_NAME_ANDROID,
    "x-rpc-device_model": conf.device_config.X_RPC_DEVICE_MODEL_ANDROID,
    "Referer": "https://app.mihoyo.com",
    "Content-Type": "application/json; charset=UTF-8",
    "Host": "bbs-api.mihoyo.com",
    "Connection": "Keep-Alive",
    "Accept-Encoding": "gzip",
    "User-Agent": conf.device_config.USER_AGENT_ANDROID_OTHER
}
HEADERS_GOOD_LIST = {
    "Host":
        "api-takumi.mihoyo.com",
    "Accept":
        "application/json, text/plain, */*",
    "Origin":
        "https://user.mihoyo.com",
    "Connection":
        "keep-alive",
    "x-rpc-device_id": generate_device_id(),
    "x-rpc-client_type":
        "5",
    "User-Agent":
        conf.device_config.USER_AGENT_MOBILE,
    "Referer":
        "https://user.mihoyo.com/",
    "Accept-Language":
        "zh-CN,zh-Hans;q=0.9",
    "Accept-Encoding":
        "gzip, deflate, br"
}
HEADERS_EXCHANGE = {
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
    "Host":
        "api-takumi.mihoyo.com",
    "User-Agent":
        conf.device_config.USER_AGENT_MOBILE,
    "x-rpc-app_version":
        conf.device_config.X_RPC_APP_VERSION,
    "x-rpc-channel":
        "appstore",
    "x-rpc-client_type":
        "1",
    "x-rpc-device_id": None,
    "x-rpc-device_model":
        conf.device_config.X_RPC_DEVICE_MODEL_MOBILE,
    "x-rpc-device_name":
        conf.device_config.X_RPC_DEVICE_NAME_MOBILE,
    "x-rpc-sys_version":
        conf.device_config.X_RPC_SYS_VERSION
}
HEADERS_ADDRESS = {
    "Host": "api-takumi.mihoyo.com",
    "Accept": "application/json, text/plain, */*",
    "Origin": "https://user.mihoyo.com",
    "Connection": "keep-alive",
    "x-rpc-device_id": None,
    "x-rpc-client_type": "5",
    "User-Agent": conf.device_config.USER_AGENT_MOBILE,
    "Referer": "https://user.mihoyo.com/",
    "Accept-Language": "zh-CN,zh-Hans;q=0.9",
    "Accept-Encoding": "gzip, deflate, br"
}

IncorrectReturn = (KeyError, TypeError, AttributeError, ValidationError)
"""米游社API返回数据无效会触发的异常组合"""


async def get_game_record(account: UserAccount, retry: bool = True) -> Tuple[BaseApiStatus, Optional[List[GameRecord]]]:
    """
    获取用户绑定的游戏账户信息，返回一个GameRecord对象的列表

    :param account: 用户账户数据
    :param retry: 是否允许重试
    """
    try:
        async for attempt in tenacity.AsyncRetrying(stop=custom_attempt_times(retry), reraise=True,
                                                    wait=tenacity.wait_fixed(conf.preference.retry_interval)):
            with attempt:
                async with httpx.AsyncClient() as client:
                    res = await client.get(URL_GAME_RECORD.format(account.bbs_uid), headers=HEADERS_GAME_RECORD,
                                           cookies=account.cookies, timeout=conf.preference.time_out)
                if not check_login(res.text):
                    logger.info(
                        f"获取用户游戏数据(GameRecord) - 用户 {account.bbs_uid} 登录失效")
                    logger.debug(f"网络请求返回: {res.text}")
                    return BaseApiStatus(login_failed=True), None
                return BaseApiStatus(success=True), list(
                    map(GameRecord.parse_obj, res.json()["data"]["list"]))
    except IncorrectReturn:
        logger.error(f"获取用户游戏数据(GameRecord) - 服务器没有正确返回")
        logger.debug(f"网络请求返回: {res.text}")
        logger.debug(f"{traceback.format_exc()}")
        return BaseApiStatus(incorrect_return=True), None
    except Exception:
        logger.error(f"获取用户游戏数据(GameRecord) - 请求失败")
        logger.debug(f"{traceback.format_exc()}")
        return BaseApiStatus(network_error=True), None


async def get_game_list(retry: bool = True) -> Tuple[BaseApiStatus, Optional[List[GameInfo]]]:
    """
    获取米哈游游戏的详细信息，若返回`None`说明获取失败

    :param retry: 是否允许重试
    """
    headers = HEADERS_GAME_LIST.copy()
    try:
        subscribe = Subscribe()
        async for attempt in tenacity.AsyncRetrying(stop=custom_attempt_times(retry), reraise=True,
                                                    wait=tenacity.wait_fixed(conf.preference.retry_interval)):
            with attempt:
                headers["DS"] = generate_ds()
                async with httpx.AsyncClient() as client:
                    res = await client.get(URL_GAME_LIST, headers=headers, timeout=conf.preference.time_out)
                if not check_ds(res.text):
                    logger.info(
                        f"获取游戏信息(GameInfo): DS无效，正在在线获取salt以重新生成...")
                    await subscribe.load()
                    headers["User-Agent"] = conf.device_config.USER_AGENT_MOBILE
                    headers["DS"] = generate_ds()
                return BaseApiStatus(success=True), list(
                    map(GameInfo.parse_obj, res.json()["data"]["list"]))
    except IncorrectReturn:
        logger.error(f"获取游戏信息(GameInfo) - 服务器没有正确返回")
        logger.debug(f"网络请求返回: {res.text}")
        logger.debug(f"{traceback.format_exc()}")
        return BaseApiStatus(incorrect_return=True), None
    except Exception:
        logger.error(f"获取游戏信息(GameInfo) - 请求失败")
        logger.debug(f"{traceback.format_exc()}")
        return BaseApiStatus(network_error=True), None


async def get_user_myb(account: UserAccount, retry: bool = True) -> Tuple[BaseApiStatus, Optional[int]]:
    """
    获取用户当前米游币数量

    :param account: 用户账户数据
    :param retry: 是否允许重试
    """
    try:
        async for attempt in tenacity.AsyncRetrying(stop=custom_attempt_times(retry), reraise=True,
                                                    wait=tenacity.wait_fixed(conf.preference.retry_interval)):
            with attempt:
                async with httpx.AsyncClient() as client:
                    res = await client.get(URL_MYB, headers=HEADERS_MYB, cookies=account.cookies,
                                           timeout=conf.preference.time_out)
                if not check_login(res.text):
                    logger.info(
                        f"获取用户米游币 - 用户 {account.bbs_uid} 登录失效")
                    logger.debug(f"网络请求返回: {res.text}")
                    return BaseApiStatus(login_failed=True), None
                return BaseApiStatus(success=True), int(res.json()["data"]["points"])
    except IncorrectReturn:
        logger.error(f"获取用户米游币 - 服务器没有正确返回")
        logger.debug(f"网络请求返回: {res.text}")
        logger.debug(f"{traceback.format_exc()}")
        return BaseApiStatus(incorrect_return=True), None
    except Exception:
        logger.error(f"获取用户米游币 - 请求失败")
        logger.debug(f"{traceback.format_exc()}")
        return BaseApiStatus(network_error=True), None


async def device_login(account: UserAccount, retry: bool = True):
    """
    设备登录(deviceLogin)(适用于安卓设备)

    :param account: 用户账户数据
    :param retry: 是否允许重试
    """
    data = {
        "app_version": conf.device_config.X_RPC_APP_VERSION,
        "device_id": account.device_id_android,
        "device_name": conf.device_config.X_RPC_DEVICE_NAME_ANDROID,
        "os_version": "30",
        "platform": "Android",
        "registration_id": "1a0018970a5c00e814d"
    }
    headers = HEADERS_DEVICE.copy()
    headers["x-rpc-device_id"] = account.device_id_android
    try:
        subscribe = Subscribe()
        async for attempt in tenacity.AsyncRetrying(stop=custom_attempt_times(retry), reraise=True,
                                                    wait=tenacity.wait_fixed(conf.preference.retry_interval)):
            with attempt:
                headers["DS"] = generate_ds(data)
                async with httpx.AsyncClient() as client:
                    res = await client.post(URL_DEVICE_LOGIN, headers=headers, json=data, cookies=account.cookies,
                                            timeout=conf.preference.time_out)
                if not check_login(res.text):
                    logger.info(
                        f"设备登录(device_login) - 用户 {account.bbs_uid} 登录失效")
                    logger.debug(f"网络请求返回: {res.text}")
                    return BaseApiStatus(login_failed=True)
                if not check_ds(res.text):
                    logger.info(
                        f"设备登录(device_login): DS无效，正在在线获取salt以重新生成...")
                    await subscribe.load()
                    headers["DS"] = generate_ds(data)
                if res.json()["message"] != "OK":
                    raise ValueError
                else:
                    return BaseApiStatus(success=True)
    except IncorrectReturn:
        logger.error(f"设备登录(device_login) - 服务器没有正确返回")
        logger.debug(f"网络请求返回: {res.text}")
        logger.debug(f"{traceback.format_exc()}")
        return BaseApiStatus(incorrect_return=True)
    except Exception:
        logger.error(f"设备登录(device_login) - 请求失败")
        logger.debug(f"{traceback.format_exc()}")
        return BaseApiStatus(network_error=True)


async def device_save(account: UserAccount, retry: bool = True):
    """
    设备保存(saveDevice)(适用于安卓设备)

    :param account: 用户账户数据
    :param retry: 是否允许重试
    """
    data = {
        "app_version": conf.device_config.X_RPC_APP_VERSION,
        "device_id": account.device_id_android,
        "device_name": conf.device_config.X_RPC_DEVICE_NAME_ANDROID,
        "os_version": "30",
        "platform": "Android",
        "registration_id": "1a0018970a5c00e814d"
    }
    headers = HEADERS_DEVICE.copy()
    headers["x-rpc-device_id"] = account.device_id_android
    try:
        subscribe = Subscribe()
        async for attempt in tenacity.AsyncRetrying(stop=custom_attempt_times(retry), reraise=True,
                                                    wait=tenacity.wait_fixed(conf.preference.retry_interval)):
            with attempt:
                headers["DS"] = generate_ds(data)
                async with httpx.AsyncClient() as client:
                    res = await client.post(URL_DEVICE_SAVE, headers=headers, json=data, cookies=account.cookies,
                                            timeout=conf.preference.time_out)
                if not check_login(res.text):
                    logger.info(
                        f"设备保存(device_save) - 用户 {account.bbs_uid} 登录失效")
                    logger.debug(f"网络请求返回: {res.text}")
                    return BaseApiStatus(login_failed=True)
                if not check_ds(res.text):
                    logger.info(
                        f"设备保存(device_save): DS无效，正在在线获取salt以重新生成...")
                    await subscribe.load()
                if res.json()["message"] != "OK":
                    raise ValueError
                else:
                    return BaseApiStatus(success=True)
    except IncorrectReturn:
        logger.error(f"设备保存(device_save) - 服务器没有正确返回")
        logger.debug(f"网络请求返回: {res.text}")
        logger.debug(f"{traceback.format_exc()}")
        return BaseApiStatus(incorrect_return=True)
    except Exception:
        logger.error(f"设备保存(device_save) - 请求失败")
        logger.debug(f"{traceback.format_exc()}")
        return BaseApiStatus(network_error=True)


async def get_good_detail(good_id: str, retry: bool = True) -> Tuple[GetGoodDetailStatus, Optional[Good]]:
    """
    获取某商品的详细信息

    :param good_id: 商品ID
    :param retry: 是否允许重试
    :return: 商品数据
    """
    try:
        async for attempt in tenacity.AsyncRetrying(stop=custom_attempt_times(retry), reraise=True,
                                                    wait=tenacity.wait_fixed(conf.preference.retry_interval)):
            with attempt:
                async with httpx.AsyncClient() as client:
                    res = await client.get(URL_CHECK_GOOD.format(good_id), timeout=conf.preference.time_out)
                if res.json()['message'] == '商品不存在' or res.json()['message'] == '商品已下架':
                    return GetGoodDetailStatus(good_not_existed=True), None
                return GetGoodDetailStatus(success=True), Good.parse_obj(res.json()["data"])
    except IncorrectReturn:
        logger.error(f"米游币商品兑换 - 获取商品详细信息: 服务器没有正确返回")
        logger.debug(f"网络请求返回: {res.text}")
        logger.debug(f"{traceback.format_exc()}")
        GetGoodDetailStatus(incorrect_return=True), None
    except Exception:
        logger.error(f"米游币商品兑换 - 获取商品详细信息: 网络请求失败")
        logger.debug(f"{traceback.format_exc()}")
        GetGoodDetailStatus(network_error=True), None


async def get_good_list(game: Literal["bh3", "ys", "bh2", "wd", "bbs"], retry: bool = True) -> Tuple[
    BaseApiStatus, Optional[List[Good]]]:
    """
    获取商品信息列表

    :param game: 游戏简称
    :param retry: 是否允许重试
    :return: 商品信息列表
    """
    if game == "bh3":
        game = "bh3"
    elif game == "ys":
        game = "hk4e"
    elif game == "bh2":
        game = "bh2"
    elif game == "wd":
        game = "nxx"
    elif game == "bbs":
        game = "bbs"

    good_list = []
    page = 1

    try:
        async for attempt in tenacity.AsyncRetrying(stop=custom_attempt_times(retry), reraise=True,
                                                    wait=tenacity.wait_fixed(conf.preference.retry_interval)):
            with attempt:
                async with httpx.AsyncClient() as client:
                    res = await client.get(URL_GOOD_LIST.format(page=page,
                                                                game=game), headers=HEADERS_GOOD_LIST,
                                           timeout=conf.preference.time_out)
                goods = map(Good.parse_obj, res.json()["data"]["list"])
                # 判断是否已经读完所有商品
                if not goods:
                    break
                else:
                    good_list += goods
                page += 1
    except IncorrectReturn:
        logger.error(f"米游币商品兑换 - 获取商品列表: 服务器没有正确返回")
        logger.debug(f"网络请求返回: {res.text}")
        logger.debug(f"{traceback.format_exc()}")
        return BaseApiStatus(incorrect_return=True), None
    except Exception:
        logger.error(f"米游币商品兑换 - 获取商品列表: 网络请求失败")
        logger.debug(f"{traceback.format_exc()}")
        return BaseApiStatus(network_error=True), None

    # "next_time" 为 0 表示任何时间均可兑换或兑换已结束
    # "type" 为 1 时商品只有在指定时间开放兑换；为 0 时商品任何时间均可兑换
    result = list(filter(lambda good: good.next_time == 0 and good.type == 1 or not good.unlimit and good.next_num == 0,
                         good_list))

    return BaseApiStatus(success=True), result


async def get_address(account: UserAccount, retry: bool = True) -> Tuple[BaseApiStatus, Optional[List[Address]]]:
    """
    获取用户的地址数据

    :param account: 用户账户数据
    :param retry: 是否允许重试
    """
    headers = HEADERS_ADDRESS.copy()
    headers["x-rpc-device_id"] = account.device_id_ios
    try:
        async for attempt in tenacity.AsyncRetrying(stop=custom_attempt_times(retry), reraise=True,
                                                    wait=tenacity.wait_fixed(conf.preference.retry_interval)):
            with attempt:
                async with httpx.AsyncClient() as client:
                    res = await client.get(URL_ADDRESS.format(
                        round(NtpTime.time() * 1000)), headers=headers, cookies=account.cookies,
                        timeout=conf.preference.time_out)
                    if not check_login(res.text):
                        logger.info(
                            f"获取地址数据 - 用户 {account.bbs_uid} 登录失效")
                        logger.debug(f"网络请求返回: {res.text}")
                        return BaseApiStatus(login_failed=True), None
                address_list = list(map(Address.parse_obj, res.json()["data"]["list"]))
    except KeyError:
        logger.error(f"获取地址数据 - 服务器没有正确返回")
        logger.debug(f"网络请求返回: {res.text}")
        logger.debug(f"{traceback.format_exc()}")
        return BaseApiStatus(incorrect_return=True), None
    except Exception:
        logger.error(f"获取地址数据 - 请求失败")
        logger.debug(f"{traceback.format_exc()}")
        return BaseApiStatus(network_error=True), None
    return BaseApiStatus(success=True), address_list


async def check_registrable(phone_number: int, retry: bool = True) -> Tuple[BaseApiStatus, Optional[bool]]:
    """
    检查用户是否可以注册

    :param phone_number: 手机号
    :param retry: 是否允许重试
    """
    headers = HEADERS_WEBAPI.copy()
    headers["x-rpc-device_id"] = generate_device_id()
    try:
        async for attempt in tenacity.AsyncRetrying(stop=custom_attempt_times(retry), reraise=True,
                                                    wait=tenacity.wait_fixed(conf.preference.retry_interval)):
            with attempt:
                async with httpx.AsyncClient() as client:
                    res = await client.get(URL_REGISTRABLE.format(mobile=phone_number, t=round(NtpTime.time() * 1000)),
                                           headers=headers, timeout=conf.preference.timeout)
                return BaseApiStatus(success=True), bool(res.json()["data"]["is_registable"])
    except IncorrectReturn:
        logger.error(f"检查用户 {phone_number} 是否可以注册 - 服务器没有正确返回")
        logger.debug(f"网络请求返回: {res.text}")
        logger.debug(f"{traceback.format_exc()}")
        return BaseApiStatus(incorrect_return=True), None
    except:
        logger.error(f"检查用户 {phone_number} 是否可以注册 - 请求失败")
        logger.debug(f"{traceback.format_exc()}")
        return BaseApiStatus(network_error=True), None


async def create_mmt(retry: bool = True) -> Tuple[BaseApiStatus, Optional[MmtData]]:
    """
    发送短信验证前所需的人机验证任务申请

    :param retry: 是否允许重试
    """
    headers = HEADERS_WEBAPI.copy()
    headers["x-rpc-device_id"] = generate_device_id()
    try:
        async for attempt in tenacity.AsyncRetrying(stop=custom_attempt_times(retry), reraise=True,
                                                    wait=tenacity.wait_fixed(conf.preference.retry_interval)):
            with attempt:
                async with httpx.AsyncClient() as client:
                    time_now = round(NtpTime.time() * 1000)
                    res = await client.get(URL_CREATE_MMT.format(now=time_now, t=time_now),
                                           headers=headers, timeout=conf.preference.timeout)
                return BaseApiStatus(success=True), MmtData.parse_obj(res.json()["data"]["mmt_data"])
    except IncorrectReturn:
        logger.error(f"获取短信验证-人机验证任务(create_mmt) - 服务器没有正确返回")
        logger.debug(f"网络请求返回: {res.text}")
        logger.debug(f"{traceback.format_exc()}")
        return BaseApiStatus(incorrect_return=True), None
    except:
        logger.error(f"获取短信验证-人机验证任务(create_mmt) - 请求失败")
        logger.debug(f"{traceback.format_exc()}")
        return BaseApiStatus(network_error=True), None


async def create_mobile_captcha(phone_number: int, mmt_data: MmtData, geetest_result: GeetestResult,
                                retry: bool = True):
    """
    发送短信验证码

    :param phone_number: 手机号
    :param mmt_data: 人机验证任务数据
    :param geetest_result: 人机验证结果数据
    :param retry: 是否允许重试
    """
    headers = HEADERS_WEBAPI.copy()
    headers["x-rpc-device_id"] = generate_device_id()
    try:
        async for attempt in tenacity.AsyncRetrying(stop=custom_attempt_times(retry), reraise=True,
                                                    wait=tenacity.wait_fixed(conf.preference.retry_interval)):
            with attempt:
                async with httpx.AsyncClient() as client:
                    res = await client.post(URL_CREATE_MOBILE_CAPTCHA,
                                            data=f"action_type=login&mmt_key={mmt_data.mmt_key}"
                                                 f"&geetest_challenge={mmt_data.challenge}"
                                                 f"&geetest_validate={geetest_result.validate}"
                                                 f"&geetest_seccode={geetest_result.seccode}"
                                                 f"&mobile={phone_number}"
                                                 f"&t={round(NtpTime.time() * 1000)}",
                                            headers=headers, timeout=conf.preference.timeout)
                if res.json()["data"]["msg"] == "成功" or res.json()["data"]["status"] == 1:
                    return CreateMobileCaptchaStatus(success=True)
                elif res.json()["data"]["msg"] == "图片验证码失败" or res.json()["data"]["status"] == -302:
                    return CreateMobileCaptchaStatus(incorrect_geetest=True)
    except IncorrectReturn:
        logger.error(f"发送短信验证码 - 服务器没有正确返回")
        logger.debug(f"网络请求返回: {res.text}")
        logger.debug(f"{traceback.format_exc()}")
        return CreateMobileCaptchaStatus(incorrect_return=True)
    except:
        logger.error(f"发送短信验证码 - 请求失败")
        logger.debug(f"{traceback.format_exc()}")
        return CreateMobileCaptchaStatus(network_error=True)


async def get_login_ticket_by_captcha(mobile_captcha_result: MobileCaptchaResult, retry: bool = True) -> Tuple[
    GetCookieStatus, Optional[BBSCookies]]:
    """
    通过短信验证码获取 login_ticket

    :param mobile_captcha_result: 短信验证结果数据
    :param retry: 是否允许重试
    """
    headers = HEADERS_WEBAPI.copy()
    headers["x-rpc-device_id"] = generate_device_id()
    try:
        async for attempt in tenacity.AsyncRetrying(stop=custom_attempt_times(retry),
                                                    wait=tenacity.wait_fixed(conf.preference.retry_interval)):
            with attempt:
                async with httpx.AsyncClient() as client:
                    res = await client.post(URL_LOGIN_CAPTCHA, headers=headers,
                                            content=f"mobile={mobile_captcha_result.phone_number}"
                                                    f"&mobile_captcha={mobile_captcha_result.captcha}"
                                                    "&source=user.mihoyo.com",
                                            timeout=conf.preference.time_out)
                res_json = res.json()
                if res_json["data"]["msg"] == "验证码错误" or res_json["data"]["info"] == "Captcha not match Err":
                    logger.info(f"短信验证码获取 login_ticket - 验证码错误")
                    return GetCookieStatus(incorrect_captcha=True), None
                bbs_cookies = BBSCookies.parse_obj(dict_from_cookiejar(
                    res.cookies.jar))
                if not bbs_cookies.login_ticket:
                    return GetCookieStatus(missing_login_ticket=True), None
                else:
                    return GetCookieStatus(success=True), bbs_cookies
    except IncorrectReturn:
        logger.error(f"短信验证码获取 login_ticket: 服务器没有正确返回")
        logger.debug(f"网络请求返回: {res.text}")
        logger.debug(f"{traceback.format_exc()}")
        return GetCookieStatus(incorrect_return=True), None
    except Exception:
        logger.error(f"短信验证码获取 login_ticket: 网络请求失败")
        logger.debug(f"{traceback.format_exc()}")
        return GetCookieStatus(network_error=True), None


async def get_stoken_by_login_ticket(bbs_cookies: BBSCookies, retry: bool = True) -> Tuple[
    GetCookieStatus, Optional[BBSCookies]]:
    """
    获取stoken

    :param bbs_cookies: 米游社Cookies，需要包含 login_ticket 和 bbs_uid
    :param retry: 是否允许重试
    """
    if not bbs_cookies.login_ticket:
        return GetCookieStatus(missing_login_ticket=True), None
    elif not bbs_cookies.bbs_uid:
        return GetCookieStatus(missing_bbs_uid=True), None
    try:
        async for attempt in tenacity.AsyncRetrying(stop=custom_attempt_times(retry), reraise=True,
                                                    wait=tenacity.wait_fixed(conf.preference.retry_interval)):
            with attempt:
                async with httpx.AsyncClient() as client:
                    res = await client.get(
                        URL_LOGIN_STOKEN.format(bbs_cookies.login_ticket, bbs_cookies.bbs_uid),
                        timeout=conf.preference.time_out)
                bbs_cookies.stoken = list(filter(
                    lambda data: data["name"] == "stoken", res.json()["data"]["list"]))[0]["token"]
                return GetCookieStatus(success=True), bbs_cookies
    except IncorrectReturn:
        logger.error(f"登录米哈游账号 - 获取stoken: 服务器没有正确返回")
        logger.debug(f"网络请求返回: {res.text}")
        logger.debug(f"{traceback.format_exc()}")
        return GetCookieStatus(incorrect_return=True), None
    except Exception:
        logger.error(f"登录米哈游账号 - 获取stoken: 网络请求失败")
        logger.debug(f"{traceback.format_exc()}")
        return GetCookieStatus(network_error=True), None


async def get_cookie_token_by_captcha(mobile_captcha_result: MobileCaptchaResult, retry: bool = True) -> Tuple[
    GetCookieStatus, Optional[BBSCookies]]:
    """
    通过短信验证码获取 cookie_token

    :param mobile_captcha_result: 短信验证结果数据
    :param retry: 是否允许重试
    """
    try:
        async for attempt in tenacity.AsyncRetrying(stop=custom_attempt_times(retry),
                                                    wait=tenacity.wait_fixed(conf.preference.retry_interval)):
            with attempt:
                async with httpx.AsyncClient() as client:
                    res = await client.post(URL_LOGIN_COOKIE_TOKEN, headers=HEADERS_LOGIN_STOKEN, json={
                        "is_bh2": False,
                        "mobile": str(mobile_captcha_result.phone_number),
                        "captcha": mobile_captcha_result.captcha,
                        "action_type": "login",
                        "token_type": 6
                    }, timeout=conf.preference.time_out)
                res_json = res.json()
                if res_json["data"]["msg"] == "验证码错误" or res_json["data"]["info"] == "Captcha not match Err":
                    logger.info(f"登录米哈游账号 - 验证码错误")
                    return GetCookieStatus(incorrect_captcha=True), None
                bbs_cookies = BBSCookies.parse_obj(
                    dict_from_cookiejar(res.cookies.jar))
                if not bbs_cookies.cookie_token:
                    return GetCookieStatus(missing_cookie_token=True), None
                else:
                    return GetCookieStatus(success=True), bbs_cookies
    except IncorrectReturn:
        logger.error(f"登录米哈游账号 - 获取stoken: 服务器没有正确返回")
        logger.debug(f"网络请求返回: {res.text}")
        logger.debug(f"{traceback.format_exc()}")
        return GetCookieStatus(incorrect_return=True), None
    except Exception:
        logger.error(f"登录米哈游账号 - 获取stoken: 网络请求失败")
        logger.debug(f"{traceback.format_exc()}")
        return GetCookieStatus(network_error=True), None


class Exchange:
    """
    米游币商品兑换任务
    """

    def __init__(self, exchange_plan: ExchangePlan, account: Optional[UserAccount] = None) -> None:
        """
        初始化兑换任务(仅导入参数)

        :param exchange_plan: 兑换计划数据
        :param account: 用户账户数据
        """
        self.initialized = False
        self.exchange_plan = exchange_plan
        if not account:
            account_in_plan = exchange_plan.account
            if isinstance(account_in_plan, int):
                self.account = conf.accounts[account_in_plan]
            else:
                self.account = account_in_plan
        else:
            self.account = account
        self.content = {
            "app_id": 1,
            "point_sn": "myb",
            "goods_id": self.exchange_plan.good_id,
            "exchange_num": 1
        }
        if self.exchange_plan.address_id:
            self.content.setdefault("address_id", self.exchange_plan.address_id)

    async def init_plan(self, retry: bool = True):
        """
        初始化兑换任务

        :param retry: 是否重试
        """
        try:
            async for attempt in tenacity.AsyncRetrying(stop=custom_attempt_times(retry),
                                                        wait=tenacity.wait_fixed(conf.preference.retry_interval)):
                with attempt:
                    async with httpx.AsyncClient() as client:
                        res = await client.get(
                            URL_CHECK_GOOD.format(self.exchange_plan.good_id), timeout=conf.preference.time_out)
                    good_info = Good.parse_obj(res.json()["data"])
                    if good_info.type == 2 and good_info.game_biz != "bbs_cn":
                        if not self.account.cookies.stoken:
                            logger.error(
                                f"米游币商品兑换 - 初始化兑换任务: 商品 {self.exchange_plan.good_id} 为游戏内物品，由于未配置stoken，放弃兑换")
                            return ExchangeStatus(missing_stoken=True)
                        elif self.account.cookies.stoken.find("v2__") == 0 and not self.account.cookies.mid:
                            logger.error(
                                f"米游币商品兑换 - 初始化兑换任务: 商品 {self.exchange_plan.good_id} 为游戏内物品，由于stoken为\"v2\"类型，且Cookies缺少mid，放弃兑换")
                            return ExchangeStatus(missing_mid=True)
                        elif not self.exchange_plan.game_uid:
                            logger.error(
                                f"米游币商品兑换 - 初始化兑换任务: 商品 {self.exchange_plan.good_id} 为游戏内物品，由于未配置对应游戏的账号UID，放弃兑换")
                            return ExchangeStatus(missing_game_uid=True)
                    # 若商品非游戏内物品，则直接返回，不进行下面的操作
                    else:
                        if not self.exchange_plan.address_id:
                            logger.error(
                                f"米游币商品兑换 - 初始化兑换任务: 商品 {self.exchange_plan.good_id} 为实体物品，由于未配置地址ID，放弃兑换")
                            return ExchangeStatus(missing_address=True)

                    if good_info.game not in ("bh3", "hk4e", "bh2", "nxx"):
                        logger.warning(
                            f"米游币商品兑换 - 初始化兑换任务: 暂不支持商品 {self.exchange_plan.good_id} 所属的游戏")
                        return ExchangeStatus(unsupported_game=True)

                    game_record_result = await get_game_record(self.account)
                    if not game_record_result[0]:
                        return ExchangeStatus(failed_getting_game_record=True)
                    else:
                        record_list = game_record_result[1]

                    for record in record_list:
                        if record.uid == self.exchange_plan.game_uid:
                            self.content.setdefault("uid", record.uid)
                            # 例: cn_gf01
                            self.content.setdefault("region", record.region)
                            # 例: hk4e_cn
                            self.content.setdefault(
                                "game_biz", good_info.game_biz)
                            break

                    self.initialized = True
                    return ExchangeStatus(success=True)
        except IncorrectReturn:
            logger.error(f"米游币商品兑换 - 初始化兑换任务: 服务器没有正确返回")
            logger.debug(f"网络请求返回: {res.text}")
            logger.debug(f"{traceback.format_exc()}")
            return ExchangeStatus(incorrect_return=True)
        except Exception:
            logger.error(f"米游币商品兑换 - 初始化兑换任务: 网络请求失败")
            logger.debug(f"{traceback.format_exc()}")
            return ExchangeStatus(network_error=True)

    async def start(self) -> Tuple[ExchangeStatus, Optional[ExchangeResult]]:
        """
        执行兑换操作
        """
        if not self.initialized:
            logger.error(f"商品：{self.exchange_plan.good_id} 未进行兑换任务初始化，放弃兑换")
            return ExchangeStatus(init_required=True), None
        else:
            headers = HEADERS_EXCHANGE
            headers["x-rpc-device_id"] = self.account.device_id_ios
            try:
                async with httpx.AsyncClient() as client:
                    res = await client.post(
                        URL_EXCHANGE, headers=headers, json=self.content, cookies=self.account.cookies,
                        timeout=conf.preference.time_out)
                if not check_login(res.text):
                    logger.info(
                        f"米游币商品兑换 - 执行兑换: 用户 {self.account.bbs_uid} 登录失效")
                    logger.debug(f"网络请求返回: {res.text}")
                    return ExchangeStatus(login_failed=True), None
                if res.json()["message"] == "OK":
                    logger.info(
                        f"米游币商品兑换 - 执行兑换: 用户 {self.account.bbs_uid} 商品 {self.exchange_plan.good_id} 兑换成功！可以自行确认。")
                    logger.debug(f"网络请求返回: {res.text}")
                    return ExchangeStatus(success=True), ExchangeResult(result=True, return_data=res.json())
                else:
                    logger.info(
                        f"米游币商品兑换 - 执行兑换: 用户 {self.account.bbs_uid} 商品 {self.exchange_plan.good_id} 兑换失败，可以自行确认。")
                    logger.debug(f"网络请求返回: {res.text}")
                    return ExchangeStatus(success=True), ExchangeResult(result=False, return_data=res.json())
            except IncorrectReturn:
                logger.error(
                    f"米游币商品兑换 - 执行兑换: 用户 {self.account.bbs_uid} 商品 {self.exchange_plan.good_id} 服务器没有正确返回")
                logger.debug(f"网络请求返回: {res.text}")
                logger.debug(f"{traceback.format_exc()}")
                return ExchangeStatus(incorrect_return=True), None
            except Exception:
                logger.error(
                    f"米游币商品兑换 - 执行兑换: 用户 {self.account.bbs_uid} 商品 {self.exchange_plan.good_id} 请求失败")
                logger.debug(f"{traceback.format_exc()}")
                return ExchangeStatus(network_error=True), None
