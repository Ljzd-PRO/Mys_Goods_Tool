from argparse import ArgumentParser
from typing import Optional

from textual.app import App

import mys_goods_tool.user_data
from mys_goods_tool.exchange_mode import exchange_mode_simple
from mys_goods_tool.user_data import load_config

USAGE = """
Mys_Goods_Tool
使用说明：
%(prog)s [-m <运行模式>] [-c <用户数据文件路径>]
选项：
    -h, --help 显示此帮助信息
    -m, --mode <参数> 指定运行模式
        guide TUI指引模式，包含登陆绑定、管理兑换计划和开始兑换等功能（默认）
        exchange-simple 兑换模式，无TUI界面，仅输出日志文本
    -c, --conf <参数> 指定用户数据文件路径
例如：
    %(prog)s -m exchange-simple -c ./workplace/user_data.json
        通过该命令运行本程序，将读取 ./workplace/user_data.json 用户数据文件，并直接进入无TUI界面的兑换模式，等待到达兑换时间并执行兑换。
    %(prog)s
        通过该命令运行本程序或直接双击打开程序，将读取程序目录下的用户数据文件user_data.json，并提供登录绑定、管理兑换计划等功能。
        """.strip()


class ArgumentParserWithHelp(ArgumentParser):
    def error(self, message):
        self.print_help()
        super().error(message)


arg_parser = ArgumentParserWithHelp(description="Mys_Goods_Tool", usage=USAGE)
arg_parser.add_argument("-m", "--mode", dest="mode", choices=["guide", "exchange-simple"],
                        default="guide")
arg_parser.add_argument("-c", "--conf", type=str, dest="conf", default=None)

TEXTUAL_DEBUG = False


def main(textual_app: Optional[App] = None):
    arg = arg_parser.parse_args()

    if arg.conf is not None:
        mys_goods_tool.user_data.CONFIG_PATH = arg.conf
        mys_goods_tool.user_data.config, mys_goods_tool.user_data.different_device_and_salt = load_config()
    if arg.mode == "guide":
        if textual_app is None:
            from mys_goods_tool.tui import TuiApp
            textual_app = TuiApp()
        textual_app.run()
    elif arg.mode == "exchange-simple":
        exchange_mode_simple()


if __name__ == "__main__":
    app: Optional[App] = None
    if TEXTUAL_DEBUG:
        from mys_goods_tool.tui import TuiApp

        app = TuiApp()
    main(app)
