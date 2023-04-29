from __future__ import annotations

import asyncio
import time
from abc import abstractmethod
from typing import Tuple, Optional, Set, List, Dict, Any, Callable

from rich.console import RenderableType
from rich.markdown import Markdown
from textual import events
from textual.app import ComposeResult
from textual.widgets import (
    TabbedContent, TabPane, OptionList
)
from textual.widgets._option_list import Option

from mys_goods_tool.api import get_good_list, get_game_list, get_address
from mys_goods_tool.custom_css import *
from mys_goods_tool.custom_widget import StaticStatus, ControllableButton, LoadingDisplay, \
    DynamicTabbedContent, GameButton
from mys_goods_tool.data_model import Good, GameInfo, Address
from mys_goods_tool.user_data import config as conf, UserAccount


class ExchangePlanView(Container):
    """
    添加兑换计划 - 界面
    """
    loop: asyncio.AbstractEventLoop
    loop_tasks: Set[asyncio.Task] = set()

    def compose(self) -> ComposeResult:
        with TabbedContent():
            with TabPane("➕添加计划", id="tab-adding"):
                with TabbedContent():
                    with TabPane("1.选择账号", id="tab-adding-account"):
                        yield AccountWidget()
                    with TabPane("2.选择目标商品", id="tab-adding-goods"):
                        yield GoodsWidget()
                    with TabPane("3.选择收货地址", id="tab-adding-address"):
                        yield AddressWidget()
                    with TabPane("4.完成添加", id="tab-adding-ending"):
                        yield AccountWidget()

            with TabPane("✏️管理计划", id="tab-managing"):
                yield Container()

    def _on_compose(self) -> None:
        ExchangePlanView.loop = asyncio.get_event_loop()


class BasePlanAdding(PlanAddingWidget):
    DEFAULT_TEXT: RenderableType
    """默认提示文本内容"""
    text_view: StaticStatus
    """实时文本提示"""

    button_select: ControllableButton
    """保存选定内容"""
    button_refresh: ControllableButton
    """刷新列表"""
    button_reset: ControllableButton
    """重置选择"""
    selected: Optional[Any] = None
    """已选内容"""

    empty_data_option: Option
    """可选列表为空时显示的视图"""

    @abstractmethod
    def reset_selected(self):
        """
        重置已选内容
        一般包含以下操作：
            - 清空已选内容
            - 禁用重置按钮
            - 启用选择按钮
            - 重置文本内容
        """
        pass

    @abstractmethod
    def _on_button_pressed(self, event: ControllableButton.Pressed) -> None:
        """
        按下按钮时触发的事件
        一般包含：
            - 选择按钮：保存选定内容
                - 禁用选择按钮
                - 禁用选项列表
                - 启用重置按钮
                - 更新文本内容
            - 刷新按钮：刷新列表
                - 更新选项列表
                - 检查新的列表是否为空
                - 重置已选内容
            - 重置按钮：重置已选内容
                - 重置已选内容
                - 重置文本内容
                - 禁用重置按钮
                - 启用选择按钮
                - 启用选项列表
        """
        pass


