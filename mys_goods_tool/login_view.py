from __future__ import annotations

import asyncio
import queue
from typing import NamedTuple, Tuple, Optional, Set
from urllib.parse import urlencode

from rich.markdown import Markdown
from textual.app import ComposeResult
from textual.widgets import (
    Input
)

from mys_goods_tool.api import create_mobile_captcha, create_mmt, get_login_ticket_by_captcha, \
    get_multi_token_by_login_ticket, get_cookie_token_by_stoken, get_stoken_v2_by_v1, get_ltoken_by_stoken, \
    get_device_fp
from mys_goods_tool.custom_css import *
from mys_goods_tool.custom_widget import RadioStatus, StaticStatus, ControllableButton, LoadingDisplay
from mys_goods_tool.data_model import GeetestResult, MmtData, GetCookieStatus
from mys_goods_tool.exchange_plan_view import ExchangePlanView
from mys_goods_tool.geetest import GeetestProcessManager, SetAddressProcessManager
from mys_goods_tool.user_data import config as conf, UserAccount, CONFIG_PATH
from mys_goods_tool.utils import logger


class LoginView(Container):
    """
    登录页面
    """
    DEFAULT_CSS = """
    LoginView {
        height: auto;
    }
    """

    def compose(self) -> ComposeResult:
        yield CaptchaLoginInformation()
        yield PhoneForm()
        yield CaptchaForm()


class CaptchaLoginInformation(Container):
    """
    短信验证登录页面的信息提示区域
    """
    DEFAULT_CSS = """
    CaptchaLoginInformation {
        height: auto;
        margin: 1 0;
        overflow: hidden;
    }

    CaptchaLoginInformation Horizontal {
        align: center middle;
    }
    """

    RadioTuple = NamedTuple("RadioTuple",
                            create_geetest=RadioStatus,
                            http_server=RadioStatus,
                            geetest_finished=RadioStatus,
                            create_captcha=RadioStatus,
                            login_ticket_by_captcha=RadioStatus,
                            multi_token_by_login_ticket=RadioStatus,
                            get_stoken_v2=RadioStatus,
                            get_ltoken_by_stoken=RadioStatus,
                            cookie_token_by_stoken=RadioStatus,
                            login_finished=RadioStatus
                            )

    StaticTuple = NamedTuple("StaticTuple",
                             geetest_title=Static,
                             geetest_text=StaticStatus
                             )

    radio_tuple = RadioTuple(
        create_geetest=RadioStatus("短信验证码 - 申请人机验证任务"),
        http_server=RadioStatus("开启人机验证网页服务器"),
        geetest_finished=RadioStatus("完成人机验证"),
        create_captcha=RadioStatus("发出短信验证码"),
        login_ticket_by_captcha=RadioStatus("通过验证码获取 login_ticket"),
        multi_token_by_login_ticket=RadioStatus("通过 login_ticket 获取 stoken"),
        get_stoken_v2=RadioStatus("获取 v2 版本 stoken 和 mid"),
        get_ltoken_by_stoken=RadioStatus("通过 stoken_v2 获取 ltoken"),
        cookie_token_by_stoken=RadioStatus("通过 stoken_v2 获取 cookie_token"),
        login_finished=RadioStatus("完成登录")
    )

    SAVE_TEXT = str(CONFIG_PATH)
    GEETEST_TEXT = "- 暂无需要完成的人机验证任务 -"

    static_tuple = StaticTuple(
        geetest_title=Static(Markdown("## GEETEST人机验证链接")),
        geetest_text=StaticStatus(GEETEST_TEXT)
    )

    radio_set = CaptchaStepSet(*radio_tuple)
    static_set = CaptchaTips(*static_tuple)

    def compose(self) -> ComposeResult:
        yield Horizontal(self.radio_set, self.static_set)


