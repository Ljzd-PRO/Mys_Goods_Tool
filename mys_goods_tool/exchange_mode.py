import asyncio
import random
import sys
from datetime import datetime
from typing import Callable, Optional, TypeVar
from urllib.parse import urlparse

import ping3
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from textual.containers import Container
from textual.events import Event

from mys_goods_tool.api import good_exchange, URL_EXCHANGE
from mys_goods_tool.data_model import ExchangeStatus
from mys_goods_tool.user_data import config as conf, ExchangePlan, Preference, ExchangeResult
from mys_goods_tool.utils import logger, LOG_FORMAT

# NtpTime.sync()

_T = TypeVar("_T")

ExchangeCallback = Callable[[ExchangeStatus, Optional[ExchangeResult]], None]
# AsyncExchangeCallback = Callable[[ExchangeStatus, Optional[ExchangeResult]], Coroutine[ExchangeStatus, Optional[
#     ExchangeResult], None]]
"""兑换回调函数类型"""


def _on_fail(status: ExchangeStatus, result: Optional[ExchangeResult]):
    if status.network_error:
        error = "网络错误"
    elif status.missing_stoken:
        error = "商品为游戏内物品，但 Cookies 缺少 stoken"
    elif status.missing_mid:
        error = "商品为游戏内物品，但 stoken 为 'v2' 类型同时 Cookies 缺少 mid"
    elif status.missing_address:
        error = "商品为实体物品，但未配置收货地址"
    elif status.missing_game_uid:
        error = "商品为游戏内物品，但未配置对应游戏的账号UID"
    elif status.unsupported_game:
        error = "暂不支持兑换对应分区/游戏的商品"
    elif status.failed_getting_game_record:
        error = "获取用户 GameRecord 失败"
    elif status.init_required:
        error = "未进行兑换任务初始化"
    elif status.account_not_found:
        error = "账号不存在"
    else:
        error = "未知错误"

    logger.error(f"用户 {result.plan.account.bbs_uid} - {result.plan.good.general_name} 兑换失败，原因：{error}")


def _connection_test():
    """
    连接测试
    """
    hostname = urlparse(URL_EXCHANGE).hostname
    result = ping3.ping(str(hostname), unit="ms")
    if result is None:
        logger.info(f"Ping 商品兑换API服务器 {hostname} 超时")
    elif result is False:
        logger.info(f"Ping 商品兑换API服务器 {hostname} 失败")
    else:
        logger.info(f"Ping 商品兑换API服务器 {hostname} 延迟 {round(result, 2)} ms")


def get_scheduler(on_success: ExchangeCallback,
                  on_fail: ExchangeCallback):
    """
    获取兑换计划调度器
    """
    scheduler = AsyncIOScheduler()
    scheduler.configure(timezone=conf.preference.timezone or Preference.timezone)

    if conf.preference.enable_connection_test:
        interval = conf.preference.connection_test_interval or Preference.connection_test_interval
        scheduler.add_job(_connection_test, "interval", seconds=interval)

    for plan in conf.exchange_plans:
        scheduler.add_job(exchange_begin,
                          "date",
                          args=(plan, on_success, on_fail),
                          run_date=datetime.fromtimestamp(plan.good.time)
                          )

    return scheduler


async def exchange_begin(plan: ExchangePlan,
                         on_success: ExchangeCallback,
                         on_fail: ExchangeCallback):
    """
    到点后执行兑换

    :param plan: 兑换计划
    :param on_success: 兑换成功后的回调函数
    :param on_fail: 兑换失败后的回调函数
    """
    logger.info(f"{plan.good.general_name} - {plan.good.time_text} 定时器触发，开始兑换")
    random_x, random_y = conf.preference.exchange_latency
    latency = random.uniform(random_x, random_y)
    await asyncio.sleep(latency)
    exchange_status, exchange_result = await good_exchange(plan)
    logger.info(f"{plan.good.general_name} - {plan.good.time_text} 兑换请求已发送")
    if exchange_result:
        if exchange_result.result:
            on_success(exchange_status, exchange_result)
        else:
            on_fail(exchange_status, exchange_result)
    else:
        on_fail(exchange_status, exchange_result)


def exchange_mode_simple():
    """
    普通文本模式（无Textual）
    """
    logger.add(sys.stdout, diagnose=True, format=LOG_FORMAT, level="DEBUG")
    if not conf.exchange_plans:
        logger.info("无兑换计划需要执行")
        return

    def on_success(_: ExchangeStatus, result: Optional[ExchangeResult]):
        logger.info(f"用户 {result.plan.account.bbs_uid} - {result.plan.good.general_name} 兑换成功")

    def on_fail(_: ExchangeStatus, result: Optional[ExchangeResult]):
        logger.error(f"用户 {result.plan.account.bbs_uid} - {result.plan.good.general_name} 兑换失败")

    scheduler = get_scheduler(on_success, on_fail)
    try:
        scheduler.start()
        logger.info("兑换计划定时器已启动")
        asyncio.get_event_loop().run_forever()
    except KeyboardInterrupt:
        scheduler.shutdown()
        logger.info("兑换计划定时器已停止")


class EnterExchangeMode(Event):
    """
    进入兑换模式的事件
    """
    pass


class ExchangeModeView(Container):
    """
    兑换模式视图
    """
    DEFAULT_CSS = """
    ExchangeModeView {
        overflow: auto;
    }
    """
    # TODO 兑换模式视图
