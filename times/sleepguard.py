# -*- coding: utf-8 -*-
"""
休眠控制相关类
"""
import time
import random
from lelog.logs import log


class SleepGuard:
    """
    运行间隔保障类，用于确保两次操作之间至少间隔指定的时间（包含一定随机性）。

    参数:
        minTime: 最低运行间隔时间（单位：秒）。
        plusRandom: 额外时间随机增量（单位：秒），在实际间隔时间中会乘以0~1范围内的随机数，默认值为0。

    使用方式:
        使用 with 语句调用该类，在退出 with 块时会根据代码块的实际运行时间决定是否需要额外 sleep。

    说明:
        - 进入上下文时记录开始时间。
        - 离开上下文时计算代码块运行的实际时间。
        - 如果实际运行时间小于计划的间隔（minTime + plusRandom*随机数），则调用 sleep 延时剩余时间；
          否则直接返回，不做延时。
    """

    def __init__(self, minTime, plusRandom=0):
        self.minTime = minTime  # 最低运行间隔
        self.plusRandom = plusRandom  # 随机增量
        # 计算计划的总间隔时间（随机因子取值范围 [0,1)）
        self.planTime = self.minTime + self.plusRandom * random.uniform(0, 1)
        log.debug("初始化SleepGuard: planTime = {:.3f}秒".format(self.planTime))
        self.startTime = None

    def __enter__(self):
        # 记录进入上下文的时间
        self.startTime = time.time()
        log.debug("进入SleepGuard上下文，记录开始时间：{:.3f}".format(self.startTime))
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # 计算代码块实际运行时间
        elapsedTime = time.time() - self.startTime
        log.debug("退出SleepGuard上下文，代码块运行时间：{:.3f}秒".format(elapsedTime))
        # 如果运行时间不足计划时间，则休眠剩余时间
        if elapsedTime < self.planTime:
            sleepTime = self.planTime - elapsedTime
            log.debug("实际运行时间不足计划时间，休眠 {:.3f} 秒".format(sleepTime))
            time.sleep(sleepTime)
        else:
            log.debug("代码块运行时间超过计划时间，无需休眠")


if __name__ == "__main__":

    # ----------------------------
    # SleepGuard
    # ----------------------------

    # 示例1：代码块执行时间短于计划间隔
    log.info("示例1: 代码块执行时间短于计划时间")
    with SleepGuard(2, 1):  # 计划时间介于2到3秒之间
        log.info("执行快速任务")
        time.sleep(0.5)  # 模拟任务执行耗时0.5秒

    # 示例2：代码块执行时间长于计划间隔
    log.info("示例2: 代码块执行时间长于计划时间")
    with SleepGuard(2, 1):  # 计划时间介于2到3秒之间
        log.info("执行耗时任务")
        time.sleep(3)  # 模拟任务执行耗时3秒

    # 示例3：不使用随机增量（plusRandom缺省）
    log.info("示例3: plusRandom缺省，仅使用最低间隔")
    with SleepGuard(2):  # 此时计划时间固定为2秒
        log.info("执行任务")
        time.sleep(1)  # 模拟任务执行耗时1秒

    # input("按任意键退出 \n ")
    # print(0)
    pass
