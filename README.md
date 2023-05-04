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
v2.0.0 开始的包含了图形化的小工具是基本上重做了，所以刚发布这段时间测试可能不太够，可能不太稳定。

## 功能和特性
- [x] 使用 [Textual](https://github.com/Textualize/textual) 终端图形界面库，支持 Windows / Linux / macOS 甚至可能是移动端SSH客户端
- [x] 短信验证码登录（只需接收一次验证码）
- [x] 内置人机验证页面，无需前往官网验证
- [x] 多账号支持
- [x] 支持米游社所有分区的商品兑换

### TODO
- [ ] 支持在图形界面中编辑偏好设置
- [ ] 密码登录
- [ ] 解决SSH客户端无法跳转人机验证链接的问题

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

### 1. 下载安装
有两种方案，配置 Python 环境并从 PyPI 安装包 **或者** 直接下载可执行文件。

#### 配置 Python 环境并从 PyPI 安装包
1. 配置 Python 环境
2. 进行安装
    ```shell
    pip install mys-goods-tool
    ```
3. 运行
    ```shell
    python -m mys_goods_tool
    ```

#### 直接下载可执行文件
- 前往 [🔗 Releases](https://github.com/Ljzd-PRO/Mys_Goods_Tool/releases) 下载最新版本可执行文件
- 双击打开或在可执行文件目录下运行
    - Windows
        ```shell
        .\Mys_Goods_Tool.exe
        ```
    - Linux / macOS
        ```shell
        chmod +x ./Mys_Goods_Tool
        ./Mys_Goods_Tool
        ```

### 2. 自定义启动参数（可选）
- `%(prog)s` 即为程序路径
    ```shell
    Mys_Goods_Tool
    使用说明:
    %(prog)s [-m <运行模式>] [-c <用户数据文件路径>]
    选项:
        -h, --help 显示此帮助信息
        -m, --mode <参数> 指定运行模式
            guide TUI指引模式 包含登陆绑定 管理兑换计划和开始兑换等功能 默认
            exchange-simple 兑换模式 无TUI界面 仅输出日志文本
        -c, --conf <参数> 指定用户数据文件路径
    例如:
        ./Mys_Goods_Tool -m exchange-simple -c ./workplace/user_data.json
            通过该命令运行本程序 将读取 ./workplace/user_data.json 用户数据文件 并直接进入无TUI界面的兑换模式 等待到达兑换时间并执行兑换
        ./Mys_Goods_Tool
            通过该命令运行本程序或直接双击打开程序 将读取程序目录下的用户数据文件user_data.json 并提供登录绑定 管理兑换计划等功能
    ```

### 3. 偏好设置（可选）
默认配置下基本上可以正常使用，如果需要修改配置，可以参考 [`mys_goods_tool/user_data.py`](https://github.com/Ljzd-PRO/Mys_Goods_Tool/blob/stable/mys_goods_tool/user_data.py) 进行配置。

默认配置文件路径为 `./user_data.json`，可以通过 `-c` 或 `--conf` 参数指定配置文件路径。

默认日志文件路径为 `./logs/mys_goods_tool.log`，可以通过修改配置文件中的偏好设置来指定日志输出路径。

## 兼容性
支持 Python **`3.9`** - **`3.11`**

## 其他
- 仅供学习时参考

- 相似项目推荐:  \
**mysTool - 米游社辅助工具插件**  \
简介：NoneBot2 插件 | 米游社工具-每日米游币任务、游戏签到、商品兑换、免抓包登录、原神树脂提醒  \
🔗 https://github.com/Ljzd-PRO/nonebot-plugin-mystool

- 本项目已开启[🔗Github Actions](https://github.com/Ljzd-PRO/Mys_Goods_Tool/actions)。
欢迎[🔗指出Bug](https://github.com/Ljzd-PRO/Mys_Goods_Tool/issues)和[🔗贡献代码](https://github.com/Ljzd-PRO/Mys_Goods_Tool/pulls)👏

- 开发版分支：[🔗dev](https://github.com/Ljzd-PRO/Mys_Goods_Tool/tree/dev/)
