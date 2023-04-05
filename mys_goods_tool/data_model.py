from typing import Optional, Tuple, Literal, Dict, NamedTuple

from pydantic import BaseModel


class Good(BaseModel):
    """
    商品数据
    """
    type: int
    """为 1 时商品只有在指定时间开放兑换；为 0 时商品任何时间均可兑换"""
    next_time: Optional[int]
    """为 0 表示任何时间均可兑换或兑换已结束"""
    status: Optional[str]
    sale_start_time: Optional[str]
    time_by_detail: Optional[int]
    next_num: Optional[int]
    account_exchange_num: int
    """已经兑换次数"""
    account_cycle_limit: int
    """最多可兑换次数"""
    account_cycle_type: Literal["forever", "month"]
    """限购类型"""
    game_biz: Optional[str]
    """商品对应的游戏区服"""
    game: Optional[str]
    """商品对应的游戏"""
    unlimit: Optional[bool]
    """是否为不限量商品"""

    # 以下为实际会用到的属性

    name: str
    """商品名称"""

    goods_id: str
    """商品ID(Good_ID)"""

    price: int
    """商品价格"""

    icon: str
    """商品图片链接"""

    @property
    def time(self):
        """
        兑换时间
        如果返回`None`，说明获取商品兑换时间失败
        """
        # "next_time" 为 0 表示任何时间均可兑换或兑换已结束
        # "type" 为 1 时商品只有在指定时间开放兑换；为 0 时商品任何时间均可兑换
        if self.type != 1 and self.next_time == 0:
            return None
        elif self.status != "not_in_sell":
            return self.next_time
        elif not self.sale_start_time:
            return int(self.sale_start_time)
        else:
            return self.time_by_detail

    @property
    def num(self):
        """
        库存
        如果返回`None`，说明获取商品库存失败
        """
        if self.type != 1 and self.next_num == 0:
            return None
        else:
            return self.next_num

    @property
    def limit(self):
        """
        限购，返回元组 (已经兑换次数, 最多可兑换次数, 限购类型)
        """
        return (self.account_exchange_num,
                self.account_cycle_limit, self.account_cycle_type)

    @property
    def is_visual(self) -> bool:
        """
        是否为虚拟商品
        """
        if self.type == 2:
            return True
        else:
            return False


class GameRecord(BaseModel):
    """
    用户游戏数据
    """
    region_name: str
    """服务器区名"""

    game_id: int
    """游戏ID"""

    level: int
    """用户游戏等级"""

    region: str
    """服务器区号"""

    game_role_id: str
    """用户游戏UID"""

    nickname: str
    """用户游戏昵称"""


class GameInfo(BaseModel):
    """
    游戏信息数据
    """
    ABBR_TO_ID: Dict[int, Tuple[str, str]] = {}
    '''
    游戏ID(game_id)与缩写和全称的对应关系
    >>> {游戏ID, (缩写, 全称)}
    '''
    id: int
    """游戏ID"""

    app_icon: str
    """游戏App图标链接(大)"""

    op_name: str
    """游戏代号(英文数字, 例如hk4e)"""

    en_name: str
    """游戏代号2(英文数字, 例如ys)"""

    icon: str
    """游戏图标链接(圆形, 小)"""

    name: str
    """游戏名称"""


class Address(BaseModel):
    """
    地址数据
    """
    connect_areacode: str
    """电话区号"""
    connect_mobile: str
    """电话号码"""

    # 以下为实际会用到的属性

    province_name: str
    """省"""

    city_name: str
    """市"""

    county_name: str
    """区/县"""

    addr_ext: str
    """详细地址"""

    connect_name: str
    """收货人姓名"""

    id: str
    """地址ID"""

    @property
    def phone(self) -> str:
        """
        联系电话(包含区号)
        """
        return self.connect_areacode + " " + self.connect_mobile


class MmtData(BaseModel):
    """
    短信验证码-人机验证任务申请-返回数据
    """
    challenge: str
    gt: str
    mmt_key: str
    new_captcha: bool


class BaseApiStatus(BaseModel):
    """
    API返回结果基类
    """
    success = False
    """成功"""
    network_error = False
    """连接失败"""
    incorrect_return = False
    """服务器返回数据不正确"""
    login_failed = False
    """登录失败"""

    def __bool__(self):
        if self.success:
            return True
        else:
            return False


class CreateMobileCaptchaStatus(BaseApiStatus):
    """
    发送短信验证码 返回结果
    """
    incorrect_geetest = False
    """人机验证结果数据无效"""


class GetCookieStatus(BaseApiStatus):
    """
    获取Cookie 返回结果
    """
    incorrect_captcha = False
    """验证码错误"""
    missing_login_ticket = False
    """Cookies 缺少 login_ticket"""
    missing_bbs_uid = False
    """Cookies 缺少 bbs_uid (stuid, ltuid, ...)"""
    missing_cookie_token = False
    """Cookies 缺少 cookie_token"""
    missing_stoken = False
    """Cookies 缺少 stoken"""


class GetGoodDetailStatus(BaseApiStatus):
    """
    获取商品详细信息 返回结果
    """
    good_not_existed = False


class ExchangeStatus(BaseApiStatus):
    """
    兑换操作 返回结果
    """
    missing_stoken = False
    """商品为游戏内物品，但 Cookies 缺少 stoken"""
    missing_mid = False
    """商品为游戏内物品，但 stoken 为 'v2' 类型同时 Cookies 缺少 mid"""
    missing_address = False
    """商品为实体物品，但未配置收货地址"""
    missing_game_uid = False
    """商品为游戏内物品，但未配置对应游戏的账号UID"""
    unsupported_game = False
    """暂不支持兑换对应分区/游戏的商品"""
    failed_getting_game_record = False
    """获取用户 GameRecord 失败"""
    init_required = False
    """未进行兑换任务初始化"""
    account_not_found = False
    """账号不存在"""


GeetestResult = NamedTuple("GeetestResult", validate=str, seccode=str)
"""人机验证结果数据"""

ExchangeResult = NamedTuple("ExchangeResult", result=bool, return_data=dict)
"""兑换结果数据"""
