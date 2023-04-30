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
    TabbedContent, TabPane, OptionList
)
from textual.widgets._option_list import Option, Separator

from mys_goods_tool.api import get_good_list, get_game_list, get_address
from mys_goods_tool.custom_css import *
from mys_goods_tool.custom_widget import StaticStatus, ControllableButton, LoadingDisplay, \
    DynamicTabbedContent, GameButton
from mys_goods_tool.data_model import Good, GameInfo, Address
from mys_goods_tool.user_data import config as conf, UserAccount

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


class AccountContent(BaseExchangePlan):
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
    empty_data_option = Option("暂无账号数据 请尝试刷新", disabled=True)

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
        yield Horizontal(self.button_select, self.button_refresh, self.button_reset)
        yield self.option_list

    def reset_selected(self, _: Optional[events.Message] = None):
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
        ExchangePlanView.address_content.reset_account()

    async def _on_button_pressed(self, event: ControllableButton.Pressed) -> None:
        if event.button.id == "button-account-select":
            # 按下“保存”按钮时触发的事件

            if self.option_list.highlighted is None:
                self.app.notice("[bold red]请先从列表中选择账号！[/]")
                return

            account_key = self.account_keys[self.option_list.highlighted]
            self.selected = conf.accounts.get(account_key)
            if self.selected is None:
                self.app.notice(f"未找到账号：[bold red]{account_key}[/]")
                return

            # 禁用选择按钮、启用重置按钮、禁用选项列表
            self.button_select.disable()
            self.button_reset.enable()
            self.option_list.disabled = True

            self.text_view.update(f"已选择账户"
                                  f"\n[list]"
                                  f"\n🪪 通信证ID - [bold green]{account_key}[/]"
                                  f"\n[/list]")
            if conf.accounts[account_key].cookies.is_correct():
                self.app.notice(f"选择的账号：[bold green]{account_key}[/] Cookies完整，可继续")
            else:
                self.app.notice(
                    f"选择的账号：[bold red]{account_key}[/] Cookies不完整，但你仍然可以尝试进行兑换")

            await ExchangePlanView.address_content.update_address()

        elif event.button.id == "button-account-refresh":
            # 按下“刷新”按钮时触发的事件

            self.account_keys = list(conf.accounts.keys())
            self.option_list.clear_options()
            for account in self.account_keys:
                self.option_list.add_option(account)
            if not self.account_keys:
                self.option_list.add_option(self.empty_data_option)
            # 重置已选内容
            self.reset_selected(event)
            self.app.notice("[bold green]已刷新账号列表[/]")

        elif event.button.id == "button-account-reset":
            # 按下“重置”按钮时触发的事件

            self.reset_selected(event)
            self.app.notice("已重置账号选择")


