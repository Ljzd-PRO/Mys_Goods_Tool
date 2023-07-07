from __future__ import annotations

from abc import abstractmethod
from typing import Tuple, Optional, List, Dict, Union, Type, TypeVar

from rich.console import RenderableType
from rich.markdown import Markdown
from textual import events
from textual.app import ComposeResult
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import (
    TabbedContent, TabPane, OptionList, ListView
)
from textual.widgets._option_list import Option, Separator

from mys_goods_tool.api import get_good_list, get_address, get_game_record, good_exchange, \
    get_good_detail, get_good_games, get_device_fp
from mys_goods_tool.custom_css import *
from mys_goods_tool.custom_widget import StaticStatus, ControllableButton, LoadingDisplay, \
    DynamicTabbedContent, GameButton, PlanButton, UnClickableItem
from mys_goods_tool.data_model import Good, Address, GameRecord
from mys_goods_tool.user_data import config as conf, UserAccount, ExchangePlan
from mys_goods_tool.utils import logger

_T = TypeVar("_T")


class BaseExchangePlan(ExchangePlanContent):
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
    _selected: Optional[Type[_T]] = None
    """已选内容"""

    empty_data_option: Option
    """可选列表为空时显示的视图"""

    @property
    def selected(self):
        """已选内容"""
        return self._selected

    @selected.setter
    def selected(self, value: Type[_T]):
        """设置已选内容的同时更新CheckOutText兑换计划预览视图"""
        type(self)._selected = value
        FinishContent.check_out_text.set_check_item(value, type(self))

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

    @abstractmethod
    def update_data(self):
        """
        更新数据
        一般包含：
            - 更新选项列表
            - 如果列表为空，加入空数据提示项
            - 重置已选内容
        """
        pass

    def reset_all(self) -> None:
        """
        重置所有内容
        - 重置已选游戏账号
        - 重置文本内容
        - 禁用所有按钮
        - 禁用选项列表
        - 清空选项列表
        """
        pass


class AccountContent(BaseExchangePlan):
    """
    选择账号视图
    """
    DEFAULT_TEXT = Markdown("- 请选择一个米游社账号")
    text_view = StaticStatus(DEFAULT_TEXT)

    button_select = ControllableButton("💾 保存", id="button-account-select", disabled=True)
    button_refresh = ControllableButton("🔄 刷新", variant="primary", id="button-account-refresh")
    button_reset = ControllableButton("↩ 重置", variant="warning", id="button-account-reset", disabled=True)

    account_keys = list(conf.accounts.keys())
    """账号列表"""
    option_list = OptionList(*account_keys, disabled=True)
    """账号选项列表"""
    empty_data_option = Option("暂无米游社账号数据 请尝试刷新", disabled=True)

    if account_keys:
        # 如果账号列表非空，启用 选择按钮、选项列表
        button_select.enable()
        option_list.disabled = False
    else:
        option_list.add_option(empty_data_option)

    def __init__(self, *children: Widget):
        super().__init__(*children)

    def compose(self) -> ComposeResult:
        yield self.text_view
        with Horizontal():
            yield self.button_select
            yield self.button_refresh
            yield self.button_reset
        yield self.option_list

    def reset_selected(self):
        """
        重置账号选择
        """
        # 刷新选项列表后检查是否为空
        if not self.account_keys:
            self.option_list.disabled = True
            self.button_select.disable()
        else:
            self.option_list.disabled = False
            self.button_select.enable()

        self.selected = None
        self.button_reset.disable()
        self.text_view.update(self.DEFAULT_TEXT)
        ExchangePlanView.address_content.reset_all()
        ExchangePlanView.game_record_content.reset_all()

    def update_data(self):
        """
        更新账号列表
        """
        self.account_keys = list(conf.accounts.keys())
        self.option_list.clear_options()
        for account in self.account_keys:
            self.option_list.add_option(account)
        if not self.account_keys:
            self.option_list.add_option(self.empty_data_option)
        # 重置已选内容
        self.reset_selected()

    async def _on_button_pressed(self, event: ControllableButton.Pressed) -> None:
        if event.button.id == "button-account-select":
            # 按下“保存”按钮时触发的事件

            if self.option_list.highlighted is None:
                self.app.notice("[bold red]请先从列表中选择米游社账号！[/]")
                return

            account_key = self.account_keys[self.option_list.highlighted]
            self.selected = conf.accounts.get(account_key)
            if self.selected is None:
                self.app.notice(f"未找到米游社账号：[bold red]{account_key}[/]")
                return

            # 禁用选择按钮、启用重置按钮、禁用选项列表
            self.button_select.disable()
            self.button_reset.enable()
            self.option_list.disabled = True

            self.text_view.update(f"已选择米游社账号"
                                  f"\n[list]"
                                  f"\n🪪 通信证ID - [bold green]{account_key}[/]"
                                  f"\n[/list]")
            if conf.accounts[account_key].cookies.is_correct():
                self.app.notice(f"选择的米游社账号：[bold green]{account_key}[/] Cookies完整，可继续")
            else:
                self.app.notice(
                    f"选择的米游社账号：[bold red]{account_key}[/] Cookies不完整，但你仍然可以尝试进行兑换")

            await ExchangePlanView.address_content.update_data()
            await ExchangePlanView.game_record_content.update_data()

        elif event.button.id == "button-account-refresh":
            # 按下“刷新”按钮时触发的事件

            self.update_data()
            self.app.notice("[bold green]已刷新米游社账号列表[/]")

        elif event.button.id == "button-account-reset":
            # 按下“重置”按钮时触发的事件

            self.reset_selected()
            self.app.notice("已重置米游社账号选择")