class AccountWidget(BasePlanAdding):
    """
    选择账号 - 界面
    """
    DEFAULT_TEXT = Markdown("- 请选择一个账户")
    text_view = StaticStatus(DEFAULT_TEXT)

    button_select = ControllableButton("💾 保存", id="button-account-select", disabled=True)
    button_refresh = ControllableButton("🔄 刷新", variant="primary", id="button-account-refresh")
    button_reset = ControllableButton("↩ 重置", variant="warning", id="button-account-reset", disabled=True)

    account_keys = list(conf.accounts.keys())
    """账号列表"""
    option_list = OptionList(*account_keys, disabled=True)
    """账号选项列表"""
    selected: Optional[UserAccount] = None
    """选定的账号"""
    empty_data_option = Option("暂无账号数据 请尝试刷新", disabled=True)

    if account_keys:
        # 如果账号列表非空，启用 选择按钮、选项列表
        button_select.enable()
        option_list.disabled = False
    else:
        option_list.add_option(empty_data_option)

    def compose(self) -> ComposeResult:
        yield self.text_view
        yield Horizontal(self.button_select, self.button_refresh, self.button_reset)
        yield self.option_list

    def reset_selected(self):
        """
        重置账号选择
        """
        if not self.account_keys:
            # 选项列表为空时禁用 选择按钮、选项列表
            self.option_list.disabled = True
            self.button_select.disable()
        else:
            # 否则启用 选择按钮、选项列表
            self.option_list.disabled = False
            self.button_select.enable()
        self.button_reset.disable()
        AddressWidget.reset_account()
        self.text_view.update(self.DEFAULT_TEXT)

    def _on_button_pressed(self, event: ControllableButton.Pressed) -> None:
        if event.button.id == "button-account-select":
            # 按下“保存”按钮时触发的事件

            if self.option_list.highlighted is None:
                self.app.notice("[bold red]请先从列表中选择账号！[/]")
                return

            # 禁用选择按钮、启用重置按钮、禁用选项列表
            self.button_select.disable()
            self.button_reset.enable()
            self.option_list.disabled = True

            selected = self.account_keys[self.option_list.highlighted]
            self.selected = selected

            AddressWidget.text_view.update(AddressWidget.DEFAULT_TEXT)
            task = ExchangePlanView.loop.create_task(AddressWidget.update_address(self.app.notice))
            task.add_done_callback(ExchangePlanView.loop_tasks.discard)

            self.text_view.update(f"已选择账户 [bold green]{selected}[/]")
            if conf.accounts[selected].cookies.is_correct():
                self.app.notice(f"选择的账号：[bold green]{selected}[/] Cookies完整，可继续")
            else:
                self.app.notice(
                    f"选择的账号：[bold red]{selected}[/] Cookies不完整，但你仍然可以尝试进行兑换")

        elif event.button.id == "button-account-refresh":
            # 按下“刷新”按钮时触发的事件

            self.account_keys = list(conf.accounts.keys())
            self.option_list.clear_options()
            for account in self.account_keys:
                self.option_list.add_option(account)
            if not self.account_keys:
                self.option_list.add_option(self.empty_data_option)
            # 重置已选内容
            self.reset_selected()
            self.app.notice(f"[bold green]已刷新账号列表[/]")

        elif event.button.id == "button-account-reset":
            # 按下“重置”按钮时触发的事件

            self.reset_selected()
            self.app.notice("已重置账号选择")


