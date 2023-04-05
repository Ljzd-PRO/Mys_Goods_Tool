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
