# 米游社商品抢兑工具

米游社米游币可兑换的商品通常份数很少，担心抢不到的话可以使用这个脚本，可设置多个商品，一个抢不到还可以抢别的。

建议同时自己也用手机操作去抢，以免脚本出问题。
* * *
**· 第1⃣️步 配置`config.ini`文件，包含以下参数：**

**[Config]**

  `Cookie` 用户Cookies数据，可抓包获取  
  `Time` 商品兑换活动开始时间（按照24小时制 时:分:秒 格式）  
  `Address_ID` 送货地址ID，可抓包获取
  > [`Address_ID` 获取方法](./Docs/Address_ID.md)
  
  `Good_ID` 商品ID列表，可抓包获取（用逗号 , 分隔）

**[Preference]**

  `Check_Network` 是否自动检测网络连接情况（是: 填入 1, 否: 填入 0）(ping api.mihoyo.com)  
  `Check_Time` 每隔多久检查一次网络连接情况（单位 秒）  
  `Stop_Check` 距离开始兑换还剩多久停止检查网络（单位 秒）
* * *
**· 第2⃣️步 运行`main.py`或运行[已经编译好的程序](https://github.com/Ljzd-PRO/Mys_Goods_Tool/releases)**

**可前往`./logs/mys_goods_tool.log`查看日志**
