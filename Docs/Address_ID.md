# 手动获取`Address_ID`的方法
**❕注意：可直接用`tool.py`信息查询工具获取`Address_ID`，免去手动抓包的麻烦。前提是要先配置好`Cookie`**

启动抓包，打开米游社App **我的-设置-通行证账号与安全-管理收货地址** 这个页面，

App会发出一个GET请求，请求URL为`https://api-takumi.mihoyo.com/account/address/list?t=xxxxxxxxxx`，该请求的返回数据中有`id`键，`id`对应的值就是配置文件里的`Address_ID`

> 示例

这是打开页面后App发出的GET请求：
```json
{
  "retcode": 0,
  "message": "OK",
  "data": {
    "list": [
      {
        "id": "12345",
        "connect_name": "小王",
        "connect_areacode": "+86",
        "connect_mobile": "189****9999",
        "country": 1,
        "province": xxxxxx,
        "city": xxxxx,
        "county": xxxxxx,
        "province_name": "某省",
        "city_name": "某市",
        "county_name": "某区",
        "addr_ext": "某路某号",
        "is_default": 0,
        "status": 1
      },
      {
        "id": "67890",
        "connect_name": "小王",
        "connect_areacode": "+86",
        "connect_mobile": "189****9999",
        "country": 1,
        "province": xxxxxx,
        "city": xxxxx,
        "county": xxxxxx,
        "province_name": "某某省",
        "city_name": "某某市",
        "county_name": "某某区",
        "addr_ext": "某某路某某号",
        "is_default": 0,
        "status": 1
      }
    ]
  }
}
```
其中，`12345`和`67890`就是可选用的Address_ID，兑换的周边要寄送到哪个地址配置文件就填哪个。
