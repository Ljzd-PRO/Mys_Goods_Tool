# 米游社商品兑换工具
<div align="left">
  <a href="https://www.codefactor.io/repository/github/ljzd-pro/mys_goods_tool" target="_blank">
    <img alt="CodeFactor" src="https://www.codefactor.io/repository/github/ljzd-pro/mys_goods_tool/badge?style=for-the-badge">
  </a>
  <a href="https://github.com/Ljzd-PRO/Mys_Goods_Tool/releases/latest" target="_blank">
    <img alt="最新发行版" src="https://img.shields.io/github/v/release/Ljzd-PRO/Mys_Goods_Tool?logo=python&style=for-the-badge">
  </a>
  <a href="https://github.com/Ljzd-PRO/Mys_Goods_Tool/commits/" target="_blank">
    <img alt="最后提交" src="https://img.shields.io/github/last-commit/Ljzd-PRO/Mys_Goods_Tool?style=for-the-badge">
  </a>
  <a href="https://github.com/Ljzd-PRO/Mys_Goods_Tool/actions/workflows/codeql-analysis.yml" target="_blank">
    <img alt="GitHub CodeQL 代码检查" src="https://img.shields.io/github/workflow/status/Ljzd-PRO/Mys_Goods_Tool/CodeQL?logo=github&style=for-the-badge">
  </a>
</div>

**🎉 更新：增加支持自动分析 HttpCanary 的抓包数据([🔗v1.2.2](https://github.com/Ljzd-PRO/Mys_Goods_Tool/releases/tag/v1.2.2))**

**🎉 iOS iSH ([🔗AppStore](https://apps.apple.com/us/app/ish-shell/id1436902243)｜[🔗GitHub](https://github.com/ish-app/ish)) 可运行，[🔗release](https://github.com/Ljzd-PRO/Mys_Goods_Tool/releases) 有已经打包好的**

米游社米游币可兑换的商品通常份数很少，担心抢不到的话可以使用这个脚本，可设置多个商品。

建议同时自己也用手机操作去抢，以免脚本出问题。

## 使用说明

### 第1⃣️步 配置`config.ini`文件，包含以下参数

**[Config]**
|  参数   | 说明  |
|  ----  | ----  |
| Cookie | 用户Cookies数据。`tool.py`工具可以从抓包数据中筛选出Cookies信息 |
| stoken | Cookies中的`stoken`项。可选，如果要兑换游戏内物品则需要该信息 |
| Time | 商品兑换活动开始时间（按照 `2022-1-1 00:00:00` 格式） |
| Address_ID | 送货地址ID。可用 `tool.py` 信息查询工具进行查询（附：[🔗`Address_ID` 手动抓包获取方法](./Docs/Address_ID.md)） |
| Good_ID | 商品ID列表。可用 `tool.py` 信息查询工具进行查询（用逗号 , 分隔） |
| UID | 游戏UID。可选，如果要兑换游戏内物品则需要填写，只能填写一个UID。 |

**[Preference]**
|  参数   | 说明  |
|  ----  | ----  |
| Check_Network | 是否自动检测网络连接情况（是: 填入 1, 否: 填入 0）(`ping api-takumi.mihoyo.com`) |
| Check_Time | 每隔多久检查一次网络连接情况（单位 秒） |
| Stop_Check | 距离开始兑换还剩多久停止检查网络（单位 秒） |

**示例**
```ini
[Config]
cookie = "ltuid=123456789; login_ticket=abcDEFijkLMN; account_id=123456789; ltoken=DEFijkLMNabc; cookie_token=ijkLMNabcDEF; stoken=LMNabcDEFijk;"
stoken = LMNabcDEFijk
time = 2022-6-8 19:00:00
address_id = 13911
good_id = 2022053111713, 2022053111397
uid = 987654321

[Preference]
check_network = 1
check_time = 10
stop_check = 30
```

### 第2⃣️步 运行`main.py`或运行[🔗已经编译好的程序](https://github.com/Ljzd-PRO/Mys_Goods_Tool/releases)

**可前往`./logs/mys_goods_tool.log`查看日志**

## 其他
本项目已开启[🔗Github Actions](https://github.com/Ljzd-PRO/Mys_Goods_Tool/actions)。  
欢迎[🔗指出Bug](https://github.com/Ljzd-PRO/Mys_Goods_Tool/issues)和[🔗贡献代码](https://github.com/Ljzd-PRO/Mys_Goods_Tool/pulls)👏

开发版分支：[🔗dev](https://github.com/Ljzd-PRO/Mys_Goods_Tool/tree/dev/)
