# Mys_Goods_Tool 米游社商品兑换工具
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

### 更新说明
v2.0.0 开始的包含了图形化的小工具是基本上重做了，所以刚发布这段时间测试可能不太够，可能不太稳定。

## 功能和特性
- [x] 使用 Textual 终端图形界面库，支持 Windows / Linux / macOS 甚至可能是移动端SSH客户端
- [x] 短信验证码登录（只需接收一次验证码）
- [x] 内置人机验证页面，无需前往官网验证
- [x] 多账号支持
- [x] 支持米游社所有分区的商品兑换

### TODO
- [ ] 支持在图形界面中编辑偏好设置
- [ ] 密码登录


## 使用说明

### 1. 下载安装
有两种方案，配置 Python 环境并从 PyPI 安装包 或者 直接下载可执行文件。

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
默认配置下基本上可以正常使用，如果需要修改配置，可以参考 [`mys_goods_tool/user_data.py`]() 进行配置。

默认配置文件路径为 `./user_data.json`，可以通过 `-c` 或 `--conf` 参数指定配置文件路径。

## 其他
- 仅供学习时参考

- 相似项目推荐:  \
**mysTool - 米游社辅助工具插件**  \
简介：NoneBot2 插件 | 米游社工具-每日米游币任务、游戏签到、商品兑换、免抓包登录、原神树脂提醒  \
🔗 https://github.com/Ljzd-PRO/nonebot-plugin-mystool

- 本项目已开启[🔗Github Actions](https://github.com/Ljzd-PRO/Mys_Goods_Tool/actions)。
欢迎[🔗指出Bug](https://github.com/Ljzd-PRO/Mys_Goods_Tool/issues)和[🔗贡献代码](https://github.com/Ljzd-PRO/Mys_Goods_Tool/pulls)👏

- 开发版分支：[🔗dev](https://github.com/Ljzd-PRO/Mys_Goods_Tool/tree/dev/)
