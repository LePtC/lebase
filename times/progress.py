# -*- coding: utf-8 -*-
"""
进度条相关类和函数
"""
import time
from typing import Optional

from lelog.logs import log


def print_progress(startTime: float, countNum: int, totalNum: int, detail: str = "") -> str:
    elapsedTime = int(time.time() - startTime)
    remainingTime = ((totalNum - countNum) / countNum) * elapsedTime if countNum else 0
    percentage = (countNum / totalNum) * 100 if totalNum else 0
    textProgress = f"{countNum} / {totalNum} ({percentage:.1f}%) T: {elapsedTime} / {remainingTime:.0f} s {detail}"
    print(f"\r{textProgress}", end="", flush=True)
    return textProgress


class Progress:
    """
    进度打印日志类，通过 with 语法管理进度记录的开始、更新和结束。

    Attributes:
        totalCount (int): 总任务数量
        startTime (float): 任务开始时的时间戳
        currentCount (int): 当前已处理的任务数量
        printStep (int): 每隔多少步打印一次进度信息
    """

    def __init__(self, totalCount: int, msg: str = "", printStep: int = 1, logStep: int = 0):
        """
        初始化进度日志对象。

        Args:
            totalCount (int): 总任务数量
            msg (str): 开始时输出的日志信息
            printStep (int): 每隔多少步打印一次进度信息，缺省值为1
            logStep (int): 在 printStep 基础上，每隔多少个 printStep 打印一次进度信息，缺省值为0（关闭）
        """
        self.totalCount = totalCount
        self.msg = msg
        self.printStep = printStep if printStep > 0 else 1  # 确保 printStep 为正整数
        self.logStep = logStep
        self.startTime = time.time()
        self.currentCount = 0
        # 输出开始日志信息
        log.info("开始 " + msg + " ...")

    def __enter__(self):
        """
        进入 with 语句时调用，返回对象自身。
        """
        return self

    def tik(self, detail: str = ""):
        """
        更新进度，计数器加一，并根据 printStep 判断是否打印当前进度信息。
        注意：若总任务数无法整除 printStep，仍保证最后一次进度（100%）能打印出来。

        Args:
            detail (str): 当前任务的详细描述信息
        """
        self.currentCount += 1
        # 只有当步数是 printStep 的整数倍或者完成最后一步时，才打印进度信息
        if (self.currentCount % self.printStep == 0) or (self.currentCount == self.totalCount):
            msg = self.print_progress(detail)
            if self.logStep > 0:
                if (self.currentCount // self.printStep % self.logStep == 0) or (
                    self.currentCount == self.totalCount
                ):
                    print("")  # 换行
                    log.info(msg)

    def fin(self, detail: str = ""):
        """
        适用于 batchSize 不整除时最后批上传后直接完成
        """
        self.currentCount = self.totalCount - 1
        self.tik(detail)

    def print_progress(self, detail: str = "") -> str:
        """
        打印当前进度信息，包括已处理数量、总数量、百分比、已用时间和估计剩余时间。

        Args:
            detail (str): 当前任务的详细描述信息
        """
        elapsedTime = int(time.time() - self.startTime)
        remainingTime = int(self.calc_remaining_time(elapsedTime, self.currentCount, self.totalCount))
        percentage = self.calc_percentage(self.currentCount, self.totalCount)
        textProgress = (
            f"{self.currentCount} / {self.totalCount} "
            f"({percentage:.1f}%) T: {elapsedTime} / {remainingTime} s "
            f"{detail}"
        )
        # \r 回到行首，end="" 不换行，flush 确保实时输出
        print(f"\r{textProgress}", end="", flush=True)
        return textProgress

    @staticmethod
    def calc_remaining_time(elapsedTime: int, currentCount: int, totalCount: int) -> float:
        """
        计算估计的剩余时间。

        Args:
            elapsedTime (int): 已用时间（秒）
            currentCount (int): 当前已处理任务数
            totalCount (int): 总任务数

        Returns:
            float: 估计剩余时间（秒）
        """
        if currentCount:
            return ((totalCount - currentCount) / currentCount) * elapsedTime
        else:
            return 0

    @staticmethod
    def calc_percentage(currentCount: int, totalCount: int) -> float:
        """
        计算已处理任务的百分比。

        Args:
            currentCount (int): 当前已处理任务数
            totalCount (int): 总任务数

        Returns:
            float: 完成百分比
        """
        if totalCount:
            return (currentCount / totalCount) * 100
        else:
            return 0

    def __exit__(self, exc_type: Optional[type], exc_val: Optional[Exception], exc_tb: Optional[type]) -> None:
        """
        离开 with 语句时调用，输出结束日志和换行符。
        如果在任务处理中发生异常，则记录警告日志。

        Args:
            exc_type: 异常类型
            exc_val: 异常值
            exc_tb: 异常追踪信息
        """
        # 输出换行符，确保终端输出整洁
        print("")
        elapsedTime = time.time() - self.startTime
        if exc_type:
            # 如果出现异常，则记录警告日志
            log.warning(f"任务：{self.msg} 异常终止，用时：{elapsedTime:.1f} s")
        else:
            log.success(f"任务：{self.msg} 成功完成，用时：{elapsedTime:.1f} s")


if __name__ == "__main__":

    import random

    def demo_normal_flow():
        """
        示例1：正常流程的使用方法，模拟处理一系列任务，并实时更新进度信息。
        此处设置 printStep=3，即每 3 个任务打印一次进度，最后一步无论如何都会打印。
        """
        # 模拟任务列表（例如：20 个任务）
        someList = [{"name": f"Task{i}"} for i in range(1, 21)]

        with Progress(len(someList), f"检查 {len(someList)} 个数据库") as pr:
            for task in someList:
                time.sleep(random.uniform(0.1, 0.3))  # 模拟任务处理耗时
                pr.tik(f"当前任务: {task['name']}")

    def demo_exception_flow():
        """
        示例2：处理过程中出现异常的情况，演示如何捕获异常并记录日志。
        """
        try:
            with Progress(totalCount=10, msg="处理 10 个下载", printStep=2, logStep=1) as pr:
                for i in range(1, 11):
                    time.sleep(0.2)
                    # 模拟在第5个任务时抛出异常
                    if i == 5:
                        raise ValueError("示例异常")
                    pr.tik(detail=f"任务{i}")
        except Exception as e:
            log.warning(f"处理过程中出现异常: {e}")

    print("===== Demo: 正常流程 =====")
    demo_normal_flow()
    print("\n===== Demo: 异常流程 =====")
    demo_exception_flow()
