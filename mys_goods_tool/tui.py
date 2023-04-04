from __future__ import annotations

import asyncio
import queue
from typing import NamedTuple, Tuple, Optional

from importlib_metadata import version
from rich.console import RenderableType
from rich.markdown import Markdown
from rich.pretty import Pretty
from rich.text import Text
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical
from textual.dom import DOMNode
from textual.events import Event
from textual.reactive import reactive
from textual.screen import Screen
from textual.widgets import (
    Button,
    DataTable,
    Footer,
    Header,
    Input,
    Static,
    Switch,
    TextLog, LoadingIndicator, Tree, RadioButton
)

from api import create_mobile_captcha, create_mmt
from data_model import GeetestResult, MmtData
from geetest import GeetestProcessManager, SetAddressProcessManager
from utils import LOG_FORMAT, logger

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

CSS_MD = """

Textual uses Cascading Stylesheets (CSS) to create Rich interactive User Interfaces.

- **Easy to learn** - much simpler than browser CSS
- **Live editing** - see your changes without restarting the app!

Here's an example of some CSS used in this app:

"""

EXAMPLE_CSS = """\
Screen {
    layers: base overlay notes;
    overflow: hidden;
}

Sidebar {
    width: 40;
    background: $panel;
    transition: offset 500ms in_out_cubic;
    layer: overlay;

}

Sidebar.-hidden {
    offset-x: -100%;
}"""

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

NONE = "none"
"""显示（CSS display 属性 - none）"""
BLOCK = "block"
"""隐藏（CSS display 属性 - block）"""

DOMNode.DEFAULT_CSS += """
    * {
        transition: background 500ms in_out_cubic, color 500ms in_out_cubic;
    }
    """
Screen.DEFAULT_CSS += """
    Screen {
        layers: base overlay notes notifications;
        overflow: hidden;
    }
    
    Screen>Container {
        height: 100%;
        overflow: hidden;
    }
    """
TextLog.DEFAULT_CSS += """
    TextLog {
        background: $surface;
        color: $text;
        height: 50vh;
        dock: bottom;
        layer: notes;
        border-top: hkey $primary;
        offset-y: 0;
        transition: offset 400ms in_out_cubic;
        padding: 0 1 1 1;
    }

    TextLog:focus {
        offset: 0 0 !important;
    }

    TextLog.-hidden {
        offset-y: 100%;
    }
    """
DataTable.DEFAULT_CSS += """
    DataTable {
        height: 16;
    }
    """
Tree.DEFAULT_CSS += """
    Tree {
        margin: 1 0;
    }
    """
Vertical.DEFAULT_CSS += """
    Vertical {
        height: auto;
        layout: vertical;
    }
    """
Horizontal.DEFAULT_CSS += """
    Horizontal {
        height: auto;
        layout: horizontal;
    }
    """


class Body(Container):
    DEFAULT_CSS = """
    Body {
        height: 100%;
        overflow-y: scroll;
        width: 100%;
        background: $surface;
    }
    """


