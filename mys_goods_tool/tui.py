from __future__ import annotations

import sys
from io import StringIO

from rich.console import RenderableType
from rich.markdown import Markdown
from rich.text import Text
from textual import events
from textual.app import App, ComposeResult, DEFAULT_COLORS
from textual.binding import Binding
from textual.color import Color
from textual.events import Event
from textual.reactive import reactive
from textual.widgets import (
    Button,
    Footer,
    Header,
    Switch
)

from mys_goods_tool.custom_css import *
from mys_goods_tool.custom_widget import RadioStatus, StaticStatus
from mys_goods_tool.exchange_mode import ExchangeModeView, EnterExchangeMode, ExitExchangeMode
from mys_goods_tool.exchange_plan_view import ExchangePlanView
from mys_goods_tool.login_view import LoginView
from mys_goods_tool.user_data import ROOT_PATH, VERSION, different_device_and_salt
from mys_goods_tool.utils import LOG_FORMAT, logger

WELCOME_MD = """
# Mys_Goods_Tool - 米游社商品兑换工具

## 更新说明

- 兑换请求Headers增加与修改了 `Referer`, `x-rpc-device_fp`, `x-rpc-verify_key`, `Origin` 等字段，可能修复兑换失败的问题
- 修复登陆时因为连接断开（client has been closed）而导致登陆失败的问题
- 防止因配置文件中默认存在 `device_config`, `salt_config` 而导致更新后默认配置被原配置覆盖的问题
- 若需要修改 `device_config` 配置，修改后还设置用户数据文件中 `preference.override_device_and_salt` 为 `true` 以覆盖默认值
- 修复Unix下即使安装了 uvloop 也找不到，无法应用的问题

## 功能和特性

- 使用 [Textual](https://github.com/Textualize/textual) 终端图形界面库，支持 Windows / Linux / macOS 甚至可能是移动端SSH客户端
- 短信验证码登录（只需接收一次验证码）
- 内置人机验证页面，无需前往官网验证
- 多账号支持
- 支持米游社所有分区的商品兑换

## 其他
- [**🔗完整说明文档**](https://github.com/Ljzd-PRO/Mys_Goods_Tool/wiki)
- 仅供学习时参考

- 相似项目推荐:  \
  **mysTool - 米游社辅助工具插件**  \
  简介：NoneBot2 插件 | 米游社工具-每日米游币任务、游戏签到、商品兑换、免抓包登录、原神树脂提醒  \
  🔗 https://github.com/Ljzd-PRO/nonebot-plugin-mystool
  
- 本项目已开启[🔗Github Actions](https://github.com/Ljzd-PRO/Mys_Goods_Tool/actions)。
  欢迎[🔗指出Bug](https://github.com/Ljzd-PRO/Mys_Goods_Tool/issues)
  和[🔗贡献代码](https://github.com/Ljzd-PRO/Mys_Goods_Tool/pulls)👏

- 开发版分支：[🔗dev](https://github.com/Ljzd-PRO/Mys_Goods_Tool/tree/dev/)
"""


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

    def _on_button_pressed(self) -> None:
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
        return f"[b]v{VERSION}"


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
        with Container():
            yield Message("米游社商品兑换工具")
            yield Message()
            yield Message(
                "[bold italic black][link=https://github.com/Ljzd-PRO/Mys_Goods_Tool]🔗 GitHub 项目链接[/link][/]")
            yield Message()
            yield Message(
                "[bold italic black][link=https://github.com/Ljzd-PRO/nonebot-plugin-mystool]🔗 mysTool - 米游社辅助工具 NoneBot机器人插件[/link][/]")
            yield Version()
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

    def _on_click(self, _: events.Click) -> None:
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

    # TODO: 目前似乎切换后会导致UI界面卡顿，待优化

    def compose(self) -> ComposeResult:
        yield Switch(value=self.app.dark)
        yield Static("深色模式切换", classes="label")

    def _on_mount(self, _: events.Mount) -> None:
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
        border: wide $primary;
    }
    """

    def _on_mount(self, _: events.Mount) -> None:
        self.set_timer(3, self.remove)

    def on_click(self) -> None:
        self.remove()


# 主题颜色
# https://colorhunt.co/palette/b9eddd87cbb9569daa577d86
# TODO: 希望可以找到更好的日间模式(Light Mode)配色方案
DEFAULT_COLORS["dark"].primary = Color.parse("#569DAA")
DEFAULT_COLORS["dark"].secondary = Color.parse("#577D86")
DEFAULT_COLORS["dark"].accent = DEFAULT_COLORS["dark"].primary


# DEFAULT_COLORS["light"].primary = Color.parse("#B9EDDD")
# DEFAULT_COLORS["light"].secondary = Color.parse("#87CBB9")
# DEFAULT_COLORS["light"].accent = DEFAULT_COLORS["dark"].primary


class TuiApp(App):
    TITLE = "Mys_Goods_Tool"
    """textual TUI 标题"""
    BINDINGS = [
        ("ctrl+b", "toggle_sidebar", "🧭侧栏"),
        ("ctrl+t", "app.toggle_dark", "🌓深色模式切换"),
        ("ctrl+s", "app.screenshot()", "✂截屏"),
        ("f1", "app.toggle_class('TextLog', '-hidden')", "📃日志"),
        Binding("ctrl+c,ctrl+q", "app.quit", "🚪退出", show=True),
    ]
    """按键绑定"""

    show_sidebar = reactive(False)

    app: TuiApp
    """当前App实例"""

    text_log_writer: TextLogWriter
    """textual日志输出流"""
    text_log = TextLog(classes="-hidden", wrap=False, highlight=True, markup=True)
    """textual日志输出界面"""

    quick_access = QuickAccess(
        LocationLink("🏠 主页", ".location-top"),
        LocationLink("🔑 登录绑定", ".location-login"),
        LocationLink("📅 管理兑换计划", ".location-add_plan"),
        LocationLink("⏰ 进入兑换模式", ".location-exchange_mode"),
    )
    """快速访问菜单"""
    disable_required_column = (
        AboveFold(Welcome(), classes="location-top"),
        Column(
            Section(
                SectionTitle("米游社账号登录绑定"),
                LoginView(),
            ),
            classes="location-login location-first",
        ),
        Column(
            Section(
                SectionTitle("管理米游币商品兑换计划"),
                ExchangePlanView(),
            ),
            classes="location-add_plan",
        )
    )
    """进入兑换模式后需要禁用的Column"""
    body = Body(
        quick_access,
        *disable_required_column,
        Column(
            Section(
                SectionTitle("定时兑换模式"),
                ExchangeModeView(),
            ),
            classes="location-exchange_mode",
        )
    )
    """主体内容"""

    def notice(self, renderable: RenderableType) -> None:
        """
        发出消息通知

        :param renderable: 通知内容
        """
        self.app.screen.mount(Notification(renderable))

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
            self.body
        )
        yield Footer()

    async def on_event(self, event: Event) -> None:
        """
        重写事件处理，在收到请求修改Widget属性的事件时，完成修改
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

        elif isinstance(event, EnterExchangeMode):
            self.quick_access.disabled = True
            for column in self.disable_required_column:
                column.disabled = True
                column.display = NONE
            self.app.query_one(".location-exchange_mode").scroll_visible(top=True, duration=0.5, force=True)

        elif isinstance(event, ExitExchangeMode):
            self.quick_access.disabled = False
            for column in self.disable_required_column:
                column.disabled = False
                column.display = BLOCK
            self.app.query_one(".location-exchange_mode").scroll_visible(top=True, animate=False)

        await super().on_event(event)

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

    class TextLogWriter(StringIO):
        def write(self, text: str) -> None:
            super().write(text)
            TuiApp.text_log.write(text)

    def _on_mount(self, _: events.Mount) -> None:
        TuiApp.app = self
        TuiApp.text_log_writer = TuiApp.TextLogWriter()
        logger.add(self.text_log_writer, diagnose=False, level="DEBUG", format=LOG_FORMAT)
        if sys.platform not in ('win32', 'cygwin', 'cli'):
            try:
                import uvloop
            except ModuleNotFoundError:
                logger.info("在非 Windows 环境下，你可以安装 uvloop 以提高性能")
            else:
                import asyncio
                asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
        self.query_one("Welcome Button", Button).focus()
        if different_device_and_salt:
            logger.warning("检测到设备信息配置 device_config 或 salt_config 使用了非默认值，"
                           "如果你修改过这些配置，需要设置 preference.override_device_and_salt 为 True 以覆盖默认值并生效。"
                           "如果继续，将可能保存默认值到配置文件。")

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
