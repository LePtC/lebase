# -*- coding: utf-8 -*-
"""
计时器相关类和函数
"""
import time
from lelog.logs import log
from lebase.safes import ensure_numstr


def logtime(now=None):
    if now is not None:
        __now = now
    else:
        __now = time.localtime(time.time())
    return time.strftime("%m/%d %H:%M:%S", __now)


class Clock:
    borntime = 0
    withtime = 0
    name = "未命名"

    def __init__(self, processname="未命名"):
        self.name = processname  # 是否需要 ensure.st(processname)？
        self.borntime = time.time()

    def __enter__(self):
        self.withtime = time.time()
        log.info(f"开始：{self.name}")
        return self

    def __exit__(self, type, value, trace):
        log.info(f"完毕：{self.name}（用时：{ensure_numstr(time.time() - self.withtime)} s）")


if __name__ == "__main__":

    with Clock(__file__) as ck:
        print("Hello")
