import multiprocessing

from mys_goods_tool.__main__ import main
from mys_goods_tool.tui import TuiApp

if __name__ == "__main__":
    multiprocessing.freeze_support()
    app = TuiApp()
    main(app)