class PhoneForm(LoginForm):
    """
    手机号 表单
    """
    input = Input(placeholder="手机号", id="login_phone")
    """手机号输入框"""
    device_id: Optional[str] = None
    """人机验证过程的设备ID"""

    ButtonTuple = NamedTuple("ButtonTuple",
                             send=ControllableButton,
                             stop_geetest=ControllableButton,
                             success=ControllableButton,
                             error=ControllableButton)

    def __init__(self):
        super().__init__()

        self.mmt_data: Optional[MmtData] = None
        """GEETEST行为验证任务数据"""
        self.geetest_manager: Optional[GeetestProcessManager] = None
        """包含进程池的GEETEST验证HTTP服务器 进程管理器"""
        self.set_address_manager = SetAddressProcessManager(self.set_address_callback,
                                                            self.set_address_error_callback)
        """包含进程池的可用监听地址获取 进程管理器"""
        self.loop = asyncio.get_event_loop()
        """事件循环"""
        self.loop_tasks: Set[asyncio.Task] = set()
        """异步任务集合（保留其强引用）"""
        self.before_create_captcha = True
        """当前状态是否处于按下“发送短信验证码”按钮之前"""

        self.loading = LoadingDisplay()
        self.loading.hide()

        self.button = self.ButtonTuple(
            send=ControllableButton("发送短信验证码", variant="primary", id="create_captcha_send"),
            stop_geetest=ControllableButton("放弃人机验证", variant="warning", id="create_captcha_stop_geetest"),
            success=ControllableButton("完成", variant="success", id="create_captcha_success"),
            error=ControllableButton("返回", variant="error", id="create_captcha_error")
        )
        for button in self.button[1:]:
            button.hide()

    def compose(self) -> ComposeResult:
        yield Static("手机号", classes="label")
        yield self.input
        yield Static()
        yield from self.button
        yield Static()
        yield self.loading

    def close_create_captcha_send(self):
        """
        关闭发送短信验证码按钮
        """
        self.loading.hide()
        self.button.send.hide()
        self.button.send.enable()

    def httpd_error_callback(self, exception: BaseException):
        """
        GEETEST验证HTTP服务器启动失败时的回调函数
        """
        logger.error("用于Geetest验证的HTTP服务器启动失败")
        logger.debug(exception)
        CaptchaLoginInformation.radio_tuple.http_server.turn_off()
        self.button.stop_geetest.hide()
        self.button.error.show()

    async def listen_result(self):
        """
        等待GEETEST验证结果的异步任务
        """
        self.app.notice("请前往链接进行验证")
        while True:
            await asyncio.sleep(1)
            try:
                geetest_result: GeetestResult = self.geetest_manager.result_queue.get_nowait()
            except queue.Empty:
                continue
            else:
                logger.info(f"已收到Geetest验证结果数据，将发送验证码至 {self.input.value}")
                CaptchaLoginInformation.radio_tuple.geetest_finished.turn_on()
                self.loading.show()
                create_captcha_status, _ = await create_mobile_captcha(
                    int(self.input.value),
                    self.mmt_data,
                    geetest_result,
                    device_id=PhoneForm.device_id
                )
                if create_captcha_status:
                    self.loading.hide()
                    logger.info(f"短信验证码已发送至 {self.input.value}")
                    CaptchaLoginInformation.radio_tuple.create_captcha.turn_on()
                    CaptchaLoginInformation.static_tuple.geetest_text.change_text(CaptchaLoginInformation.GEETEST_TEXT,
                                                                                  "center")
                    self.button.success.show()
                    self.button.stop_geetest.hide()

                    self.geetest_manager.pipe[1].send(True)
                    await self.geetest_manager.force_stop_later(10)

                    self.app.notice("短信验证码已发送至 [green]" + self.input.value + "[/]")
                    break
                else:
                    self.loading.hide()
                    self.button.error.show()
                    self.button.stop_geetest.hide()
                    CaptchaLoginInformation.static_tuple.geetest_text.change_text(CaptchaLoginInformation.GEETEST_TEXT,
                                                                                  "center")
                    self.app.notice("[red]短信验证码发送失败[/]")

    def set_address_callback(self, address: Tuple[str, int]):
        """
        可用监听地址获取成功时的回调函数

        :param address: 返回的可用地址
        """
        if not address:
            self.close_create_captcha_send()
            self.button.error.show()
            return
        self.geetest_manager = GeetestProcessManager(address, error_httpd_callback=self.httpd_error_callback)
        logger.info(f"尝试在 http://{address[0]}:{address[1]} 上启动用于Geetest验证的HTTP服务器")
        self.geetest_manager.start()

        self.close_create_captcha_send()
        self.button.stop_geetest.show()
        CaptchaLoginInformation.radio_tuple.http_server.turn_on()

        task = self.loop.create_task(self.listen_result())
        self.loop_tasks.add(task)
        task.add_done_callback(self.loop_tasks.discard)

        params = {
            "gt": self.mmt_data.gt,
            "mmtKey": self.mmt_data.mmt_key,
            "riskType": self.mmt_data.risk_type
        }
        url_params = urlencode(params)
        link = f"http://{address[0]}:{address[1]}/index.html?{url_params}"
        link_localized = f"http://{address[0]}:{address[1]}/localized.html?{url_params}"
        CaptchaLoginInformation.static_tuple.geetest_text.change_text(
            renderable=f"\n- 请前往链接进行验证：\n"
                       f"[@click=app.open_link('{link}')]{link}[/]\n"
                       f"\n- 如果页面加载慢或者出错，尝试：\n"
                       f"[@click=app.open_link('{link_localized}')]{link_localized}[/]\n"
                       f"\n如果你在使用SSH或WSL，无法跳转链接，可前往日志文件复制验证链接",
            text_align="left")
        logger.info(f"请前往链接进行人机验证：{link}")
        logger.info(f"如果页面加载慢或者出错，尝试：{link_localized}")

    def set_address_error_callback(self, exception: BaseException):
        """
        可用监听地址获取失败时的回调函数
        """
        logger.error("尝试获取可用HTTP监听地址失败")
        logger.debug(exception)
        self.close_create_captcha_send()
        self.button.error.show()
        self.app.notice("[red]尝试获取可用HTTP监听地址失败！[/]")
        return

    async def create_captcha(self):
        """
        发送验证码的完整操作
        """
        if not self.before_create_captcha:
            return
        elif not self.input.value:
            self.app.notice("登录信息缺少 [bold red]手机号[/] ！")
            return
        self.before_create_captcha = False

        [i.turn_off() for i in CaptchaLoginInformation.radio_tuple]
        self.button.send.disable()
        self.loading.show()

        create_mmt_status, self.mmt_data, PhoneForm.device_id, _ = await create_mmt()
        if not create_mmt_status:
            self.close_create_captcha_send()
            self.button.error.show()
            self.app.notice("[red]获取Geetest行为验证任务数据失败！[/]")
            return
        else:
            logger.info(f"已成功获取Geetest行为验证任务数据 {self.mmt_data}")
            CaptchaLoginInformation.radio_tuple.create_geetest.turn_on()
            self.set_address_manager.start()

        return create_mmt_status

    async def on_input_submitted(self, _: Input.Submitted):
        await self.create_captcha()

    async def _on_button_pressed(self, event: ControllableButton.Pressed):
        if event.button.id == "create_captcha_send":
            # 按下“发送短信验证码”按钮时触发的事件

            await self.create_captcha()

        elif event.button.id == "create_captcha_stop_geetest":
            # 按下“放弃人机验证”按钮时触发的事件

            CaptchaLoginInformation.static_tuple.geetest_text.change_text(CaptchaLoginInformation.GEETEST_TEXT,
                                                                          "center")
            [i.turn_off() for i in CaptchaLoginInformation.radio_tuple]
            self.geetest_manager.pipe[1].send(True)
            self.button.stop_geetest.hide()
            self.button.send.show()
            self.before_create_captcha = True
            await self.geetest_manager.force_stop_later(10)

        elif event.button.id in ["create_captcha_success", "create_captcha_error"]:
            # 按下“完成（成功）”或“返回（出错）”按钮时触发的事件

            if event.button.id == "create_captcha_error":
                [i.turn_off() for i in CaptchaLoginInformation.radio_tuple]
            self.button.success.hide()
            self.button.error.hide()
            self.button.send.show()
            self.before_create_captcha = True


