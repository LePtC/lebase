# -*- coding: utf-8 -*-
"""
计时器相关类和函数
"""
import time
from types import TracebackType
from typing import Optional

from lebase.safes import ensure_numstr
from lelog.logs import log


def logtime(now: Optional[time.struct_time] = None) -> str:
    if now is not None:
        nowTime = now
    else:
        nowTime = time.localtime(time.time())
    return time.strftime("%m/%d %H:%M:%S", nowTime)


class Clock:
    def __init__(self, processName: str = "未命名"):
        self.name = processName  # 是否需要 ensure.st(processName)？
        self.bornTime = time.time()
        self.withTime = 0

    def __enter__(self):
        self.withTime = time.time()
        log.info(f"开始：{self.name}")
        return self

    def __exit__(
        self, type: Optional[type[BaseException]], value: Optional[BaseException], trace: Optional[TracebackType]
    ) -> None:
        log.info(f"完毕：{self.name}（用时：{ensure_numstr(time.time() - self.withTime)} s）")


if __name__ == "__main__":
    with Clock(__file__) as ck:
        print("Hello")