class GoodsWidget(BasePlanAdding):
    """
    选择商品 - 界面
    """
    DEFAULT_CSS = """
    GoodsWidget TabbedContainer {
        height: 100%;
        width: 100%;
    }
    """
    DEFAULT_TEXT = Markdown("- 请选择一个商品")
    text_view = StaticStatus(DEFAULT_TEXT)

    button_refresh = ControllableButton("🔄 刷新", variant="primary", id="button-goods-refresh")
    button_reset = ControllableButton("↩ 重置", variant="warning", id="button-goods-reset", disabled=True)

    loading = LoadingDisplay()
    loading.hide()

    good_dict: Dict[int, GoodsDictValue] = {}
    """获取到的商品数据以及相关的控件"""
    selected: Optional[Tuple[GameInfo, int]] = None
    """已选择的商品"""

    empty_data_option = Option("暂无商品数据，可能是目前没有限时兑换的商品，可尝试刷新", disabled=True)
    """空的商品选项列表"""
    tabbed_content = DynamicTabbedContent()

    class GoodsDictValue:
        """
        游戏分区对应的商品数据相关
        """

        def __init__(self,
                     game_info: GameInfo,
                     button_select: Optional[GameButton] = None,
                     tap_pane: Optional[TabPane] = None,
                     good_list: List[Good] = None,
                     ):
            """
            :param game_info: 商品分区数据
            :param tap_pane: 分区对应的 `TabPane` 标签页
            :param good_list: 商品数据
            :param button_select: 选择商品的按钮
            """
            self.game_info = game_info
            """商品分区数据"""
            self.button_select = button_select or GameButton(
                "💾 确定",
                id=f"button-goods-select-{game_info.id}",
                disabled=True,
                game=game_info)
            """选择商品的按钮"""
            self.option_list = OptionList(GoodsWidget.empty_data_option, disabled=True)
            """商品的选项列表"""
            self.tap_pane = tap_pane or TabPane(game_info.name, Horizontal(self.button_select, self.option_list))
            """分区对应的 `TabPane` 标签页"""
            self.good_list = good_list
            """商品数据"""

    def compose(self) -> ComposeResult:
        yield self.text_view
        yield Horizontal(self.button_refresh, self.button_reset, self.loading)
        yield self.tabbed_content

    async def update_goods(self):
        """
        刷新商品信息
        """
        # 进度条、刷新按钮
        self.loading.show()
        self.button_refresh.disable()

        view_actions: List[Callable] = []

        for goods_data in self.good_dict.values():
            good_list_status, good_list = await get_good_list(goods_data.game_info.op_name)
            good_list = list(filter(lambda x: x.is_time_limited(), good_list))

            # 一种情况是获取成功但返回的商品数据为空，一种是API请求失败
            if good_list_status:
                goods_data.option_list.clear_options()
                if good_list:
                    goods_data.good_list = good_list
                    good_names = map(lambda x: x.general_name, good_list)
                    for name in good_names:
                        goods_data.option_list.add_option(name)
                else:
                    goods_data.option_list.add_option(self.empty_data_option)
            else:
                self.app.notice(f"[bold red]获取分区 [bold red]{goods_data.game_info.name}[/] 的商品数据失败！[/]")
                # TODO 待补充各种错误情况

        # 进度条、刷新按钮
        self.loading.hide()
        self.button_refresh.enable()

        # 重置已选内容（包含启用 选择按钮、选项列表）
        self.reset_selected()

    async def _on_mount(self, _: events.Mount):
        # 进度条、刷新按钮
        self.button_refresh.disable()
        self.loading.show()

        # 更新商品分区列表
        game_list_status, game_list = await get_game_list()
        if game_list_status:
            for game in game_list:
                if game.id not in self.good_dict:
                    # 如果没有商品分区对应值，则进行创建
                    goods_data = self.GoodsDictValue(game)
                    self.good_dict.setdefault(game.id, goods_data)
                    await self.tabbed_content.append(goods_data.tap_pane)

            # 更新每个分区的商品数据
            await self.update_goods()
        else:
            self.text_view.update("[bold red]⚠ 获取商品分区列表失败，可尝试刷新[/]")
            self.app.notice("[bold red]获取商品分区列表失败！[/]")
            # TODO 待补充各种错误情况

        # 进度条、刷新按钮
        self.button_refresh.enable()
        self.loading.hide()

    def reset_selected(self):
        """
        重置商品选择
        """
        self.button_reset.disable()
        self.selected = None
        for value in self.good_dict.values():
            if value.good_list:
                value.button_select.enable()
                value.option_list.disabled = False
            else:
                value.button_select.disable()
                value.option_list.disabled = True
        self.text_view.update(self.DEFAULT_TEXT)

    async def _on_button_pressed(self, event: GameButton.Pressed) -> None:
        if event.button.id.startswith("button-goods-select-"):
            # 按下“保存”按钮时触发的事件

            game = event.button.game
            game_id = game.id
            if not game:
                self.app.notice(f"[bold red]未找到对应的分区数据 / 分区不可用[/]")
                return
            option_list = self.good_dict[game_id].option_list
            selected_index = option_list.highlighted
            if selected_index is None:
                self.app.notice(f"[bold red]未选择商品！[/]")
                return
            self.selected = (game, selected_index)
            _, good_index = self.selected
            good = self.good_dict[game_id].good_list[good_index]

            # 启用重置按钮
            self.button_reset.enable()

            # 禁用其他分区的选择按钮
            # 禁用其他分区的选项列表
            for value in self.good_dict.values():
                value.button_select.disable()
                value.option_list.disabled = True

            if good.is_time_end():
                exchange_time_text = "已结束"
                exchange_stoke_text = "无"
            elif good.is_time_limited():
                exchange_time_text = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(good.time))
                exchange_stoke_text = good.num
            else:
                exchange_time_text = "任何时间"
                exchange_stoke_text = "不限"

            self.text_view.update(f"已选择商品："
                                  f"\n[list]"
                                  f"\n🗂️ 商品分区：[bold green]{game.name}[/]"
                                  f"\n📌 名称：[bold green]{good.general_name}[/]"
                                  f"\n💰 价格：[bold green]{good.price}[/] 米游币"
                                  f"\n📦 库存：[bold green]{exchange_stoke_text}[/] 件"
                                  f"\n📅 兑换时间：[bold green]{exchange_time_text}[/]"
                                  f"\n📌 商品ID：[bold green]{good.goods_id}[/]"
                                  f"\n[/list]")

        elif event.button.id == "button-goods-refresh":
            # 按下“刷新”按钮时触发的事件

            # 在初次加载时，如果获取商品分区信息失败，则此时重新获取
            if not self.good_dict:
                await self._on_mount(events.Mount())
            await self.update_goods()

        elif event.button.id == "button-goods-reset":
            # 按下“重置”按钮时触发的事件

            self.reset_selected()
            self.app.notice("已重置商品选择")


