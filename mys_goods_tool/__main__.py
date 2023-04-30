from argparse import ArgumentParser

import mys_goods_tool.user_data
from mys_goods_tool.user_data import load_config
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


def guide_mode(textual_app: TuiApp):
    textual_app.run()


def main(textual_app: TuiApp):
    arg = arg_parser.parse_args()

    if arg.conf is not None:
        mys_goods_tool.user_data.CONFIG_PATH = arg.conf
        mys_goods_tool.user_data.config = load_config()
    if arg.mode == "guide":
        guide_mode(textual_app)
    elif arg.mode == "exchange":
        # TODO 兑换模式
        ...
    elif arg.mode == "exchange-simple":
        # TODO 兑换模式 simple
        ...
    elif arg.mode == "test":
        # TODO 测试模式
        ...


USAGE = """
Mys_Goods_Tool
使用说明：
%(prog)s [-m <运行模式>] [-c <配置文件路径>]
选项：
    -h, --help 显示此帮助信息
    -m, --mode <参数> 指定运行模式
        guide 指引模式（默认）
        exchange 兑换模式，等待到达兑换时间并自动兑换
        exchange-simple 兑换模式，无TUI界面，仅输出日志文本
        test 测试模式，测试配置文件是否正确以及是否可能可以成功兑换
    -c, --conf <参数> 指定配置文件路径
例如：
    %(prog)s -m exchange -c ./workplace/config.json
        通过该命令运行本程序，将读取 ./workplace/config.json 配置文件，并直接进入兑换模式，等待到达兑换时间并执行兑换。
    %(prog)s -m test
        通过该命令运行本程序，将读取程序目录下的配置文件config.json，检查配置文件格式是否正确，并直接尝试兑换以测试是否为未来的兑换计划做好准备。
    %(prog)s
        通过该命令运行本程序或直接双击打开程序，将读取程序目录下的配置文件config.json，并提供添加兑换计划、查看兑换计划、删除兑换计划、设置收货地址等功能。
        """.strip()


class ArgumentParserWithHelp(ArgumentParser):
    def error(self, message):
        self.print_help()
        super().error(message)


arg_parser = ArgumentParserWithHelp(description="Mys_Goods_Tool", usage=USAGE)
arg_parser.add_argument("-m", "--mode", dest="mode", choices=["guide", "exchange", "exchange-simple", "test"],
                        default="guide")
arg_parser.add_argument("-c", "--conf", type=str, dest="conf", default=None)

if __name__ == "__main__":
    app = TuiApp()
    main(app)
