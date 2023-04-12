import sys

from .tui import TuiApp

pyperclip_import_result = True
try:
    import pyperclip
except ImportError:
    print("pyperclip 剪切板模块导入失败，程序将不会自动复制文本到剪切板...")
    pyperclip_import_result = False

VERSION = "v2.0.0-dev"
"""程序当前版本"""
NTP_MAX_RETRY_TIMES = 5
"""网络时间校对失败后最多重试次数"""


def print_help():
    print(f"""
Mys_Goods_Tool
使用说明：
{sys.argv[0]} [选项(可选)] [配置文件路径(可选)]
选项：
    -h 显示此帮助信息
    -m <参数> 指定运行模式
        guide 指引模式（默认）
        exchange 兑换模式，等待到达兑换时间并自动兑换
        exchange-simple 兑换模式，无TUI界面，仅输出日志文本
        test 测试模式，测试配置文件是否正确以及是否可能可以成功兑换
例如：
    ./{sys.argv[0]} -m exchange ./workplace/config.json
        通过该命令运行本程序，将读取 ./workplace/config.json 配置文件，并直接进入兑换模式，等待到达兑换时间并执行兑换。
    ./{sys.argv[0]} -m test
        通过该命令运行本程序，将读取程序目录下的配置文件config.json，检查配置文件格式是否正确，并直接尝试兑换以测试是否为未来的兑换计划做好准备。
    ./{sys.argv[0]}
        通过该命令运行本程序或直接双击打开程序，将读取程序目录下的配置文件config.json，并提供添加兑换计划、查看兑换计划、删除兑换计划、设置收货地址等功能。
        """.strip())


def guide_mode():
    app = TuiApp()
    app.run()


def main():
    if len(sys.argv) == 1:
        guide_mode()
    elif sys.argv[1] == "-h":
        print_help()
    elif sys.argv[1] == "-m":
        if sys.argv[2] == "guide":
            ...
        elif sys.argv[2] == "exchange":
            ...
        elif sys.argv[2] == "test":
            ...
        else:
            print_help()


if __name__ == "__main__":
    main()