class Title(Static):
    DEFAULT_CSS = """
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


class OptionGroup(Container):
    DEFAULT_CSS = """
    OptionGroup {
        background: $boost;
        color: $text;
        height: 1fr;
        border-right: vkey $background;
    }
    """


class SectionTitle(Static):
    DEFAULT_CSS = """
    SectionTitle {
        padding: 1 2;
        background: $boost;
        text-align: center;
        text-style: bold;
    }
    """


class Message(Static):
    DEFAULT_CSS = """
    Message {
        margin: 0 1;
    }
    """


class AboveFold(Container):
    DEFAULT_CSS = """
    AboveFold {
        width: 100%;
        height: 100%;
        align: center middle;
    }
    """


class Section(Container):
    DEFAULT_CSS = """
    Section {
        height: auto;
        min-width: 40;
        margin: 1 2 4 2;
    }
    """


class Column(Container):
    DEFAULT_CSS = """
    Column {
        height: auto;
        min-height: 100vh;
        align: center top;
        overflow: hidden;
    }
    """


class TextContent(Static):
    DEFAULT_CSS = """
    TextContent {
        margin: 1 0;
    }
    """


class QuickAccess(Container):
    DEFAULT_CSS = """
        QuickAccess {
        width: 30;
        dock: left;
    }
    """


class Window(Container):
    DEFAULT_CSS = """
    Window {
        background: $boost;
        overflow: auto;
        height: auto;
        max-height: 16;
    }
    
    Window>Static {
        width: auto;
    }
    """


class SubTitle(Static):
    DEFAULT_CSS = """
        SubTitle {
        padding-top: 1;
        border-bottom: heavy $panel;
        color: $text;
        text-style: bold;
    }
    """


class LoginForm(Container):
    """
    登录表单
    """
    DEFAULT_CSS = """
    LoginForm {
        height: auto;
        padding: 1 2;
        layout: grid;
        grid-size: 2;
        grid-rows: 4;
        grid-columns: 12 1fr;
        background: $boost;
        border: wide $background;
    }

    LoginForm ButtonDisplay {
        margin: 0 1;
        width: 100%;
    }

    LoginForm .label {
        padding: 1 2;
        text-align: right;
    }
    """


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


class LoginInformation(Container):
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
        
        Tips>StaticStatus {
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

    DEFAULT_CSS = """
    LoginInformation {
        height: auto;
        margin: 1 0;
        overflow: hidden;
    }
    
    LoginInformation Horizontal {
        align: center middle;
    }
    """
    RadioTuple = NamedTuple("RadioTuple",
                            create_geetest=RadioStatus,
                            http_server=RadioStatus,
                            finish_geetest=RadioStatus,
                            create_captcha=RadioStatus,
                            login=RadioStatus
                            )

    StaticTuple = NamedTuple("StaticTuple",
                             save_title=Static,
                             save_text=StaticStatus,
                             geetest_title=Static,
                             geetest_text=StaticStatus
                             )

    radio_tuple = RadioTuple(
        create_geetest=RadioStatus("短信验证码 - 申请人机验证任务"),
        http_server=RadioStatus("开启人机验证网页服务器"),
        finish_geetest=RadioStatus("完成人机验证"),
        create_captcha=RadioStatus("发出短信验证码"),
        login=RadioStatus("完成登录")
    )

    SAVE_TEXT = "..."
    GEETEST_TEXT = "- 暂无需要完成的人机验证任务 -"

    static_tuple = StaticTuple(
        save_title=Static(Markdown("## 下一个账号将保存至")),
        save_text=StaticStatus(SAVE_TEXT),
        geetest_title=Static(Markdown("## GEETEST人机验证链接")),
        geetest_text=StaticStatus(GEETEST_TEXT)
    )

    radio_set = StepSet(*radio_tuple)
    static_set = Tips(*static_tuple)

    def compose(self) -> ComposeResult:
        yield Horizontal(self.radio_set, self.static_set)

    async def on_event(self, event: Event) -> None:
        """
        重写事件处理，在收到请求修改LoginInformation内的各种组件属性的事件时，完成修改
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
        self.app.add_note("[b magenta]Start!")
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
        self.app.query_one(self.reveal).scroll_visible(top=True, duration=0.5)
        self.app.add_note(f"Scrolling to [b]{self.reveal}[/b]")


class CaptchaForm(LoginForm):
    input = Input(placeholder="手机号", id="phone")
    """手机号输入框"""

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
        self.listen_result_task: Optional[asyncio.Task] = None
        """等待GEETEST验证结果的异步任务"""
        self.loop = asyncio.get_event_loop()
        """事件循环"""

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
                LoginInformation.radio_tuple.finish_geetest.turn_on()
                self.loading.display = BLOCK
                if await create_mobile_captcha(int(self.input.value), self.mmt_data, geetest_result):
                    self.loading.display = NONE
                    logger.info(f"短信验证码已发送至 {self.input.value}")
                    LoginInformation.radio_tuple.create_captcha.turn_on()
                    self.geetest_manager.pipe[1].send(True)
                    await self.geetest_manager.force_stop_later(10)
                    self.button.success.show()
                    self.button.stop_geetest.hide()
                    break
                self.loading.display = NONE

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
        LoginInformation.radio_tuple.http_server.turn_on()
        link = f"http://{address[0]}:{address[1]}/index.html?gt={self.mmt_data.gt}&challenge={self.mmt_data.challenge}"
        LoginInformation.static_tuple.geetest_text.change_text(
            renderable=f"\n- 请前往链接进行验证：\n"
                       f"[@click=pass]{link}[/]",
            text_align="left")
        self.listen_result_task = self.loop.create_task(self.listen_result())

    def set_address_error_callback(self, exception: BaseException):
        logger.error("尝试异步获取可用HTTP监听地址失败")
        logger.debug(exception)
        self.close_create_captcha_send()
        self.button.error.show()
        return

    async def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "create_captcha_send":
            if not self.input.value:
                TuiApp.notice("登录信息缺少 [bold red]手机号[/] ！")
                return
            elif not self.input.value.isdigit():
                TuiApp.notice("登录信息 [bold red]手机号[/] 格式错误！")
                return
            self.button.send.disabled = True
            self.loading.display = BLOCK

            create_mmt_result = await create_mmt()
            if not create_mmt_result[0]:
                self.close_create_captcha_send()
                self.button.error.show()
                return
            else:
                logger.info(f"已成功获取Geetest行为验证任务数据 {create_mmt_result[1]}")
                LoginInformation.radio_tuple.create_geetest.turn_on()
                self.mmt_data = create_mmt_result[1]
                self.set_address_manager.start()

        elif event.button.id == "create_captcha_stop_geetest":
            LoginInformation.static_tuple.geetest_text.change_text(LoginInformation.GEETEST_TEXT, "center")
            LoginInformation.radio_tuple.create_geetest.turn_off()
            LoginInformation.radio_tuple.http_server.turn_off()
            LoginInformation.radio_tuple.finish_geetest.turn_off()
            LoginInformation.radio_tuple.create_captcha.turn_off()
            self.geetest_manager.pipe[1].send(True)
            self.button.stop_geetest.hide()
            self.button.send.show()
            await self.geetest_manager.force_stop_later(10)

        elif event.button.id in ["create_captcha_success", "create_captcha_error"]:
            self.button.success.hide()
            self.button.error.hide()
            self.button.send.show()


