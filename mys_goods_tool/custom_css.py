from __future__ import annotations

from textual.containers import Container, Horizontal, Vertical
from textual.dom import DOMNode
from textual.screen import Screen
from textual.widgets import (
    DataTable,
    Static,
    TextLog, Tree
)

NONE = "none"
"""隐藏（CSS display 属性 - none）"""
BLOCK = "block"
"""显示（CSS display 属性 - block）"""

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
        height: auto;
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

    LoginForm ControllableButton {
        margin: 0 1;
        width: 100%;
    }

    LoginForm .label {
        padding: 1 2;
        text-align: right;
    }
    """


class ExchangePlanContent(Container):
    """
    兑换计划的添加步骤视图
    """
    DEFAULT_CSS = """
    ExchangePlanContent {
        height: auto;
        width: 1fr;
        border: round #666;
        padding: 2;
    }

    ExchangePlanContent OptionList {
        height: auto;
        width: 1fr;
        padding: 1;
        border: round $primary;
    }
    
    ExchangePlanContent OptionList Option {
        margin: 1;
    }
    
    ExchangePlanContent ListView {
        height: auto;
        width: 1fr;
        padding: 1;
        border: round $primary;
    }
    
    ExchangePlanContent StaticStatus {
        margin: 0 0 1 0;
    }
    
    ExchangePlanContent Horizontal Button {
        margin: 0 1 0 0;
    }
    
    ExchangePlanContent Horizontal LoadingIndicator {
        width: auto;
        min-width: 16;
        height: 3;
    }
    """


class CaptchaTips(Container):
    """
    登陆信息面板文本视图
    """
    DEFAULT_CSS = """
    CaptchaTips {
        height: 100%;
        width: 1fr;
        align: right middle;
        padding: 1;
        overflow: auto;
        border: round #666;
    }

    App.-light-mode Tips {
        border: round #CCC;
    }

    CaptchaTips StaticStatus {
        width: 100%;
        align: center top;
        text-align: center;
    }
    """


class CaptchaStepSet(Container):
    """
    登陆进度节点集合视图
    """
    DEFAULT_CSS = """
    CaptchaStepSet {
        height: auto;
        width: 1fr;
        align: left middle;
        overflow: auto;
        border: round #666;
    }

    App.-light-mode StepSet {
        border: round #CCC;
    }

    CaptchaStepSet RadioStatus {
        margin: 1 1;
    }
    """
