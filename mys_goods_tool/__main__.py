from argparse import ArgumentParser
from typing import Optional

from textual.app import App

import mys_goods_tool.user_data
from mys_goods_tool.user_data import load_config

VERSION = "v2.0.0-dev"
"""程序当前版本"""


def main(textual_app: Optional[App]):
    arg = arg_parser.parse_args()

    if arg.conf is not None:
        mys_goods_tool.user_data.CONFIG_PATH = arg.conf
        mys_goods_tool.user_data.config = load_config()
    if arg.mode == "guide":
        textual_app.run()
    elif arg.mode == "exchange":
        # TODO 兑换模式
        ...
    elif arg.mode == "exchange-simple":
        # TODO 兑换模式 simple
        ...


USAGE = """
Mys_Goods_Tool
使用说明：
%(prog)s [-m <运行模式>] [-c <用户数据文件路径>]
选项：
    -h, --help 显示此帮助信息
    -m, --mode <参数> 指定运行模式
        guide 指引模式（默认）
        exchange 兑换模式，等待到达兑换时间并自动兑换
        exchange-simple 兑换模式，无TUI界面，仅输出日志文本
    -c, --conf <参数> 指定用户数据文件路径
例如：
    %(prog)s -m exchange -c ./workplace/user_data.json
        通过该命令运行本程序，将读取 ./workplace/user_data.json 用户数据文件，并直接进入兑换模式，等待到达兑换时间并执行兑换。
    %(prog)s -m test
        通过该命令运行本程序，将读取程序目录下的用户数据文件user_data.json，检查用户数据文件格式是否正确，并直接尝试兑换以测试是否为未来的兑换计划做好准备。
    %(prog)s
        通过该命令运行本程序或直接双击打开程序，将读取程序目录下的用户数据文件user_data.json，并提供添加兑换计划、查看兑换计划、删除兑换计划、设置收货地址等功能。
        """.strip()


class ArgumentParserWithHelp(ArgumentParser):
    def error(self, message):
        self.print_help()
        super().error(message)


arg_parser = ArgumentParserWithHelp(description="Mys_Goods_Tool", usage=USAGE)
arg_parser.add_argument("-m", "--mode", dest="mode", choices=["guide", "exchange", "exchange-simple"],
                        default="guide")
arg_parser.add_argument("-c", "--conf", type=str, dest="conf", default=None)

TEXTUAL_DEBUG = False

if __name__ == "__main__":
    app: Optional[App] = None
    if TEXTUAL_DEBUG:
        from .tui import TuiApp

        app = TuiApp()
    main(app)
