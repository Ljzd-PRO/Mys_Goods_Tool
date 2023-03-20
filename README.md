# 米游社商品兑换工具
<div>
  <a href="https://www.codefactor.io/repository/github/ljzd-pro/mys_goods_tool" target="_blank">
    <img alt="CodeFactor" src="https://www.codefactor.io/repository/github/ljzd-pro/mys_goods_tool/badge?style=for-the-badge">
  </a>
  <a href="https://github.com/Ljzd-PRO/Mys_Goods_Tool/releases/latest" target="_blank">
    <img alt="最新发行版" src="https://img.shields.io/github/v/release/Ljzd-PRO/Mys_Goods_Tool?logo=python&style=for-the-badge">
  </a>
  <a href="https://github.com/Ljzd-PRO/Mys_Goods_Tool/commits/" target="_blank">
    <img alt="最后提交" src="https://img.shields.io/github/last-commit/Ljzd-PRO/Mys_Goods_Tool?style=for-the-badge">
  </a>
</div>

### 🎉 更新 [🔗v1.4.4](https://github.com/Ljzd-PRO/Mys_Goods_Tool/releases/tag/v1.4.4)

修复获取**米游社**uid失败导致检查游戏账户失败的问题  
如报错：

```
2023-01-18 15:46:13  DEBUG  checkGame_response: {"data":null,"message":"Invalid uid","retcode":-1}
```

**🎉 iOS
iSH ([🔗AppStore](https://apps.apple.com/us/app/ish-shell/id1436902243)｜[🔗GitHub](https://github.com/ish-app/ish))
可运行，[🔗release](https://github.com/Ljzd-PRO/Mys_Goods_Tool/releases) 有已经打包好的**
*（附：[🔗iOS iSH 运行本程序的方法](./Docs/iSH.md)）*

米游社米游币可兑换的商品通常份数很少，担心抢不到的话可以使用这个脚本，可设置多个商品。

建议同时自己也用手机操作去抢，以免脚本出问题。

## 使用说明

### 第1⃣️步 配置`config.ini`文件，包含以下参数

**[Config]**
|  参数   | 说明  |
|  ----  | ----  |
| Cookie | **用户Cookies数据**<br>可通过`tool.py`工具直接获取（示例中两端的引号可有可无）<br>**兑换游戏内物品时 `stoken` 为必需项**<br>*（附：[🔗`tool` 工具使用说明](./Docs/tool.md)）* |
| Time | **商品兑换活动开始时间**<br>（按照 `2022-1-1 00:00:00` 格式） |
| Address_ID | **送货地址ID**<br>可用 `tool.py` 信息查询工具进行查询<br>*（附：[🔗`Address_ID` ~~手动抓包~~获取方法](./Docs/Address_ID.md)）* |
| Good_ID | **要兑换的商品ID列表**<br>所有兑换任务会同时执行。可用 `tool.py` 信息查询工具进行查询（用逗号 , 分隔）<br>*（附：[🔗`tool` 工具使用说明](./Docs/tool.md)）* |
| UID | **游戏UID**<br>可选，如果要兑换游戏内物品则需要填写，只能填写一个UID。 |

**[Preference]**
|  参数   | 说明  |
|  ----  | ----  |
| Check_Network | 是否自动检测网络连接情况<br>（是: 填入 1, 否: 填入 0）(`ping api-takumi.mihoyo.com`) |
| Check_Time | 每隔多久检查一次网络连接情况<br>（单位 秒） |
| Stop_Check | 距离开始兑换还剩多久停止检查网络<br>（单位 秒） |
| Thread | 每个商品使用多少线程进行兑换<br>（避免出现卡在单个兑换请求的现象，如果目标可兑换数量超过一个建议线程为1） |

#### **更多说明: [🔗config.ini](./config.ini)**
#### **示例**
```ini
[Config]
cookie = "ltuid=123456789;login_ticket=abcDEFijkLMN;account_id=123456789;ltoken=DEFijkLMNabc;cookie_token=ijkLMNabcDEF;stoken=LMNabcDEFijk;"
time = 2022-6-8 19:00:00
address_id = 13911
good_id = 2022053111713, 2022053111397
uid = 987654321

[Preference]
check_network = 1
check_time = 10
stop_check = 30
thread = 3
```

### 第2⃣️步 运行`main.py`或运行[🔗已经编译好的程序](https://github.com/Ljzd-PRO/Mys_Goods_Tool/releases)

- 在兑换开始之前运行主程序。

- 建议先把兑换时间设定为当前时间往后的一两分钟，测试一下是否能正常兑换，如果返回未到时间或者库存不足就基本没有问题。

- **可前往`./logs/mys_goods_tool.log`查看日志**

## 其他
- 仅供学习时参考

- 相似项目推荐:  \
**mysTool - 米游社辅助工具插件**  \
简介：NoneBot2 插件 | 米游社工具-每日米游币任务、游戏签到、商品兑换、免抓包登录、原神树脂提醒  \
🔗 https://github.com/Ljzd-PRO/nonebot-plugin-mystool

- 本项目已开启[🔗Github Actions](https://github.com/Ljzd-PRO/Mys_Goods_Tool/actions)。
欢迎[🔗指出Bug](https://github.com/Ljzd-PRO/Mys_Goods_Tool/issues)和[🔗贡献代码](https://github.com/Ljzd-PRO/Mys_Goods_Tool/pulls)👏

- 开发版分支：[🔗dev](https://github.com/Ljzd-PRO/Mys_Goods_Tool/tree/dev/)
