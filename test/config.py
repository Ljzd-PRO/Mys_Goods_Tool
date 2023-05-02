from mys_goods_tool.user_data import config as conf, UserAccount

ACCOUNTS_DICT = {
    "123456": {
            "phone_number": "",
            "cookies": {},
            "device_id_ios": "",
            "device_id_android": ""
    }
}
"""测试用的账号数据"""

ACCOUNT = "123456"
"""要选用的账号"""

accounts_model = {}

for key in ACCOUNTS_DICT:
    model = UserAccount.parse_obj(ACCOUNTS_DICT[key])
    accounts_model.setdefault(key, model)

test_config = conf.copy()
test_config.accounts = accounts_model
"""完成测试账号添加后的配置文件"""
