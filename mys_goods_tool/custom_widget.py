from __future__ import annotations

from itertools import zip_longest
from typing import Optional, Tuple

from rich.console import RenderableType
from rich.text import TextType
from textual import events
from textual.app import ComposeResult
from textual.events import Event
from textual.widgets import (
    Button,
    LoadingIndicator, RadioButton, TabbedContent, TabPane, ContentSwitcher, Tabs, ListItem
)
from textual.widgets._button import ButtonVariant
from textual.widgets._tabbed_content import ContentTab

from mys_goods_tool.custom_css import *
from mys_goods_tool.user_data import ExchangePlan


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
        """
        修改renderable属性
        主要是为了修改text_align属性，如果只是修改文本内容，直接使用update方法即可

        :param renderable: 新的 renderable 文本内容
        :param text_align: 新的 text_align 属性
        """
        self.post_message(StaticStatus.ChangeRenderable(self, renderable, text_align))


class ControllableButton(Button):
    """
    带隐藏、显示、禁用、启用控制方法的按钮
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

    def disable(self):
        """
        禁用
        """
        button = self
        button.disabled = True

    def enable(self):
        """
        启用
        """
        button = self
        button.disabled = False


class LoadingDisplay(LoadingIndicator):
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


class DynamicTabbedContent(TabbedContent):
    """
    可动态增加TabPane的TabbedContent
    """

    def __init__(self, *titles: TextType, initial: str = "") -> None:
        super().__init__(*titles, initial=initial)
        self._tabs: Optional[Tabs] = None
        self._content_switcher = ContentSwitcher(initial=self._initial or None)

    @classmethod
    def _set_id(cls, content: TabPane, new_id: str) -> TabPane:
        """Set an id on the content, if not already present.

        Args:
            content: a TabPane.
            new_id: New `is` attribute, if it is not already set.

        Returns:
            The same TabPane.
        """
        if content.id is None:
            content.id = new_id
        return content

    def compose(self) -> ComposeResult:
        """Compose the tabbed content."""

        # Wrap content in a `TabPane` if required.
        pane_content = [
            (
                self._set_id(content, f"tab-{index}")
                if isinstance(content, TabPane)
                else TabPane(
                    title or self.render_str(f"Tab {index}"), content, id=f"tab-{index}"
                )
            )
            for index, (title, content) in enumerate(
                zip_longest(self.titles, self._tab_content), 1
            )
        ]
        # Get a tab for each pane
        tabs = [
            ContentTab(content._title, content.id or "") for content in pane_content
        ]
        # Yield the tabs
        self._tabs = Tabs(*tabs, active=self._initial or None)
        yield self._tabs
        # Yield the content switcher and panes
        with self._content_switcher:
            yield from pane_content

    async def append(self, content: TabPane):
        """Add a new TabPane to the end of the tab list.

        Args:
            content: The new TabPane object to add.
        """
        self.titles.append(content._title)
        self._tab_content.append(content)
        tab_pane_with_id = self._set_id(content, f"tab-{len(self._content_switcher.children) + 1}")
        content_tab = ContentTab(tab_pane_with_id._title, tab_pane_with_id.id or "")
        await self._content_switcher.mount(tab_pane_with_id)
        # Incase _initial is not set (empty TabbedContent), set it to the active tab
        self._content_switcher._initial = self.active
        initial = self._content_switcher._initial
        with self._content_switcher.app.batch_update():
            for child in self._content_switcher.children:
                child.display = bool(initial) and child.id == initial
        self._tabs.add_tab(content_tab)


class GameButton(ControllableButton):
    """
    商品分区视图下的商品选择按钮
    """

    def __init__(
            self,
            label: TextType | None = None,
            variant: ButtonVariant = "default",
            *,
            name: str | None = None,
            id: str | None = None,
            classes: str | None = None,
            disabled: bool = False,
            partition: Tuple[str, str]
    ):
        super().__init__(label, variant, name=name, id=id, classes=classes, disabled=disabled)
        self.partition = partition

    class Pressed(Button.Pressed):
        def __init__(self, button: GameButton):
            super().__init__(button)
            self.button = button


class PlanButton(ControllableButton):
    """
    编辑兑换计划视图下的按钮
    """

    def __init__(
            self,
            label: TextType | None = None,
            variant: ButtonVariant = "default",
            *,
            name: str | None = None,
            id: str | None = None,
            classes: str | None = None,
            disabled: bool = False,
            plan: ExchangePlan
    ):
        super().__init__(label, variant, name=name, id=id, classes=classes, disabled=disabled)
        self.plan = plan

    class Pressed(Button.Pressed):
        def __init__(self, button: PlanButton):
            super().__init__(button)
            self.button = button


class UnClickableItem(ListItem):
    """
    无法点击、不会高亮的列表项
    """

    async def _on_click(self, _: events.Click) -> None:
        pass

    def watch_highlighted(self, value: bool) -> None:
        pass
