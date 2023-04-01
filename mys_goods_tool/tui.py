from __future__ import annotations

import asyncio
import traceback
from typing import NamedTuple, Tuple

from importlib_metadata import version
from rich.console import RenderableType
from rich.markdown import Markdown
from rich.pretty import Pretty
from rich.text import Text
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal
from textual.dom import DOMNode
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
    TextLog, LoadingIndicator, Tree
)

from api import create_mobile_captcha, create_mmt
from data_model import GeetestResult, MmtData, CreateMobileCaptchaStatus
from geetest import GeetestHandler, GeetestProcessManager, SetAddressProcessManager
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

WIDGETS_MD = """

通过短信验证登录绑定米游社账号

Build your own or use the builtin widgets.

- **Account** Text / Password input.
- **PassWD** Clickable button with a number of styles.

"""

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
    DEFAULT_CSS = """
    LoginForm {
        height: auto;
        margin: 1 0;
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
        yield OptionGroup(Message(MESSAGE), Version())
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
    geetest_result: GeetestResult
    """人机验证结果数据"""
    mmt_data: MmtData
    """GEETEST行为验证任务数据"""
    create_captcha_status: CreateMobileCaptchaStatus
    """接收人机验证的返回情况"""
    geetest_server_manager: GeetestProcessManager
    """包含进程池的GEETEST验证HTTP服务器线程管理器"""
    set_address_manager: SetAddressProcessManager
    """包含进程池的可用监听地址获取线程管理器"""
    input = Input(placeholder="手机号", id="phone")
    """手机号输入框"""

    ButtonTuple = NamedTuple("ButtonTuple", send=ButtonDisplay, stop_geetest=ButtonDisplay, success=ButtonDisplay,
                             error=ButtonDisplay)

    def __init__(self):
        super().__init__()

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
        self.loading.display = NONE
        self.button.send.hide()
        self.button.send.disabled = False

    def httpd_callback(self):
        if self.create_captcha_status:
            self.button.success.display = BLOCK
        else:
            self.button.error.display = BLOCK

    def httpd_error_callback(self, _: BaseException):
        logger.error("HTTP服务器 - 启动失败")
        logger.debug(traceback.format_exc())
        self.button.stop_geetest.hide()
        self.button.error.show()

    @classmethod
    def get_result(cls, _: GeetestHandler, result: GeetestResult):
        CaptchaForm.geetest_result = result
        coroutine = create_mobile_captcha(int(cls.input.value), CaptchaForm.mmt_data, result)
        loop = asyncio.get_event_loop()
        CaptchaForm.create_captcha_status = loop.run_until_complete(coroutine)
        if CaptchaForm.create_captcha_status:
            cls.geetest_server_manager.pool.terminate()

    def set_address_callback(self, address: Tuple[str, int]):
        if not address:
            self.close_create_captcha_send()
            self.button.error.show()
            return
        self.geetest_server_manager = GeetestProcessManager(address, self.get_result, self.httpd_callback,
                                                            self.httpd_error_callback)
        self.geetest_server_manager.start()
        self.close_create_captcha_send()
        self.button.stop_geetest.show()

    def set_address_error_callback(self):
        logger.error("尝试异步获取可用HTTP监听地址失败")
        logger.debug(traceback.format_exc())
        self.close_create_captcha_send()
        self.button.error.show()
        return

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "create_captcha_send":
            self.button.send.disabled = True
            self.loading.display = BLOCK

            create_mmt_result = await create_mmt()
            if not create_mmt_result[0]:
                self.close_create_captcha_send()
                self.button.error.show()
                return

            self.set_address_manager = SetAddressProcessManager(self.set_address_callback,
                                                                self.set_address_error_callback)
            self.set_address_manager.start()

        elif event.button.id == "create_captcha_stop_geetest":
            self.geetest_server_manager.pool.terminate()
            self.button.stop_geetest.hide()
            self.button.send.show()

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
                        TextContent(Markdown(WIDGETS_MD)),
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
        logger.add(self.query_one(TextLog).write, diagnose=False, level="DEBUG", format=LOG_FORMAT)
        self.add_note("Mys_Goods_Tool 开始运行")
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