class GoodsContent(BaseExchangePlan):
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
    selected_tuple: Optional[Tuple[GameInfo, int]] = None
    """已选择的商品位置"""

    empty_data_option = Option("暂无商品数据，可能是目前没有限时兑换的商品，可尝试刷新", disabled=True)
    """空的商品选项列表"""
    tabbed_content = DynamicTabbedContent()

    class GoodsDictValue:
        """
        游戏频道对应的商品数据相关
        """

        def __init__(self,
                     game_info: GameInfo,
                     button_select: Optional[GameButton] = None,
                     tap_pane: Optional[TabPane] = None,
                     good_list: List[Good] = None,
                     ):
            """
            :param game_info: 商品频道数据
            :param tap_pane: 频道对应的 `TabPane` 标签页
            :param good_list: 商品数据
            :param button_select: 选择商品的按钮
            """
            self.game_info = game_info
            """商品频道数据"""
            self.button_select = button_select or GameButton(
                "💾 确定",
                id=f"button-goods-select-{game_info.id}",
                disabled=True,
                game=game_info)
            """选择商品的按钮"""
            self.option_list = OptionList(GoodsContent.empty_data_option, disabled=True)
            """商品的选项列表"""
            self.tap_pane = tap_pane or TabPane(game_info.name, Horizontal(self.button_select, self.option_list))
            """频道对应的 `TabPane` 标签页"""
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

        for goods_data in self.good_dict.values():
            good_list_status, good_list = await get_good_list(goods_data.game_info.op_name)
            good_list = list(filter(lambda x: x.is_time_limited() and not x.is_time_end(), good_list))

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
                self.app.notice(f"[bold red]获取频道 [bold red]{goods_data.game_info.name}[/] 的商品数据失败！[/]")
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

        # 更新商品频道列表
        game_list_status, game_list = await get_game_list()
        if game_list_status:
            for game in game_list:
                if game.id not in self.good_dict:
                    # 如果没有商品频道对应值，则进行创建
                    goods_data = self.GoodsDictValue(game)
                    self.good_dict.setdefault(game.id, goods_data)
                    await self.tabbed_content.append(goods_data.tap_pane)

            # 更新每个频道的商品数据
            await self.update_goods()
        else:
            self.text_view.update("[bold red]⚠ 获取商品频道列表失败，可尝试刷新[/]")
            self.app.notice("[bold red]获取商品频道列表失败！[/]")
            # TODO 待补充各种错误情况

        # 进度条、刷新按钮
        self.button_refresh.enable()
        self.loading.hide()

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

    async def _on_button_pressed(self, event: GameButton.Pressed) -> None:
        if event.button.id.startswith("button-goods-select-"):
            # 按下“保存”按钮时触发的事件

            game = event.button.game
            if not game:
                self.app.notice("[bold red]未找到对应的频道数据或频道不可用[/]")
                return
            option_list = self.good_dict[game.id].option_list
            selected_index = option_list.highlighted
            if selected_index is None:
                self.app.notice("[bold red]未选择商品！[/]")
                return
            good_dict_value = self.good_dict.get(game.id)
            if not good_dict_value:
                self.app.notice("[bold red]未找到对应的频道[/]")
                return

            good = good_dict_value.good_list[selected_index]
            GoodsContent.selected_tuple = game, selected_index
            self.selected = good

            # 启用重置按钮
            self.button_reset.enable()

            # 禁用其他频道的选择按钮
            # 禁用其他频道的选项列表
            for value in self.good_dict.values():
                value.button_select.disable()
                value.option_list.disabled = True

            # 如果是虚拟商品，则不需要设置收货地址，并更改地址视图
            # 如果是实物商品，则需要设置收货地址，并更改地址视图
            AddressContent.check_good_type()

            self.text_view.update(f"已选择商品："
                                  f"\n[list]"
                                  f"\n🗂️ 商品频道：[bold green]{game.name}[/]"
                                  f"\n📌 名称：[bold green]{good.general_name}[/]"
                                  f"\n💰 价格：[bold green]{good.price}[/] 米游币"
                                  f"\n📦 库存：[bold green]{good.stoke_text}[/] 件"
                                  f"\n📅 兑换时间：[bold green]{good.time_text}[/]"
                                  f"\n📌 商品ID：[bold green]{good.goods_id}[/]"
                                  f"\n[/list]")

        elif event.button.id == "button-goods-refresh":
            # 按下“刷新”按钮时触发的事件

            # 在初次加载时，如果获取商品频道信息失败，则此时重新获取
            if not self.good_dict:
                await self._on_mount(events.Mount())
            await self.update_goods()

        elif event.button.id == "button-goods-reset":
            # 按下“重置”按钮时触发的事件

            self.reset_selected()
            self.app.notice("已重置商品选择")