class GetCookieForm(LoginForm):
    ButtonTuple = NamedTuple("ButtonTuple", login_1=ButtonDisplay, login_2=ButtonDisplay, login_3=ButtonDisplay,
                             error=ButtonDisplay)

    def __init__(self):
        super().__init__()

        self.input = Input(placeholder="短信验证码", id="captcha")

        self.loading = LoadingIndicator()
        self.loading.display = NONE

        self.button = self.ButtonTuple(
            login_1=ButtonDisplay("第一次登录 - 获取 A", variant="primary", id="login_1"),
            login_2=ButtonDisplay("第二次登录 - 获取 B", variant="primary", id="login_2"),
            login_3=ButtonDisplay("登录绑定下一个账号", variant="success", id="login_3"),
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

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "login_1":
            logger.info(f"phone: {CaptchaForm.input.value}, captcha: {self.input.value}")
            self.loading.display = BLOCK
            self.button.login_1.display = NONE
            self.button.login_2.display = BLOCK
            self.button.login_2.disabled = True
            await asyncio.sleep(1)
            self.loading.display = NONE
            await asyncio.sleep(2)
            self.input.value = ""
            self.button.login_2.disabled = False

        elif event.button.id == "login_2":
            logger.info(f"phone: {CaptchaForm.input.value}, captcha: {self.input.value}")
            self.loading.display = BLOCK
            self.button.login_2.display = NONE
            self.button.login_3.display = BLOCK
            self.button.login_3.disabled = True
            await asyncio.sleep(1)
            self.loading.display = NONE
            await asyncio.sleep(2)
            self.button.login_3.disabled = False

        elif event.button.id == "login_3":
            logger.info(f"phone: {CaptchaForm.input.value}, captcha: {self.input.value}")
            self.input.value = ""
            self.input_phone.value = ""
            self.loading.display = NONE
            self.button.login_3.display = NONE
            self.button.login_1.display = BLOCK


class Notification(Static):
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
    BINDINGS = [
        ("ctrl+b", "toggle_sidebar", "侧栏"),
        ("ctrl+t", "app.toggle_dark", "暗黑模式切换"),
        ("ctrl+s", "app.screenshot()", "截屏"),
        ("f1", "app.toggle_class('TextLog', '-hidden')", "日志"),
        Binding("ctrl+c,ctrl+q", "app.quit", "退出", show=True),
    ]

    show_sidebar = reactive(False)

    app: TuiApp

    @classmethod
    def notice(cls, renderable: RenderableType) -> None:
        """
        发出消息通知

        :param renderable: 通知内容
        """
        cls.app.screen.mount(Notification(renderable))

    def add_note(self, renderable: RenderableType) -> None:
        self.query_one(TextLog).write(renderable)

    def compose(self) -> ComposeResult:
        yield Container(
            Sidebar(classes="-hidden"),
            Header(show_clock=False),
            TextLog(classes="-hidden", wrap=False, highlight=True, markup=True),
            Body(
                QuickAccess(
                    LocationLink("主页", ".location-top"),
                    LocationLink("登录绑定", ".location-widgets"),
                    LocationLink("管理兑换计划", ".location-rich"),
                    LocationLink("进入兑换模式", ".location-css"),
                ),
                AboveFold(Welcome(), classes="location-top"),
                Column(
                    Section(
                        SectionTitle("米游社账号登录绑定"),
                        LoginInformation(),
                        CaptchaForm(),
                        GetCookieForm(),
                        DataTable(),
                    ),
                    classes="location-widgets location-first",
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
        self.app.bell()
        import webbrowser

        webbrowser.open(link)

    def action_toggle_sidebar(self) -> None:
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
        logger.add(self.query_one(TextLog).write, diagnose=False, level="DEBUG", format=LOG_FORMAT)
        logger.info("Mys_Goods_Tool 开始运行")
        self.query_one("Welcome Button", Button).focus()

    def action_screenshot(self, filename: str | None = None, path: str = "./") -> None:
        """Save an SVG "screenshot". This action will save an SVG file containing the current contents of the screen.

        Args:
            filename: Filename of screenshot, or None to auto-generate. Defaults to None.
            path: Path to directory. Defaults to "./".
        """
        self.bell()
        path = self.save_screenshot(filename, path)
        message = Text.assemble("截屏保存至 ", (f"'{path}'", "bold green"))
        self.add_note(message)
        self.screen.mount(Notification(message))