class CaptchaForm(LoginForm):
    """
    验证码 表单
    """
    ButtonTuple = NamedTuple("ButtonTuple", login=ControllableButton, success=ControllableButton,
                             error=ControllableButton)

    def __init__(self):
        super().__init__()
        self.login_result: Optional[GetCookieStatus] = None
        """登录操作返回值"""
        self.before_login: bool = True
        """当前状态是否在登录操作之前（不处于正在登录的状态）"""

        self.input = Input(placeholder="若发送验证码失败，也可前往米哈游通信证页面手动发送", id="login_captcha")

        self.loading = LoadingDisplay()
        self.loading.hide()

        self.button = self.ButtonTuple(
            login=ControllableButton("登录 / 刷新Cookies", variant="primary", id="login"),
            success=ControllableButton("完成", variant="success", id="login_success"),
            error=ControllableButton("返回", variant="error", id="login_error")
        )
        for i in self.button[1:]:
            i.hide()

    def compose(self) -> ComposeResult:
        yield Static("验证码", classes="label")
        yield self.input
        yield Static()
        yield from self.button
        yield Static()
        yield self.loading

    def close_login(self):
        self.button.login.hide()
        self.button.login.enable()

    async def login(self):
        """
        登录的完整操作
        """
        if not self.before_login:
            return
        elif not PhoneForm.input.value:
            self.app.notice("登录信息缺少 [bold red]手机号[/] ！")
            return
        elif not self.input.value.isdigit() and self.input.value:
            self.app.notice("登录信息 [bold red]验证码[/] 需要是数字或为空（刷新Cookies）！")
            return
        self.before_login = False

        self.button.login.disable()
        self.loading.show()

        account: Optional[UserAccount] = None
        login_status: GetCookieStatus = GetCookieStatus(success=False)
        phone_number = PhoneForm.input.value
        captcha = int(self.input.value) if self.input.value.isdigit() else self.input.value

        # 1. 通过短信验证码获取 login_ticket / 使用已有 login_ticket
        if captcha:
            login_status, cookies = await get_login_ticket_by_captcha(phone_number,
                                                                      captcha,
                                                                      PhoneForm.device_id)
            if login_status:
                logger.info(f"用户 {phone_number} 成功获取 login_ticket: {cookies.login_ticket}")
                account = conf.accounts.get(cookies.bbs_uid)
                """当前的账户数据对象"""
                if not account or not account.cookies:
                    conf.accounts.update({
                        cookies.bbs_uid: UserAccount(phone_number=phone_number, cookies=cookies)
                    })
                    account = conf.accounts[cookies.bbs_uid]
                else:
                    account.cookies.update(cookies)
                fp_status, account.device_fp = await get_device_fp(account.device_id_ios)
                if fp_status:
                    logger.info(f"成功获取 device_fp: {account.device_fp}")
                conf.save()
                CaptchaLoginInformation.radio_tuple.login_ticket_by_captcha.turn_on()
        else:
            account_list = list(filter(lambda x: x.phone_number == phone_number, conf.accounts.values()))
            account = account_list[0] if account_list else None
            if not account:
                self.app.notice(f"手机号为 [bold red]{phone_number}[/] 的账户暂未被绑定！")
                self.loading.hide()
                self.button.error.show()
                self.close_login()
                return

        # 2. 通过 login_ticket 获取 stoken 和 ltoken
        if login_status or account:
            login_status, cookies = await get_multi_token_by_login_ticket(account.cookies)
            if login_status:
                logger.info(f"用户 {phone_number} 成功获取 stoken: {cookies.stoken}")
                account.cookies.update(cookies)
                conf.save()
                CaptchaLoginInformation.radio_tuple.multi_token_by_login_ticket.turn_on()

                # 3. 通过 stoken_v1 获取 stoken_v2 和 mid
                login_status, cookies = await get_stoken_v2_by_v1(account.cookies, account.device_id_ios)
                if login_status:
                    logger.info(f"用户 {phone_number} 成功获取 stoken_v2: {cookies.stoken_v2}")
                    account.cookies.update(cookies)
                    conf.save()
                    CaptchaLoginInformation.radio_tuple.get_stoken_v2.turn_on()

                    # 4. 通过 stoken_v2 获取 ltoken
                    login_status, cookies = await get_ltoken_by_stoken(account.cookies, account.device_id_ios)
                    if login_status:
                        logger.info(f"用户 {phone_number} 成功获取 ltoken: {cookies.ltoken}")
                        account.cookies.update(cookies)
                        conf.save()
                        CaptchaLoginInformation.radio_tuple.get_ltoken_by_stoken.turn_on()

                        # 5. 通过 stoken_v2 获取 cookie_token
                        login_status, cookies = await get_cookie_token_by_stoken(account.cookies, account.device_id_ios)
                        if login_status:
                            logger.info(f"用户 {phone_number} 成功获取 cookie_token: {cookies.cookie_token}")
                            account.cookies.update(cookies)
                            conf.save()
                            CaptchaLoginInformation.radio_tuple.cookie_token_by_stoken.turn_on()

                            # TODO 2023/04/12 此处如果可以模拟App的登录操作，再标记为登录完成，更安全
                            CaptchaLoginInformation.radio_tuple.login_finished.turn_on()
                            self.app.notice(f"用户 [bold green]{phone_number}[/] 登录成功！")
                            self.button.success.show()

                            ExchangePlanView.account_content.update_data()

        self.loading.hide()
        if not login_status:
            notice_text = "登录失败：[bold red]"
            if login_status.incorrect_captcha:
                notice_text += "验证码错误！"
            elif login_status.login_expired:
                notice_text += "登录失效！"
            elif login_status.incorrect_return:
                notice_text += "服务器返回错误！"
            elif login_status.network_error:
                notice_text += "网络连接失败！"
            elif login_status.missing_bbs_uid:
                notice_text += "Cookies缺少 bbs_uid（例如 ltuid, stuid）"
            elif login_status.missing_login_ticket:
                notice_text += "Cookies缺少 login_ticket！"
            elif login_status.missing_cookie_token:
                notice_text += "Cookies缺少 cookie_token！"
            elif login_status.missing_stoken:
                notice_text += "Cookies缺少 stoken！"
            elif login_status.missing_stoken_v1:
                notice_text += "Cookies缺少 stoken_v1"
            elif login_status.missing_stoken_v2:
                notice_text += "Cookies缺少 stoken_v2"
            elif login_status.missing_mid:
                notice_text += "Cookies缺少 mid"
            else:
                notice_text += "未知错误！"
            notice_text += "[/] 如果部分步骤成功，你仍然可以尝试获取收货地址、兑换等功能"
            self.button.error.show()
            self.app.notice(notice_text)

        self.close_login()
        return login_status

    async def on_input_submitted(self, _: Input.Submitted) -> None:
        await self.login()

    async def _on_button_pressed(self, event: ControllableButton.Pressed) -> None:
        if event.button.id == "login":
            # 按下“登录”按钮时触发的事件

            await self.login()

        elif event.button.id in ["login_error", "login_success"]:
            # 按下“完成（成功）”或“返回（出错）”按钮时触发的事件

            if event.button.id == "login_success":
                [i.turn_off() for i in CaptchaLoginInformation.radio_tuple]
            self.button.login.show()
            self.button.error.hide()
            self.button.success.hide()
            self.before_login = True
