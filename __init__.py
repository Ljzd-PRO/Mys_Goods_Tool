import multiprocessing

from mys_goods_tool.__main__ import main

if __name__ == "__main__":
    multiprocessing.freeze_support()
    main()