class AddressWidget(BasePlanAdding):
    """
    收货地址选择组件
    """

    DEFAULT_TEXT = Markdown("- 请选择一个收货地址")
    REQUIRE_ACCOUNT_TEXT = Markdown("- 请先完成账号选择")
    text_view = StaticStatus(REQUIRE_ACCOUNT_TEXT)

    button_select = ControllableButton("💾 保存", id="button-address-select", disabled=True)
    button_refresh = ControllableButton("🔄 刷新", variant="primary", id="button-address-refresh", disabled=True)
    button_reset = ControllableButton("↩ 重置", variant="warning", id="button-address-reset", disabled=True)

    loading = LoadingDisplay()
    loading.hide()

    empty_data_option = Option("暂无收货地址数据 请尝试刷新", disabled=True)
    option_list = OptionList(empty_data_option)
    """收货地址选项列表"""
    address_list: List[Address] = []
    """收货地址列表"""
    selected: Optional[Address] = None
    """已选地址数据"""

    @classmethod
    async def update_address(cls, notice: Callable[[RenderableType], None]):
        """
        更新收货地址列表
        """
        if AccountWidget.selected is None:
            return

        # 进度条、刷新按钮
        cls.loading.show()
        cls.button_refresh.disable()

        address_status, cls.address_list = await get_address(AccountWidget.selected)
        if address_status:
            cls.option_list.clear_options()
            for address_data in cls.address_list:
                preview_text = f"[list]" \
                               f"\n👓 收货人：[bold green]{address_data.connect_name}[/]" \
                               f"\n📞 联系电话：[bold green]{address_data.phone}[/]" \
                               f"\n📮 收货地址：" \
                               f"\n     省：[bold green]{address_data.province_name}[/]" \
                               f"\n     市：[bold green]{address_data.city_name}[/]" \
                               f"\n     区/县：[bold green]{address_data.county_name}[/]" \
                               f"\n     详细地址：[bold green]{address_data.addr_ext}[/]" \
                               f"\n📌 地址ID：[bold green]{address_data.id}[/]" \
                               f"\n[/list]"
                cls.option_list.append(Option(preview_text))
            if not cls.address_list:
                cls.option_list.add_option(cls.empty_data_option)
        else:
            notice(f"[bold red]获取收货地址列表失败！[/]")

        # 进度条、刷新按钮
        cls.loading.hide()
        cls.button_refresh.enable()

    def compose(self) -> ComposeResult:
        yield self.text_view
        yield Horizontal(self.button_select, self.button_refresh, self.button_reset)
        yield self.option_list

    @classmethod
    def reset_account(cls):
        """
        重置已选账号
        - 重置已选地址
        - 重置文本内容
        - 禁用所有按钮
        - 禁用选项列表
        - 清空选项列表
        """
        cls.selected = None
        cls.text_view.update(cls.REQUIRE_ACCOUNT_TEXT)
        cls.button_select.disable()
        cls.button_reset.disable()
        cls.button_refresh.disable()
        cls.option_list.disabled = True
        cls.option_list.clear_options()

    def reset_selected(self):
        """
        重置已选地址
        """
        if self.address_list:
            self.button_select.enable()
            self.option_list.disabled = False
        else:
            self.button_select.disable()
            self.option_list.disabled = True
        self.selected = None
        self.text_view.update(self.DEFAULT_TEXT)
        self.button_reset.disable()

    async def _on_button_pressed(self, event: ControllableButton.Pressed) -> None:
        if event.button.id == "button-address-select":
            # 按下“保存”按钮时触发的事件

            address_index = self.option_list.highlighted
            if address_index is None:
                self.app.notice(f"[bold red]未选择收货地址！[/]")
                return
            self.selected = address_index

            self.text_view.update(f"已选择收货地址："
                                  f"\n[list]"
                                  f"\n📌 地址ID：[bold green]{self.selected.id}[/]"
                                  f"\n[/list]")

            # 禁用 选项列表、保存按钮，启用 重置按钮
            self.button_reset.enable()
            self.button_select.disable()
            self.option_list.disabled = True

        elif event.button.id == "button-address-refresh":
            # 按下“刷新”按钮时触发的事件

            await self.update_address(self.app.notice)
            self.reset_selected()

        elif event.button.id == "button-address-reset":
            # 按下“重置”按钮时触发的事件

            self.reset_selected()
            self.app.notice("已重置收获地址选择")