class AddressContent(BaseExchangePlan):
    """
    收货地址选择组件
    """

    DEFAULT_TEXT = Markdown("- 请选择一个收货地址")
    REQUIRE_ACCOUNT_TEXT = Markdown("- 请先完成账号选择")
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

    async def update_address(self):
        """
        更新收货地址列表
        """
        if AccountContent.selected is None:
            return

        # 进度条、刷新按钮、选项列表
        self.loading.show()
        self.button_refresh.disable()
        self.option_list.disabled = False

        address_status, self.address_list = await get_address(AccountContent._selected)
        if address_status:
            self.option_list.clear_options()
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
            if not self.address_list:
                self.option_list.add_option(self.empty_data_option)
        else:
            self.app.notice(f"[bold red]获取收货地址列表失败！[/]")

        # 进度条、刷新按钮
        self.loading.hide()
        self.button_refresh.enable()

        #  重置已选地址
        self.reset_selected()

        # 检查选项列表是否为空的操作包含在 check_good_type 中
        self.check_good_type()

    def compose(self) -> ComposeResult:
        yield self.text_view
        yield Horizontal(self.button_select, self.button_refresh, self.button_reset, self.loading)
        yield self.option_list

    def reset_account(self):
        """
        重置已选账号
        - 重置已选地址
        - 重置文本内容
        - 禁用所有按钮
        - 禁用选项列表
        - 清空选项列表
        """
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
        cls.check_empty()
        # 程序载入初次刷新商品列表时，重置已选商品并调用check_good_type，此时不需要检查商品类型
        if AccountContent._selected is not None:
            good: Optional[Good] = GoodsContent._selected
            if good is not None and good.is_visual:
                cls.text_view.update(cls.UNNEEDED_TEXT)
                cls.option_list.disabled = True
                cls.button_select.disable()
                cls.button_refresh.disable()
            elif cls._selected is None:
                cls.text_view.update(cls.DEFAULT_TEXT)
                cls.option_list.disabled = False
                cls.button_select.enable()
                cls.button_refresh.enable()
            else:
                # 在已选地址不为空的情况下，视图被虚拟商品改变后的情况
                ExchangePlanView.address_content._set_select_view(cls._selected)

    def reset_selected(self):
        """
        重置已选地址
        """
        self.check_empty()
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
                self.app.notice("[bold red]未选择收货地址！[/]")
                return
            if address_index >= len(self.address_list):
                self.app.notice("[bold red]无法找到收货地址！[/]")
                return
            address = self.address_list[address_index]
            self.selected = address

            self._set_select_view(address)

        elif event.button.id == "button-address-refresh":
            # 按下“刷新”按钮时触发的事件

            await self.update_address()

        elif event.button.id == "button-address-reset":
            # 按下“重置”按钮时触发的事件

            self.reset_selected()
            self.app.notice("已重置收获地址选择")


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
                good: Optional[Good] = GoodsContent._selected
                if good is not None and not good.is_visual:
                    self.address_detail = self.DEFAULT_TEXT
            elif content_type == GoodsContent:
                self.goods_name = self.DEFAULT_TEXT
                self.goods_time = self.DEFAULT_TEXT
                # 把“无需设置”还原为“待选取”
                self.address_detail = self.DEFAULT_TEXT
        elif isinstance(value, UserAccount):
            self.account_text = finished_style_text(value.bbs_uid)
        elif isinstance(value, Address):
            self.address_detail = finished_style_text(value.addr_ext)
        elif isinstance(value, Good):
            self.goods_name = finished_style_text(value.general_name)
            self.goods_time = finished_style_text(value.time_text)
            if value.is_visual:
                self.address_detail = self.UNNEEDED_TEXT
        self.refresh()

    def render(self) -> RenderableType:
        return f"请确认兑换计划信息：" \
               f"\n[list]" \
               f"\n👓 账号 - {self.account_text}" \
               f"\n📮 详细地址 - {self.address_detail}" \
               f"\n📦 商品名称 - {self.goods_name}" \
               f"\n📅 兑换时间 - {self.goods_time}" \
               f"\n[/list]"


class FinishContent(ExchangePlanContent):
    check_out_text = CheckOutText()
    button_submit = ControllableButton("保存兑换计划", variant="success", id="button-finish-submit")
    button_test = ControllableButton("测试兑换", id="button-finish-test")
    loading = LoadingDisplay()

    def compose(self) -> ComposeResult:
        yield self.check_out_text
        yield Horizontal(self.button_submit, self.button_test, self.loading)


class ExchangePlanView(Container):
    """
    添加兑换计划 - 界面
    """
    account_content = AccountContent()
    goods_content = GoodsContent()
    address_content = AddressContent()
    finish_content = FinishContent()

    def compose(self) -> ComposeResult:
        with TabbedContent():
            with TabPane("➕添加计划", id="tab-adding"):
                with TabbedContent():
                    with TabPane("1.选择账号", id="tab-adding-account"):
                        yield self.account_content
                    with TabPane("2.选择目标商品", id="tab-adding-goods"):
                        yield self.goods_content
                    with TabPane("3.选择收货地址", id="tab-adding-address"):
                        yield self.address_content
                    with TabPane("4.完成添加", id="tab-adding-ending"):
                        yield self.finish_content

            with TabPane("✏️管理计划", id="tab-managing"):
                yield Container()
