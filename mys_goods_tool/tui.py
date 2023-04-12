from __future__ import annotations

import asyncio
import queue
from importlib.metadata import version
from typing import NamedTuple, Tuple, Optional, Set

from httpx import Cookies
from rich.console import RenderableType
from rich.markdown import Markdown
from rich.pretty import Pretty
from rich.text import Text
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.events import Event
from textual.reactive import reactive
from textual.widgets import (
    Button,
    Footer,
    Header,
    Input,
    Switch,
    LoadingIndicator, RadioButton
)

from mys_goods_tool.api import create_mobile_captcha, create_mmt, get_login_ticket_by_captcha, \
    get_multi_token_by_login_ticket, get_cookie_token_by_stoken, get_stoken_v2_by_v1
from mys_goods_tool.custom_css import *
from mys_goods_tool.data_model import GeetestResult, MmtData, GetCookieStatus
from mys_goods_tool.geetest import GeetestProcessManager, SetAddressProcessManager
from mys_goods_tool.user_data import config as conf, UserAccount, CONFIG_PATH, ROOT_PATH
from mys_goods_tool.utils import LOG_FORMAT, logger

WELCOME_MD = """
# 米游社商品兑换工具

修复获取**米游社**uid失败导致检查游戏账户失败的问题  
如报错：

```
2023-01-18 15:46:13  DEBUG  checkGame_response: {"data":null,"message":"Invalid uid","retcode":-1}
```

米游社米游币可兑换的商品通常份数很少，担心抢不到的话可以使用这个脚本，可设置多个商品。

建议同时自己也用手机操作去抢，以免脚本出问题。

## 使用说明

- 在兑换开始之前运行主程序。

- 建议先把兑换时间设定为当前时间往后的一两分钟，测试一下是否能正常兑换，如果返回未到时间或者库存不足就基本没有问题。

- **可前往`./logs/mys_goods_tool.log`查看日志**

## 其他
- 仅供学习时参考

- 相似项目推荐:  \
**mysTool - 米游社辅助工具插件**  \
简介：NoneBot2 插件 | 米游社工具-每日米游币任务、游戏签到、商品兑换、免抓包登录、原神树脂提醒
"""

RICH_MD = """

Textual is built on **Rich**, the popular Python library for advanced terminal output.

Add content to your Textual App with Rich *renderables* (this text is written in Markdown and formatted with Rich's 
Markdown class). 

Here are some examples:


"""

DATA = {
    "foo": [
        3.1427,
        (
            "Paul Atreides",
            "Vladimir Harkonnen",
            "Thufir Hawat",
            "Gurney Halleck",
            "Duncan Idaho",
        ),
    ],
}


class RadioStatus(RadioButton, can_focus=False):
    """
    完成的进度节点，不允许点击交互
    可通过触发事件以即时修改value属性
    """

    class ChangeStatus(Event):
        """
        请求按钮状态修改的事件
        """

        def __init__(self, radio_status: RadioStatus):
            self.radio_status = radio_status
            super().__init__()

    class TurnOn(ChangeStatus):
        """请求按钮状态修改为亮起的事件"""
        pass

    class TurnOff(ChangeStatus):
        """请求按钮状态修改为熄灭的事件"""
        pass

    def turn_on(self):
        """修改按钮状态为亮起"""
        self.post_message(RadioStatus.TurnOn(self))

    def turn_off(self):
        """修改按钮状态为熄灭"""
        self.post_message(RadioStatus.TurnOff(self))

    def toggle(self) -> None:
        """
        重写按钮交互，交互时不会改变按钮状态
        """
        pass