class GoodsContent(BaseExchangePlan):
    """
    选择商品视图
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

    good_dict: Dict[str, GoodsDictValue] = {}
    """获取到的商品数据以及相关的控件 商品分区简称 -> 商品数据"""
    selected_tuple: Optional[Tuple[Tuple[str, str], int]] = None
    """已选择的商品位置 ((商品分区, 分区简称), 商品在OptionList中的位置)"""

    empty_data_option = Option("暂无商品数据，可能是目前没有限时兑换的商品，可尝试刷新", disabled=True)
    """空的商品选项列表"""
    tabbed_content = DynamicTabbedContent()

    class GoodsDictValue:
        """
        游戏频道对应的商品数据相关
        """

        def __init__(self,
                     partition: Tuple[str, str],
                     button_select: Optional[GameButton] = None,
                     tap_pane: Optional[TabPane] = None,
                     good_list: List[Good] = None,
                     ):
            """
            :param partition: (商品分区, 字母简称) 数据
            :param tap_pane: 频道对应的 `TabPane` 标签页
            :param good_list: 商品数据
            :param button_select: 选择商品的按钮
            """
            name, abbr = partition
            self.partition = partition
            """商品频道数据"""
            self.button_select = button_select or GameButton(
                "💾 确定",
                id=f"button-goods-select-{abbr}",
                disabled=True,
                partition=partition)
            """选择商品的按钮"""
            self.option_list = OptionList(GoodsContent.empty_data_option, disabled=True)
            """商品的选项列表"""
            self.tap_pane = tap_pane or TabPane(name, Horizontal(self.button_select, self.option_list))
            """频道对应的 `TabPane` 标签页"""
            self.good_list = good_list
            """商品数据"""

    def compose(self) -> ComposeResult:
        yield self.text_view
        with Horizontal():
            yield self.button_refresh
            yield self.button_reset
            yield self.loading
        yield self.tabbed_content

    async def update_data(self):
        """
        刷新商品信息
        """
        # 进度条、刷新按钮
        self.loading.show()
        self.button_refresh.disable()

        for goods_data in self.good_dict.values():
            name, abbr = goods_data.partition
            good_list_status, good_list = await get_good_list(abbr)
            good_list = list(filter(lambda x: x.time_limited and not x.time_end, good_list))

            # 一种情况是获取成功但返回的商品数据为空，一种是API请求失败
            goods_data.option_list.clear_options()
            if not good_list_status:
                self.app.notice(f"[bold red]获取频道 [bold red]{name}[/] 的商品数据失败！[/]")
                # TODO 待补充各种错误情况
            if good_list:
                goods_data.good_list = good_list
                good_names = map(lambda x: x.general_name, good_list)
                for name in good_names:
                    goods_data.option_list.add_option(name)
                goods_data.button_select.enable()
                goods_data.option_list.disabled = False
            else:
                goods_data.option_list.add_option(self.empty_data_option)

        # 进度条、刷新按钮
        self.loading.hide()
        self.button_refresh.enable()

        # 重置已选内容（包含启用 选择按钮、选项列表）
        self.reset_selected()

    async def _on_mount(self, _: events.Mount):
        # 进度条、刷新按钮
        self.button_refresh.disable()
        self.loading.show()

        # 更新商品频道列表
        partition_status, partition_all = await get_good_games()

        # 刷新按钮、进度条
        self.button_refresh.enable()
        self.loading.hide()

        if partition_status:
            # 过滤掉 "全部" 分区
            partitions = filter(lambda x: x[1] != "all", partition_all)
            for name, abbr in partitions:
                if abbr not in self.good_dict:
                    # 如果没有商品频道对应值，则进行创建
                    goods_data = self.GoodsDictValue((name, abbr))
                    self.good_dict.setdefault(abbr, goods_data)
                    await self.tabbed_content.append(goods_data.tap_pane)

            # 更新每个频道的商品数据
            await self.update_data()
            return True
        else:
            self.text_view.update("[bold red]⚠ 获取商品频道列表失败，可尝试刷新[/]")
            self.app.notice("[bold red]获取商品频道列表失败！[/]")
            # TODO 待补充各种错误情况
            return False

    def reset_selected(self):
        """
        重置商品选择
        """
        # 刷新选项列表后检查是否为空
        for value in self.good_dict.values():
            if value.good_list:
                value.button_select.enable()
                value.option_list.disabled = False
            else:
                value.button_select.disable()
                value.option_list.disabled = True

        self.selected = None
        self.button_reset.disable()
        self.selected_tuple = None
        self.text_view.update(self.DEFAULT_TEXT)

        AddressContent.check_good_type()
        ExchangePlanView.game_record_content.reset_selected()
        GameRecordContent.check_good_type()

    async def _on_button_pressed(self, event: GameButton.Pressed) -> None:
        if event.button.id.startswith("button-goods-select"):
            # 按下“保存”按钮时触发的事件

            name, abbr = event.button.partition
            option_list = self.good_dict[abbr].option_list
            selected_index = option_list.highlighted
            if selected_index is None:
                self.app.notice("[bold red]请先从列表中选择商品！[/]")
                return
            good_dict_value = self.good_dict.get(abbr)
            if not good_dict_value:
                self.app.notice("[bold red]未找到对应的频道[/]")
                return

            good = good_dict_value.good_list[selected_index]
            GoodsContent.selected_tuple = name, abbr, selected_index

            # 获取商品详情
            self.loading.show()
            good_detail_status, _ = await get_good_detail(good)
            self.loading.hide()
            if not good_detail_status:
                # TODO 待补充各种错误情况
                self.app.notice("[bold red]获取商品详情(game_biz)失败，但你仍然可以尝试进行兑换[/]")
            self.selected = good

            # 启用重置按钮
            self.button_reset.enable()

            # 禁用其他频道的选择按钮
            # 禁用其他频道的选项列表
            for value in self.good_dict.values():
                value.button_select.disable()
                value.option_list.disabled = True

            # 如果是虚拟/实物商品，则地址、游戏账号视图需要更新
            AddressContent.check_good_type()
            if AccountContent._selected is not None:
                GameRecordContent.check_good_type()

            self.text_view.update(f"已选择商品："
                                  f"\n[list]"
                                  f"\n🗂️ 商品频道：[bold green]{name}[/]"
                                  f"\n📌 名称：[bold green]{good.general_name}[/]"
                                  f"\n💰 价格：[bold green]{good.price}[/] 米游币"
                                  f"\n📦 库存：[bold green]{good.stoke_text}[/] 件"
                                  f"\n📅 兑换时间：[bold green]{good.time_text}[/]"
                                  f"\n📌 商品ID：[bold green]{good.goods_id}[/]"
                                  f"\n[/list]")

            if good.is_virtual and AccountContent._selected is not None:
                await ExchangePlanView.game_record_content.update_data()

        elif event.button.id == "button-goods-refresh":
            # 按下“刷新”按钮时触发的事件

            # 在初次加载时，如果获取商品频道信息失败，则此时重新获取
            if not self.good_dict:
                good_games_result = await self._on_mount(events.Mount())
            else:
                good_games_result = True
            if good_games_result:
                await self.update_data()

        elif event.button.id == "button-goods-reset":
            # 按下“重置”按钮时触发的事件

            self.reset_selected()
            self.app.notice("已重置商品选择")


class GameRecordContent(BaseExchangePlan):
    """
    游戏账号选择视图
    """
    DEFAULT_TEXT = Markdown("- 请选择一个游戏账号")
    REQUIRE_OTHER_TEXT = Markdown("- 请先完成米游社账号和商品选择")
    UNNEEDED_TEXT = Markdown("- 兑换实体商品无需选择游戏账号")

    text_view = StaticStatus(REQUIRE_OTHER_TEXT)

    button_select = ControllableButton("💾 保存", id="button-game_uid-select", disabled=True)
    button_refresh = ControllableButton("🔄 刷新", variant="primary", id="button-game_uid-refresh", disabled=True)
    button_reset = ControllableButton("↩ 重置", variant="warning", id="button-game_uid-reset", disabled=True)

    loading = LoadingDisplay()
    loading.hide()

    empty_data_option = Option("无可用账号", disabled=True)
    option_list = OptionList(REQUIRE_OTHER_TEXT, disabled=True)
    """游戏账号选项列表"""
    option_list.highlighted = None
    record_list: List[GameRecord] = []
    """游戏账号列表"""

    async def update_data(self):
        """
        更新游戏账号列表
        """
        if GoodsContent._selected is None:
            return

        # 进度条、刷新按钮、选项列表
        self.loading.show()
        self.button_refresh.disable()
        self.option_list.disabled = False

        record_status, GameRecordContent.record_list = await get_game_record(AccountContent._selected)
        self.option_list.clear_options()
        if not record_status:
            self.app.notice(f"[bold red]获取游戏账号列表失败！[/]")
        if self.record_list:
            self.option_list.add_option(Separator())
            for record in self.record_list:
                preview_text = f"[list]" \
                               f"\n👓 昵称：[bold underline]{record.nickname}[/]" \
                               f"\n📌 游戏UID：[bold underline]{record.game_role_id}[/]" \
                               f"\n🌐 区服：[bold underline]{record.region_name}[/]" \
                               f"\n🔥 等级：[bold underline]{record.level}[/]" \
                               f"\n[/list]"
                self.option_list.add_option(Option(preview_text))
                self.option_list.add_option(Separator())
                self.option_list.disabled = False
                self.button_select.enable()
        else:
            self.option_list.add_option(self.empty_data_option)

        # 进度条、刷新按钮
        self.loading.hide()
        self.button_refresh.enable()

        #  重置已选择的游戏账号
        self.reset_selected()

        # 检查选项列表是否为空的操作包含在 check_good_type 中
        self.check_good_type()

    def reset_all(self):
        self.selected = None
        self.text_view.update(self.REQUIRE_OTHER_TEXT)
        self.option_list.disabled = True
        self.option_list.clear_options()
        self.option_list.add_option(self.REQUIRE_OTHER_TEXT)
        self.button_select.disable()
        self.button_reset.disable()
        self.button_refresh.disable()

    @classmethod
    def check_empty(cls):
        """
        检查选项列表是否为空
        """
        if cls.record_list:
            cls.button_select.enable()
            cls.option_list.disabled = False
        else:
            cls.button_select.disable()
            cls.option_list.disabled = True

    @classmethod
    def check_good_type(cls):
        """
        检查商品类型是否是虚拟商品，并改变视图
        """
        # 程序载入初次刷新商品列表时，重置已选商品并调用check_good_type，由于没有选择商品，不需要检查商品类型
        if GoodsContent._selected is not None:
            good: Optional[Good] = GoodsContent._selected
            if good is not None and not good.is_virtual:
                cls.text_view.update(cls.UNNEEDED_TEXT)
                cls.option_list.disabled = True
                cls.button_select.disable()
                cls.button_refresh.disable()
            elif cls._selected is None:
                cls.text_view.update(cls.DEFAULT_TEXT)
                cls.check_empty()
                cls.button_refresh.enable()
            else:
                # 在已选游戏账号不为空的情况下，视图被虚拟商品改变后的情况
                ExchangePlanView.game_record_content._set_select_view(cls._selected)
        else:
            # # 程序载入初次刷新商品列表时，重置已选商品并调用本类的reset_selected，由于没有选择商品，需要更新文本视图
            cls.text_view.update(cls.REQUIRE_OTHER_TEXT)

    def reset_selected(self):
        self.selected = None
        self.button_reset.disable()
        self.text_view.update(self.DEFAULT_TEXT)
        self.check_good_type()

    def _set_select_view(self, record: GameRecord):
        """
        设置已选地址后改变视图
        """
        self.text_view.update(f"已选择游戏账号："
                              f"\n[list]"
                              f"\n📌 游戏UID - [bold green]{record.game_role_id}[/]"
                              f"\n[/list]")

        # 禁用 选项列表、保存按钮，启用 重置按钮
        self.button_reset.enable()
        self.button_select.disable()
        self.option_list.disabled = True

    async def _on_button_pressed(self, event: ControllableButton.Pressed) -> None:
        if event.button.id == "button-game_uid-select":
            # 按下“保存”按钮时触发的事件

            record_index = self.option_list.highlighted
            if record_index is None:
                self.app.notice("[bold red]请先从列表中选择游戏账号！[/]")
                return
            if record_index >= len(self.record_list):
                self.app.notice("[bold red]无法找到游戏账号[/]")
                return
            record = self.record_list[record_index]
            self.selected = record

            self._set_select_view(record)

        elif event.button.id == "button-game_uid-refresh":
            # 按下“刷新”按钮时触发的事件

            await self.update_data()

        elif event.button.id == "button-game_uid-reset":
            # 按下“重置”按钮时触发的事件

            self.reset_selected()
            self.app.notice("已重置游戏账号选择")

    def compose(self) -> ComposeResult:
        yield self.text_view
        with Horizontal():
            yield self.button_select
            yield self.button_refresh
            yield self.button_reset
            yield self.loading
        yield self.option_list


class AddressContent(BaseExchangePlan):
    """
    收货地址选择视图
    """

    DEFAULT_TEXT = Markdown("- 请选择一个收货地址")
    REQUIRE_ACCOUNT_TEXT = Markdown("- 请先完成米游社账号选择")
    UNNEEDED_TEXT = Markdown("- 兑换虚拟商品无需设置收货地址")

    text_view = StaticStatus(REQUIRE_ACCOUNT_TEXT)

    button_select = ControllableButton("💾 保存", id="button-address-select", disabled=True)
    button_refresh = ControllableButton("🔄 刷新", variant="primary", id="button-address-refresh", disabled=True)
    button_reset = ControllableButton("↩ 重置", variant="warning", id="button-address-reset", disabled=True)

    loading = LoadingDisplay()
    loading.hide()

    empty_data_option = Option("暂无收货地址数据 请尝试刷新", disabled=True)
    option_list = OptionList(REQUIRE_ACCOUNT_TEXT, disabled=True)
    """收货地址选项列表"""
    option_list.highlighted = None
    address_list: List[Address] = []
    """收货地址列表"""

    async def update_data(self):
        """
        更新收货地址列表
        """
        if AccountContent._selected is None:
            return

        # 进度条、刷新按钮、选项列表
        self.loading.show()
        self.button_refresh.disable()
        self.option_list.disabled = False

        address_status, AddressContent.address_list = await get_address(AccountContent._selected)
        self.option_list.clear_options()
        if not address_status:
            self.app.notice(f"[bold red]获取收货地址列表失败！[/]")
        if self.address_list:
            self.option_list.add_option(Separator())
            for address_data in self.address_list:
                preview_text = f"[list]" \
                               f"\n👓 收货人：[bold underline]{address_data.connect_name}[/]" \
                               f"\n📞 联系电话：[bold underline]{address_data.phone}[/]" \
                               f"\n📮 收货地址：" \
                               f"\n     省：[bold underline]{address_data.province_name}[/]" \
                               f"\n     市：[bold underline]{address_data.city_name}[/]" \
                               f"\n     区/县：[bold underline]{address_data.county_name}[/]" \
                               f"\n     详细地址：[bold underline]{address_data.addr_ext}[/]" \
                               f"\n📌 地址ID：[bold underline]{address_data.id}[/]" \
                               f"\n[/list]"
                self.option_list.add_option(Option(preview_text))
                self.option_list.add_option(Separator())
                self.option_list.disabled = False
                self.button_select.enable()
        else:
            self.option_list.add_option(self.empty_data_option)

        # 进度条、刷新按钮
        self.loading.hide()
        self.button_refresh.enable()

        #  重置已选地址
        self.reset_selected()

        # 检查选项列表是否为空的操作包含在 check_good_type 中
        self.check_good_type()

    def reset_all(self):
        self.selected = None
        self.text_view.update(self.REQUIRE_ACCOUNT_TEXT)
        self.option_list.disabled = True
        self.option_list.clear_options()
        self.option_list.add_option(self.REQUIRE_ACCOUNT_TEXT)
        self.button_select.disable()
        self.button_reset.disable()
        self.button_refresh.disable()

    @classmethod
    def check_empty(cls):
        """
        检查选项列表是否为空
        """
        if cls.address_list:
            cls.button_select.enable()
            cls.option_list.disabled = False
        else:
            cls.button_select.disable()
            cls.option_list.disabled = True

    @classmethod
    def check_good_type(cls):
        """
        检查商品类型是否是虚拟商品，并改变视图
        """
        # 程序载入初次刷新商品列表时，重置已选商品并调用check_good_type，由于没有选择商品，不需要检查商品类型
        if AccountContent._selected is not None:
            good: Optional[Good] = GoodsContent._selected
            if good is not None and good.is_virtual:
                cls.text_view.update(cls.UNNEEDED_TEXT)
                cls.option_list.disabled = True
                cls.button_select.disable()
                cls.button_refresh.disable()
            elif cls._selected is None:
                cls.text_view.update(cls.DEFAULT_TEXT)
                cls.check_empty()
                cls.button_refresh.enable()
            else:
                # 在已选地址不为空的情况下，视图被虚拟商品改变后的情况
                ExchangePlanView.address_content._set_select_view(cls._selected)

    def reset_selected(self):
        """
        重置已选地址
        """
        self.selected = None
        self.button_reset.disable()
        self.text_view.update(self.DEFAULT_TEXT)
        self.check_good_type()

    def _set_select_view(self, address: Address):
        """
        设置已选地址后改变视图
        """
        self.text_view.update(f"已选择收货地址："
                              f"\n[list]"
                              f"\n📌 地址ID - [bold green]{address.id}[/]"
                              f"\n[/list]")

        # 禁用 选项列表、保存按钮，启用 重置按钮
        self.button_reset.enable()
        self.button_select.disable()
        self.option_list.disabled = True

    async def _on_button_pressed(self, event: ControllableButton.Pressed) -> None:
        if event.button.id == "button-address-select":
            # 按下“保存”按钮时触发的事件

            address_index = self.option_list.highlighted
            if address_index is None:
                self.app.notice("[bold red]请先从列表中选择收货地址！[/]")
                return
            if address_index >= len(self.address_list):
                self.app.notice("[bold red]无法找到收货地址[/]")
                return
            address = self.address_list[address_index]
            self.selected = address

            self._set_select_view(address)

        elif event.button.id == "button-address-refresh":
            # 按下“刷新”按钮时触发的事件

            await self.update_data()

        elif event.button.id == "button-address-reset":
            # 按下“重置”按钮时触发的事件

            self.reset_selected()
            self.app.notice("已重置收货地址选择")

    def compose(self) -> ComposeResult:
        yield self.text_view
        with Horizontal():
            yield self.button_select
            yield self.button_refresh
            yield self.button_reset
            yield self.loading
        yield self.option_list


class CheckOutText(StaticStatus):
    """
    兑换计划预览文本
    """
    DEFAULT_TEXT = "[bold yellow]待选取[/]"
    UNNEEDED_TEXT = "[bold gray]无需设置[/]"
    account_text = reactive(DEFAULT_TEXT)
    address_detail = reactive(DEFAULT_TEXT)
    goods_name = reactive(DEFAULT_TEXT)
    goods_time = reactive(DEFAULT_TEXT)
    game_uid_text = reactive(DEFAULT_TEXT)

    def set_check_item(self,
                       value: Union[UserAccount, Address, Good, None],
                       content_type: Optional[Type[BaseExchangePlan]] = None
                       ):
        """
        传入 Union[UserAccount, Address, Good] 对象，设置对应的文本内容
        :param value: 兑换计划所需的数据对象
        :param content_type: 当 value 为 None 时，需要传入 BaseExchangePlan 对象，用于确定数据类型
        """

        def finished_style_text(text: str):
            return f"[bold green]{text}[/]"

        if value is None:
            if content_type == AccountContent:
                self.account_text = self.DEFAULT_TEXT
            elif content_type == AddressContent:
                good: Optional[Good] = ExchangePlanView.goods_content.selected
                if good is not None and not good.is_virtual:
                    self.address_detail = self.DEFAULT_TEXT
            elif content_type == GoodsContent:
                self.goods_name = self.DEFAULT_TEXT
                self.goods_time = self.DEFAULT_TEXT
                # 把“无需设置”还原为“待选取”
                self.address_detail = self.DEFAULT_TEXT
                self.game_uid_text = self.DEFAULT_TEXT
            elif content_type == GameRecordContent:
                good: Optional[Good] = ExchangePlanView.goods_content.selected
                if good is not None and good.is_virtual:
                    self.game_uid_text = self.DEFAULT_TEXT

            ExchangePlanView.finish_content.button_submit.disable()
            ExchangePlanView.finish_content.button_test.disable()
        else:
            if isinstance(value, UserAccount):
                self.account_text = finished_style_text(value.bbs_uid)
            elif isinstance(value, Address):
                self.address_detail = finished_style_text(value.addr_ext)
            elif isinstance(value, Good):
                self.goods_name = finished_style_text(value.general_name)
                self.goods_time = finished_style_text(value.time_text)
                if value.is_virtual:
                    self.address_detail = self.UNNEEDED_TEXT
                else:
                    self.game_uid_text = self.UNNEEDED_TEXT
            elif isinstance(value, GameRecord):
                self.game_uid_text = finished_style_text(str(value.game_role_id))

            account: UserAccount = ExchangePlanView.account_content.selected
            good: Good = ExchangePlanView.goods_content.selected
            address: Address = ExchangePlanView.address_content.selected
            record: GameRecord = ExchangePlanView.game_record_content.selected
            if account is not None \
                    and good is not None \
                    and (address is not None or good.is_virtual) \
                    and (record is not None or not good.is_virtual):
                ExchangePlanView.finish_content.button_submit.enable()
                ExchangePlanView.finish_content.button_test.enable()
            else:
                ExchangePlanView.finish_content.button_submit.disable()
                ExchangePlanView.finish_content.button_test.disable()

        self.refresh()

    def render(self) -> RenderableType:
        return f"请确认兑换计划信息：" \
               f"\n[list]" \
               f"\n👓 米游社账号 - {self.account_text}" \
               f"\n📦 商品名称 - {self.goods_name}" \
               f"\n📅 兑换时间 - {self.goods_time}" \
               f"\n🎮 游戏UID - {self.game_uid_text}" \
               f"\n📮 收货地址 - {self.address_detail}" \
               f"\n[/list]"


class FinishContent(ExchangePlanContent):
    """
    完成兑换计划添加的视图
    """
    check_out_text = CheckOutText()
    button_submit = ControllableButton("💾 保存兑换计划", variant="success", id="button-finish-submit", disabled=True)
    button_test = ControllableButton("🔧 测试兑换", id="button-finish-test", disabled=True)
    loading = LoadingDisplay()
    loading.hide()

    def compose(self) -> ComposeResult:
        yield self.check_out_text
        with Horizontal():
            yield self.button_submit
            yield self.button_test
            yield self.loading

    async def _on_button_pressed(self, event: ControllableButton.Pressed):
        if event.button.id.startswith("button-finish"):
            account: UserAccount = ExchangePlanView.account_content.selected
            good: Good = ExchangePlanView.goods_content.selected
            address: Optional[Address] = ExchangePlanView.address_content.selected
            record: Optional[GameRecord] = ExchangePlanView.game_record_content.selected
            plan = ExchangePlan(good=good,
                                address=address,
                                account=account,
                                game_record=record)
            if event.button.id == "button-finish-submit":
                if plan in conf.exchange_plans:
                    self.app.notice(f"[bold yellow]该兑换计划已存在[/]")
                else:
                    conf.exchange_plans.add(plan)
                    if not plan.account.device_fp:
                        logger.info(f"账号 {plan.account.bbs_uid} 未设置 device_fp，正在获取...")
                        fp_status, plan.account.device_fp = await get_device_fp(plan.account.device_id_ios)
                        if fp_status:
                            logger.info(f"成功获取 device_fp: {plan.account.device_fp}")
                    if conf.save():
                        self.app.notice(f"[bold green]已保存兑换计划[/]")
                    else:
                        self.app.notice(f"[bold red]保存兑换计划失败[/]")
                        # TODO: 保存失败的具体原因提示
                    await ExchangePlanView.manager_content.update_data()
            elif event.button.id == "button-finish-test":
                exchange_status, _ = await good_exchange(plan)
                if not exchange_status.network_error:
                    self.app.notice(f"[bold green]兑换请求已发送，请查看日志[/]")
                else:
                    self.app.notice(f"[bold red]兑换请求发送失败，请检查网络连接[/]")


class ExchangePlanRow(Container):
    """
    兑换计划行
    """

    def __init__(self, plan: ExchangePlan):
        self.plan = plan
        self.button_delete = PlanButton("🧹 删除计划",
                                        variant="warning",
                                        id=f"button-plan_row-delete-{plan.__hash__()}",
                                        plan=plan)
        self.button_confirm = PlanButton("⚠ 确认删除",
                                         variant="error",
                                         id=f"button-plan_row-confirm-{plan.__hash__()}",
                                         plan=plan)

        self.button_test = PlanButton("🔧 测试兑换",
                                      id=f"button-plan_row-test-{plan.__hash__()}",
                                      plan=plan)
        self.button_cancel = PlanButton("↩ 取消删除",
                                        variant="warning",
                                        id=f"button-plan_row-cancel-{plan.__hash__()}",
                                        plan=plan)
        self.button_confirm.hide()
        self.button_cancel.hide()
        super().__init__()

    def compose(self) -> ComposeResult:
        yield StaticStatus(f"[list]"
                           f"\n👓 米游社账号 - {self.plan.account.bbs_uid}"
                           f"\n📦 商品名称 - {self.plan.good.goods_name}"
                           f"\n📅 兑换时间 - {self.plan.good.time_text}"
                           f"\n🎮 游戏UID - {self.plan.game_record.game_role_id if self.plan.game_record is not None else '无需设置'}"
                           f"\n📮 收货地址 - {self.plan.address.addr_ext if self.plan.address is not None else '无需设置'}"
                           f"\n[/list]")
        with Horizontal():
            yield self.button_delete
            yield self.button_confirm
            yield self.button_test
            yield self.button_cancel

    async def _on_button_pressed(self, event: PlanButton.Pressed):
        if event.button.id.startswith("button-plan_row-delete"):
            self.button_delete.hide()
            self.button_confirm.show()
            self.button_test.hide()
            self.button_cancel.show()

        elif event.button.id.startswith("button-plan_row-confirm"):
            conf.exchange_plans.remove(event.button.plan)
            conf.save()
            self.app.notice(f"[bold red]已删除兑换计划[/]")
            await ExchangePlanView.manager_content.update_data()
            # TODO: 删除计划后不刷新整个列表，而是单独删除该行，但目前测试这种方法无效
            # await ManagerContent.list_view.query(ManagerContent.list_item_id(event.button.plan)).remove()
            # ManagerContent.list_view.index = None
            # ManagerContent.list_view.refresh()

        elif event.button.id.startswith("button-plan_row-test"):
            exchange_status, _ = await good_exchange(event.button.plan)
            if not exchange_status.network_error:
                self.app.notice(f"[bold green]兑换请求已发送，请查看日志[/]")
            else:
                self.app.notice(f"[bold red]兑换请求发送失败，请检查网络连接[/]")

        elif event.button.id.startswith("button-plan_row-cancel"):
            self.button_delete.show()
            self.button_confirm.hide()
            self.button_test.show()
            self.button_cancel.hide()


class ManagerContent(ExchangePlanContent):
    """
    管理兑换计划的视图
    """
    DEFAULT_CSS = """
    ManagerContent UnClickableItem {
        padding: 1;
    }
    """
    button_refresh = ControllableButton("🔄 刷新计划列表", id="button-manager-refresh")
    list_view = ListView(initial_index=None)

    @classmethod
    def list_item_id(cls, plan: ExchangePlan):
        """
        生成兑换计划列表项Widget的ID

        :param plan: 兑换计划
        """
        return f"list_item-plan_row-{plan.__hash__()}"

    @property
    def empty_data_item(self):
        """
        :return: 没有数据时的列表项
        """
        return UnClickableItem(Static("暂无兑换计划数据 请尝试刷新"), disabled=True)

    def compose(self) -> ComposeResult:
        yield self.button_refresh
        yield self.list_view

    async def update_data(self):
        """
        刷新兑换计划列表
        """
        await self.list_view.clear()
        for plan in conf.exchange_plans:
            self.list_view.disabled = False
            await self.list_view.append(
                UnClickableItem(
                    ExchangePlanRow(plan),
                    id=self.list_item_id(plan)
                )
            )
        if not conf.exchange_plans:
            self.list_view.disabled = True
            await self.list_view.append(self.empty_data_item)

    async def _on_button_pressed(self, event: ControllableButton.Pressed):
        if event.button.id == "button-manager-refresh":
            await self.update_data()

    async def _on_mount(self, event: events.Mount) -> None:
        await self.update_data()


class ExchangePlanView(Container):
    """
    添加兑换计划 - 视图
    """
    DEFAULT_CSS = """
    ExchangePlanView {
        height: auto;
        width: 1fr;
        border: round #666;
        padding: 2;
        margin: 1 0;
    }
    """

    account_content = AccountContent()
    goods_content = GoodsContent()
    game_record_content = GameRecordContent()
    address_content = AddressContent()
    finish_content = FinishContent()
    manager_content = ManagerContent()

    def compose(self) -> ComposeResult:
        with TabbedContent():
            with TabPane("➕添加计划"):
                with TabbedContent():
                    with TabPane("1.选择米游社账号"):
                        yield self.account_content
                    with TabPane("2.选择目标商品"):
                        yield self.goods_content
                    with TabPane("3.选择游戏账号"):
                        yield self.game_record_content
                    with TabPane("4.选择收货地址"):
                        yield self.address_content
                    with TabPane("5.完成添加"):
                        yield self.finish_content

            with TabPane("✏️管理计划"):
                yield self.manager_content
