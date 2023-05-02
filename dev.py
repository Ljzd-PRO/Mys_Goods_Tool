import pydevd_pycharm

DEBUG_SERVER = ('192.168.1.161', 5678)
pydevd_pycharm.settrace(DEBUG_SERVER[0], port=DEBUG_SERVER[1], stdoutToServer=True, stderrToServer=True)

import mys_goods_tool.__main__
from mys_goods_tool.tui import TuiApp

if __name__ == '__main__':
    app = TuiApp()
    mys_goods_tool.__main__.main(app)