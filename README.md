<div>
  <img alt="Mys_Goods_Tool 预览" src="https://user-images.githubusercontent.com/63289359/235797444-21a86294-609e-4c7a-9d7d-5d3683fe6ab2.png" width="45%" />
  <img alt="Mys_Goods_Tool 预览2" src="https://user-images.githubusercontent.com/63289359/235799237-3039c3e0-8fdb-4c12-957b-afb50f34625c.png" width="45%" />
</div>

# 米游社商品兑换工具

<div>
  <img alt="CodeFactor" src="https://www.codefactor.io/repository/github/ljzd-pro/mys_goods_tool/badge?style=for-the-badge">
  <img alt="最新发行版" src="https://img.shields.io/github/v/release/Ljzd-PRO/Mys_Goods_Tool?logo=python&style=for-the-badge">
  <img alt="最后提交" src="https://img.shields.io/github/last-commit/Ljzd-PRO/Mys_Goods_Tool?style=for-the-badge">
  <img alt="代码行数" src="https://img.shields.io/tokei/lines/github/Ljzd-PRO/Mys_Goods_Tool?style=for-the-badge">
  <img alt="构建结果" src="https://img.shields.io/github/actions/workflow/status/Ljzd-PRO/Mys_Goods_Tool/build-v2.yml?event=pull_request&style=for-the-badge">
  <img alt="Python版本兼容性测试" src="https://img.shields.io/github/actions/workflow/status/Ljzd-PRO/Mys_Goods_Tool/python-package.yml?event=pull_request&label=Versions%20Test&style=for-the-badge">
</div>

### 更新说明

v2.1.0-beta.1

- 兑换请求Headers增加与修改了 `Referer`, `x-rpc-device_fp`, `x-rpc-verify_key`, `Origin` 等字段，可能修复兑换失败的问题
- 修复登陆时因为连接断开（client has been closed）而导致登陆失败的问题
- 防止因配置文件中默认存在 `device_config`, `salt_config` 而导致更新后默认配置被原配置覆盖的问题
- 若需要修改 `device_config` 配置，修改后还设置用户数据文件中 `preference.override_device_and_salt` 为 `true` 以覆盖默认值
- 修复Unix下即使安装了 uvloop 也找不到，无法应用的问题

## 功能和特性

- [x] 使用 [Textual](https://github.com/Textualize/textual) 终端图形界面库，支持 Windows / Linux / macOS 甚至可能是移动端SSH客户端
- [x] 短信验证码登录（只需接收一次验证码）
- [x] 内置人机验证页面，无需前往官网验证
- [x] 多账号支持
- [x] 支持米游社所有分区的商品兑换

### 预览图

<details>
  <summary>短信验证登录</summary>
  <img src="https://user-images.githubusercontent.com/63289359/235790425-7c502a69-baac-4ced-ba07-d068a88a7ae9.png" alt="短信验证登录页面" />
  <img src="https://user-images.githubusercontent.com/63289359/235790979-85954be8-023f-47e0-bb69-bb16385905d4.png" alt="人机验证页面" />
</details>

<details>
  <summary>管理兑换计划</summary>
  <img src="https://user-images.githubusercontent.com/63289359/235791200-d1a7c8f0-9a9a-4fcc-91bf-69fe397e6420.png" alt="选择目标商品页面" />
  <img src="https://user-images.githubusercontent.com/63289359/235791332-3d8ea836-7d0b-4dbf-b643-81c65eaa5082.png" alt="确认添加计划页面" />
  <img src="https://user-images.githubusercontent.com/63289359/235791435-69edf6f7-9abf-4c81-8da4-44a486c6d362.png" alt="管理计划页面" />
</details>

<details>
  <summary>进入兑换模式</summary>
  <img src="https://user-images.githubusercontent.com/63289359/235791620-bf32692d-a521-49b3-bf2a-23d7012b6fff.png" alt="兑换模式页面" />
</details>

## 使用说明

参考 [🛠️ 下载安装](https://github.com/Ljzd-PRO/Mys_Goods_Tool/wiki/Installation)

## 常见问题

参考 [❓ 常见问题](https://github.com/Ljzd-PRO/Mys_Goods_Tool/wiki/Troubleshooting)

## 代码结构

参考 [📃 代码结构](https://github.com/Ljzd-PRO/Mys_Goods_Tool/wiki/Source-Structure)

## 其他

- [**🔗完整说明文档**](https://github.com/Ljzd-PRO/Mys_Goods_Tool/wiki)

- 仅供学习时参考

- 相似项目推荐:  \
  **mysTool - 米游社辅助工具插件**  \
  简介：NoneBot2 插件 | 米游社工具-每日米游币任务、游戏签到、商品兑换、免抓包登录、原神树脂提醒  \
  🔗 https://github.com/Ljzd-PRO/nonebot-plugin-mystool

- [🔗Bug 反馈](https://github.com/Ljzd-PRO/Mys_Goods_Tool/issues)  
- 如果你知道如何修复一些Bug和新增功能，也欢迎提交你的修订代码 [🔗Pull requests](https://github.com/Ljzd-PRO/Mys_Goods_Tool/pulls)