class StaticStatus(Static):
    """
    实时文本说明，可通过触发事件以即时修改文本属性
    """

    class ChangeRenderable(Event):
        """
        请求renderable属性（此处与文本相关）修改的事件
        """

        def __init__(self, static_status: StaticStatus, renderable: RenderableType, text_align: Optional[str] = None):
            self.static_status = static_status
            self.renderable = renderable
            self.text_align = text_align
            super().__init__()

    def change_text(self, renderable: RenderableType, text_align: Optional[str] = None) -> None:
        """修改renderable属性（此处与文本相关）"""
        self.post_message(StaticStatus.ChangeRenderable(self, renderable, text_align))


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

    class Tips(Container):
        DEFAULT_CSS = """
        Tips {
            height: 100%;
            width: 45%;
            align: right middle;
            margin: 0 2 0 0;
            padding: 1;
            overflow-x: auto;
            overflow-y: auto;
            border: round #666;
        }
    
        App.-light-mode Tips {
            border: round #CCC;
        }
        
        Tips StaticStatus {
            width: 100%;
            align: center top;
            text-align: center;
        }
        """

    class StepSet(Container):
        DEFAULT_CSS = """
        StepSet {
            height: auto;
            width: 45%;
            align: left middle;
            margin: 0 2 0 0;
            overflow: hidden;
            border: round #666;
        }
        
        App.-light-mode StepSet {
            border: round #CCC;
        }
        
        StepSet RadioStatus {
            margin: 1 2;
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
        multi_token_by_login_ticket=RadioStatus("通过 login_ticket 获取 stoken 和 ltoken"),
        get_stoken_v2=RadioStatus("获取 v2 版本 stoken"),
        cookie_token_by_stoken=RadioStatus("通过 stoken 获取 cookie_token"),
        login_finished=RadioStatus("完成登录")
    )

    SAVE_TEXT = str(CONFIG_PATH)
    GEETEST_TEXT = "- 暂无需要完成的人机验证任务 -"

    static_tuple = StaticTuple(
        geetest_title=Static(Markdown("## GEETEST人机验证链接")),
        geetest_text=StaticStatus(GEETEST_TEXT)
    )

    radio_set = StepSet(*radio_tuple)
    static_set = Tips(*static_tuple)

    def compose(self) -> ComposeResult:
        yield Horizontal(self.radio_set, self.static_set)

    async def on_event(self, event: Event) -> None:
        """
        重写事件处理，在收到请求修改CaptchaLoginInformation内的各种组件属性的事件时，完成修改
        这是因为组件只会在事件结束后进行刷新，如果有事件需要修改多个组件属性，就无法一个个生效，需要交由新的事件处理。

        :param event: 事件
        """
        if isinstance(event, RadioStatus.TurnOn):
            event.radio_status.value = True
        elif isinstance(event, RadioStatus.TurnOff):
            event.radio_status.value = False
        elif isinstance(event, StaticStatus.ChangeRenderable):
            event.static_status.update(event.renderable)
            if event.text_align:
                event.static_status.styles.text_align = event.text_align
        await super().on_event(event)


class ButtonDisplay(Button):
    """
    带隐藏显示控制方法的按钮
    """

    def show(self):
        """
        显示
        """
        self.display = BLOCK

    def hide(self):
        """
        隐藏
        """
        self.display = NONE


class PhoneForm(LoginForm):
    """
    手机号 表单
    """
    input = Input(placeholder="手机号", id="login_phone")
    """手机号输入框"""
    cookies: Optional[Cookies] = None
    """人机验证过程产生的Cookies，可供登录用"""

    ButtonTuple = NamedTuple("ButtonTuple", send=ButtonDisplay, stop_geetest=ButtonDisplay, success=ButtonDisplay,
                             error=ButtonDisplay)

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

        self.loading = LoadingIndicator()
        self.loading.display = NONE

        self.button = self.ButtonTuple(
            send=ButtonDisplay("发送短信验证码", variant="primary", id="create_captcha_send"),
            stop_geetest=ButtonDisplay("放弃人机验证", variant="warning", id="create_captcha_stop_geetest"),
            success=ButtonDisplay("完成", variant="success", id="create_captcha_success"),
            error=ButtonDisplay("返回", variant="error", id="create_captcha_error")
        )
        [i.hide() for i in self.button[1:]]

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
        self.loading.display = NONE
        self.button.send.hide()
        self.button.send.disabled = False

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
        while True:
            await asyncio.sleep(1)
            try:
                geetest_result: GeetestResult = self.geetest_manager.result_queue.get_nowait()
            except queue.Empty:
                continue
            else:
                logger.info(f"已收到Geetest验证结果数据 {geetest_result}，将发送验证码至 {self.input.value}")
                CaptchaLoginInformation.radio_tuple.geetest_finished.turn_on()
                self.loading.display = BLOCK
                create_captcha_return = await create_mobile_captcha(int(self.input.value), self.mmt_data,
                                                                    geetest_result)
                if create_captcha_return[0]:
                    self.loading.display = NONE

                    logger.info(f"短信验证码已发送至 {self.input.value}")
                    PhoneForm.cookies.update(create_captcha_return[1])

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
                    self.loading.display = NONE
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

        listen_result_task = self.loop.create_task(self.listen_result())
        self.loop_tasks.add(listen_result_task)
        listen_result_task.add_done_callback(self.loop_tasks.discard)

        link = f"http://{address[0]}:{address[1]}/index.html?gt={self.mmt_data.gt}&challenge={self.mmt_data.challenge}"
        link_localized = f"http://{address[0]}:{address[1]}/localized.html?gt={self.mmt_data.gt}&challenge={self.mmt_data.challenge}"
        CaptchaLoginInformation.static_tuple.geetest_text.change_text(
            renderable=f"\n- 请前往链接进行验证：\n"
                       f"[@click=app.open_link('{link}')]{link}[/]\n"
                       f"\n- 如果页面加载慢或者出错，尝试：\n"
                       f"[@click=app.open_link('{link_localized}')]{link_localized}[/]",
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
        self.button.send.disabled = True
        self.loading.display = BLOCK

        create_mmt_return = await create_mmt()
        if not create_mmt_return[0]:
            self.close_create_captcha_send()
            self.button.error.show()
            self.app.notice("[red]获取Geetest行为验证任务数据失败！[/]")
            return
        else:
            logger.info(f"已成功获取Geetest行为验证任务数据 {create_mmt_return[1]}")
            PhoneForm.cookies = create_mmt_return[2]
            CaptchaLoginInformation.radio_tuple.create_geetest.turn_on()
            self.mmt_data = create_mmt_return[1]
            self.set_address_manager.start()

        return create_mmt_return[0]

    async def on_input_submitted(self, _: Input.Submitted):
        await self.create_captcha()

    async def on_button_pressed(self, event: Button.Pressed):
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
    ButtonTuple = NamedTuple("ButtonTuple", login=ButtonDisplay, success=ButtonDisplay, error=ButtonDisplay)

    def __init__(self):
        super().__init__()
        self.login_result: Optional[GetCookieStatus] = None
        """登录操作返回值"""
        self.before_login: bool = True
        """当前状态是否在登录操作之前（不处于正在登录的状态）"""

        self.input = Input(placeholder="短信验证码", id="login_captcha")

        self.loading = LoadingIndicator()
        self.loading.display = NONE

        self.button = self.ButtonTuple(
            login=ButtonDisplay("登录", variant="primary", id="login"),
            success=ButtonDisplay("完成", variant="success", id="login_success"),
            error=ButtonDisplay("返回", variant="error", id="login_error")
        )
        [i.hide() for i in self.button[1:]]

    def compose(self) -> ComposeResult:
        yield Static("验证码", classes="label")
        yield self.input
        yield Static()
        yield from self.button
        yield Static()
        yield self.loading

    def close_login(self):
        self.button.login.hide()
        self.button.login.disabled = False

    async def login(self):
        """
        登录的完整操作
        """
        if not self.before_login:
            return
        elif not PhoneForm.input.value:
            self.app.notice("登录信息缺少 [bold red]手机号[/] ！")
            return
        elif not self.input.value:
            self.app.notice("登录信息缺少 [bold red]验证码[/] ！")
            return
        elif not self.input.value.isdigit():
            self.app.notice("登录信息 [bold red]验证码[/] 需要是数字！")
            return
        self.before_login = False

        self.button.login.disabled = True
        self.loading.display = BLOCK

        # 1. 通过短信验证码获取 login_ticket
        phone_number = PhoneForm.input.value
        captcha = int(self.input.value)
        login_ticket_return = await get_login_ticket_by_captcha(phone_number, captcha, PhoneForm.cookies)
        login_status = login_ticket_return[0]
        cookies = login_ticket_return[1]
        if login_status:
            logger.info(f"用户 {phone_number} 成功获取 login_ticket: {cookies.login_ticket}")
            account = conf.accounts.get(cookies.bbs_uid)
            if not account or not account.cookies:
                conf.accounts.update({
                    cookies.bbs_uid: UserAccount(phone_number=phone_number, cookies=cookies)
                })
            else:
                conf.accounts[cookies.bbs_uid].cookies.update(cookies)
            conf.save()
            CaptchaLoginInformation.radio_tuple.login_ticket_by_captcha.turn_on()

            # 2. 通过 login_ticket 获取 stoken 和 ltoken
            multi_token_return = await get_multi_token_by_login_ticket(cookies)
            login_status = multi_token_return[0]
            cookies = multi_token_return[1]
            if login_status:
                logger.info(f"用户 {phone_number} 成功获取 stoken: {cookies.stoken} 和 ltoken: {cookies.ltoken}")
                conf.accounts[cookies.bbs_uid].cookies.update(cookies)
                conf.save()
                CaptchaLoginInformation.radio_tuple.multi_token_by_login_ticket.turn_on()

                # 3. 通过 stoken_v1 获取 stoken_v2
                get_stoken_v2_return = await get_stoken_v2_by_v1(conf.accounts[cookies.bbs_uid].cookies)
                get_stoken_v2_status = get_stoken_v2_return[0]
                cookies = get_stoken_v2_return[1]
                if get_stoken_v2_status:
                    logger.info(f"用户 {phone_number} 成功获取 stoken_v2: {cookies.stoken_v2}")
                    conf.accounts[cookies.bbs_uid].cookies.update(cookies)
                    conf.save()
                    CaptchaLoginInformation.radio_tuple.get_stoken_v2.turn_on()

                    # 4. 通过 stoken 获取 cookie_token
                    cookie_token_return = await get_cookie_token_by_stoken(cookies)
                    login_status = cookie_token_return[0]
                    cookies = cookie_token_return[1]
                    if login_status:
                        logger.info(f"用户 {phone_number} 成功获取 cookie_token: {cookies.cookie_token}")
                        conf.accounts[cookies.bbs_uid].cookies.update(cookies)
                        conf.save()
                        CaptchaLoginInformation.radio_tuple.cookie_token_by_stoken.turn_on()

                        # Plan: 此处如果可以模拟App的登录操作，再标记为登录完成，更安全
                        CaptchaLoginInformation.radio_tuple.login_finished.turn_on()
                        self.app.notice(f"用户 [bold green]{phone_number}[/] 登录成功！")
                        self.button.success.show()

        self.loading.display = NONE
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
            else:
                notice_text += "未知错误！"
            notice_text += "[/] 如果部分步骤成功，你仍然可以尝试获取收货地址、兑换等功能"
            self.button.error.show()
            logger.info(notice_text)
            self.app.notice(notice_text)

        self.close_login()
        return login_status

    async def on_input_submitted(self, _: Input.Submitted) -> None:
        await self.login()

    async def on_button_pressed(self, event: Button.Pressed) -> None:
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


class Welcome(Container):
    DEFAULT_CSS = """
    Welcome {
        background: $boost;
        height: auto;
        max-width: 100;
        min-width: 40;
        border: wide $primary;
        padding: 1 2;
        margin: 1 2;
        box-sizing: border-box;
    }

    Welcome Button {
        width: 100%;
        margin-top: 1;
    }
    """

    def compose(self) -> ComposeResult:
        yield Static(Markdown(WELCOME_MD))
        yield Button("开始使用", variant="success")

    def on_button_pressed(self) -> None:
        self.app.query_one(".location-first").scroll_visible(duration=0.5, top=True)


class Version(Static):
    DEFAULT_CSS = """
    Version {
        color: $text-disabled;
        dock: bottom;
        text-align: center;
        padding: 1;
    }
    """

    def render(self) -> RenderableType:
        return f"[b]v{version('textual')}"


class Sidebar(Container):
    DEFAULT_CSS = """
    Sidebar {
        width: 40;
        background: $panel;
        transition: offset 500ms in_out_cubic;
        layer: overlay;
    }

    Sidebar:focus-within {
        offset: 0 0 !important;
    }

    Sidebar.-hidden {
        offset-x: -100%;
    }

    Sidebar Title {
        background: $boost;
        color: $secondary;
        padding: 2 4;
        border-right: vkey $background;
        dock: top;
        text-align: center;
        text-style: bold;
    }
    """

    def compose(self) -> ComposeResult:
        yield Title("Mys_Goods_Tool")
        yield OptionGroup(Message("MESSAGE"), Version())
        yield DarkSwitch()


class LocationLink(Static):
    DEFAULT_CSS = """
    LocationLink {
        margin: 1 0 0 1;
        height: 1;
        padding: 1 2;
        background: $boost;
        color: $text;
        box-sizing: content-box;
        content-align: center middle;
    }

    LocationLink:hover {
        background: $accent;
        color: $text;
        text-style: bold;
    }

    .pad {
        margin: 1 0;
    }
    """

    def __init__(self, label: str, reveal: str) -> None:
        super().__init__(label)
        self.reveal = reveal

    def on_click(self) -> None:
        # 跳转到指定位置
        self.app.query_one(self.reveal).scroll_visible(top=True, duration=0.5)


class DarkSwitch(Horizontal):
    DEFAULT_CSS = """
    DarkSwitch {
        background: $panel;
        padding: 1;
        dock: bottom;
        height: auto;
        border-right: vkey $background;
    }

    DarkSwitch .label {
        width: 1fr;
        padding: 1 2;
        color: $text-muted;
    }

    DarkSwitch Switch {
        background: $boost;
        dock: left;
    }
    """

    def compose(self) -> ComposeResult:
        yield Switch(value=self.app.dark)
        yield Static("暗黑模式切换", classes="label")

    def on_mount(self) -> None:
        self.watch(self.app, "dark", self.on_dark_change, init=False)

    def on_dark_change(self) -> None:
        self.query_one(Switch).value = self.app.dark

    def on_switch_changed(self, event: Switch.Changed) -> None:
        self.app.dark = event.value


class Notification(Static):
    """
    通知消息框
    """
    DEFAULT_CSS = """
    Notification {
        dock: bottom;
        layer: notification;
        width: auto;
        margin: 2 4;
        padding: 1 2;
        background: $background;
        color: $text;
        height: auto;
    }
    """

    def on_mount(self) -> None:
        self.set_timer(3, self.remove)

    def on_click(self) -> None:
        self.remove()


class TuiApp(App[None]):
    TITLE = "Mys_Goods_Tool"
    """textual TUI 标题"""
    BINDINGS = [
        ("ctrl+b", "toggle_sidebar", "侧栏"),
        ("ctrl+t", "app.toggle_dark", "暗黑模式切换"),
        ("ctrl+s", "app.screenshot()", "截屏"),
        ("f1", "app.toggle_class('TextLog', '-hidden')", "日志"),
        Binding("ctrl+c,ctrl+q", "app.quit", "退出", show=True),
    ]
    """按键绑定"""

    show_sidebar = reactive(False)

    app: TuiApp
    """当前App实例"""

    text_log = TextLog(classes="-hidden", wrap=False, highlight=True, markup=True)
    """textual日志输出界面"""

    @classmethod
    def notice(cls, renderable: RenderableType) -> None:
        """
        发出消息通知

        :param renderable: 通知内容
        """
        cls.app.screen.mount(Notification(renderable))

    def add_note(self, renderable: RenderableType) -> None:
        """
        输出至日志（仅textual TUI内，而不是loguru的Logger）

        :param renderable: 日志内容
        """
        self.query_one(TextLog).write(renderable)

    def compose(self) -> ComposeResult:
        yield Container(
            Sidebar(classes="-hidden"),
            Header(show_clock=False),
            self.text_log,
            Body(
                QuickAccess(
                    LocationLink("主页", ".location-top"),
                    LocationLink("登录绑定", ".location-login"),
                    LocationLink("管理兑换计划", ".location-rich"),
                    LocationLink("进入兑换模式", ".location-css"),
                ),
                AboveFold(Welcome(), classes="location-top"),
                Column(
                    Section(
                        SectionTitle("米游社账号登录绑定"),
                        CaptchaLoginInformation(),
                        PhoneForm(),
                        CaptchaForm(),
                        DataTable(),
                    ),
                    classes="location-login location-first",
                ),
                Column(
                    Section(
                        SectionTitle("Rich"),
                        TextContent(Markdown(RICH_MD)),
                        SubTitle("Pretty Printed data (try resizing the terminal)"),
                        Static(Pretty(DATA, indent_guides=True), classes="pretty pad"),
                    ),
                    classes="location-rich",
                ),
            ),
        )
        yield Footer()

    def action_open_link(self, link: str) -> None:
        """
        跳转浏览器打开URL链接
        """
        self.app.bell()
        import webbrowser

        webbrowser.open(link)

    def action_toggle_sidebar(self) -> None:
        """
        切换侧栏
        """
        sidebar = self.query_one(Sidebar)
        self.set_focus(None)
        if sidebar.has_class("-hidden"):
            sidebar.remove_class("-hidden")
        else:
            if sidebar.query("*:focus"):
                self.screen.set_focus(None)
            sidebar.add_class("-hidden")

    def on_mount(self) -> None:
        TuiApp.app = self
        logger.add(TuiApp.text_log.write, diagnose=False, level="DEBUG", format=LOG_FORMAT)
        logger.info("Mys_Goods_Tool 开始运行")
        self.query_one("Welcome Button", Button).focus()

    def action_screenshot(self, filename: str | None = None, path: str = str(ROOT_PATH)) -> None:
        """Save an SVG "screenshot". This action will save an SVG file containing the current contents of the screen.

        Args:
            filename: Filename of screenshot, or None to auto-generate. Defaults to None.
            path: Path to directory. Defaults to "./".
        """
        self.bell()
        path = self.save_screenshot(filename, path)
        message = Text.assemble("截屏已保存至 ", (f"'{path}'", "bold green"))
        self.add_note(message)
        self.screen.mount(Notification(message))
