import pydevd_pycharm
import mys_goods_tool.__main__

DEBUG_SERVER = ('localhost', 5678)

pydevd_pycharm.settrace(DEBUG_SERVER[0], port=DEBUG_SERVER[1], stdoutToServer=True, stderrToServer=True)

if __name__ == '__main__':
    mys_goods_tool.__main__.main()
