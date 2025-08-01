# -*- coding: utf-8 -*-
"""
用途：
    用来在一分钟内执行6次某checker_function，如果单次运行就超过了1分钟则无需重复运行
    在1分钟内退出，以便win定时任务在间隔1分钟后触发下一次
"""
import time
from typing import Any, Callable


class Looper:
    def __init__(self, checker_function: Callable[..., Any], *args: Any, **kwargs: Any) -> None:
        """
        初始化 Looper 上下文管理器：
        - checker_function: 需要执行的检查函数
        - *args, **kwargs: 传递给 checker_function 的参数
        """
        self.checker_function = checker_function
        self.args = args
        self.kwargs = kwargs
        self.start_time = 0.0
        self.last_run_time = 0.0

    def __enter__(self) -> "Looper":
        """进入上下文时，记录开始时间并执行 checker_function"""
        self.start_time = time.time()
        self.last_run_time = self.start_time
        return self  # 返回自身，以便可以在 `with` 语句中使用

    def run(self) -> None:
        """运行 checker_function，并按照时间间隔进行控制"""
        self.checker_function(*self.args, **self.kwargs)  # 运行检查函数
        for _ in range(5):
            current_time = time.time()

            # 如果单次执行已经超过 1 分钟，则退出
            if current_time - self.start_time >= 51:
                break

            # 计算下次执行的等待时间
            elapsed_since_last_run = current_time - self.last_run_time
            if elapsed_since_last_run < 10:
                time.sleep(10 - elapsed_since_last_run)  # 等待至 10 秒间隔

            # 再次检查时间，避免在等待后超时
            current_time = time.time()
            if current_time - self.start_time >= 51:
                break

            self.last_run_time = time.time()  # 更新上次执行时间
            self.checker_function(*self.args, **self.kwargs)  # 运行检查函数

    def __exit__(self, exc_type: Any, exc_value: Any, traceback: Any) -> None:
        """退出上下文时，可以添加清理逻辑（此处无特殊清理操作）"""
        pass


if __name__ == "__main__":

    # 示例 checker_function，支持参数
    def example_checker(name: str, delay: float) -> None:
        print(f"Checker function '{name}' running at {time.strftime('%H:%M:%S')}")
        time.sleep(delay)  # 模拟执行时间

    # 使用 with 语法运行
    with Looper(example_checker, "TestCheck", 0.2) as runner:
        runner.run()
