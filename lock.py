# -*- coding: utf-8 -*-
"""
本模块提供了一个文件锁实现方案，主要用于在 Windows 系统中多个 Python 程序（以及多线程）间避免同时操作浏览器等共享资源时产生冲突。
功能包括：
  - acquire：获取锁接口，参数包括锁名称、锁有效时长（duration）以及获取超时时间（timeout），支持超时后采用不同策略（枚举方式：RAISE、GIVEUP、FORCE）。
  - release：释放锁接口，要求传入锁名称和 token；如果 token 不匹配则释放失败；支持传入 "FORCE" 强制释放。
  - with 语句支持：定义了 Lock 上下文管理器，可直接用 with 语句获取和释放锁。
  - query：查询当前系统上所有锁的接口，返回一个包含锁名称和对应 token 信息的字典。

锁文件存放在由 `lev.appdata / locks` 目录下，文件名即为锁名称。token 格式为：
    name-pyFilename-pid_threadId-acquireTime-duration
其中：
  - pyFilename：通过 `getattr(sys.modules['__main__'], '__file__', sys.argv[0])` 获取当前主程序文件名
  - pid：当前进程ID
  - threadId：当前线程标识
  - acquireTime：获取锁的时间（整数秒）
  - duration：锁的生效时长（秒）

注意：在获取锁时若锁文件已存在，会每30秒轮询一次；若等待时间超过 timeout，则根据配置的超时策略采取相应操作。
"""

import os
import sys
import time
import threading
import enum
# from pathlib import Path

from lelog.logs import log  # 日志模块，包含 log.info、log.warn、log.error
from levar import lev  # lev.appdata 为一个 pathlib.Path 对象，代表读写文件的目录


LOCK_DIR = lev.appdata / "locks"


# 定义超时策略的枚举类型
class TimeoutStrategy(enum.Enum):
    RAISE = 1  # 超时后抛出异常
    GIVEUP = 2  # 超时后放弃获取锁，返回None
    FORCE = 3  # 超时后强制清除原锁再获取锁


# 自定义异常：获取锁超时
class LockAcquisitionTimeoutError(Exception):
    pass


# 工具函数：获取当前主程序文件名
def get_py_filename():
    fullPath = getattr(sys.modules["__main__"], "__file__", sys.argv[0])
    return fullPath.split("\\")[-1]


# 工具函数：根据锁名称获取锁文件的完整路径
def get_lock_file_path(lockName):
    if not LOCK_DIR.exists():
        LOCK_DIR.mkdir(parents=True, exist_ok=True)
    return LOCK_DIR / f"{lockName}.lock"


# 工具函数：解析 token，返回字典格式的信息
def parse_token(token):
    """
    解析 token 字符串，返回字典格式：
      {
         "name": 锁名称,
         "pyFilename": 主程序文件名,
         "pidThread": "pid_threadId",
         "acquireTime": 获取锁时间 (int),
         "duration": 锁有效时长 (int)
      }
    """
    parts = token.split("-")
    if len(parts) < 5:
        return None
    try:
        pidThread = parts[2]
        acquireTime = int(parts[3])
        duration = int(parts[4])
        return {
            "name": parts[0],
            "pyFilename": parts[1],
            "pidThread": pidThread,
            "acquireTime": acquireTime,
            "duration": duration,
        }
    except Exception as e:
        log.error("解析 token 失败：{}，错误：{}".format(token, e))
        return None


# 判断锁是否已过期（锁过期后即使 owner 未调用 release，其它进程可获取锁）
def is_lock_expired(token):
    parsed = parse_token(token)
    if not parsed:
        # 若解析失败，认为锁已失效
        return True
    expireTime = parsed["acquireTime"] + parsed["duration"]
    return time.time() > expireTime


# 写 token 到文件
def write_token_to_file(lockFile, token):
    with open(lockFile, "w", encoding="utf-8") as f:
        f.write(token)


# 从文件读取 token
def read_token_from_file(lockFile):
    try:
        with open(lockFile, "r", encoding="utf-8") as f:
            token = f.read().strip()
        return token
    except Exception as e:
        log.error("读取锁文件失败：{}，错误：{}".format(lockFile, e))
        return None


def acquire(name, duration=600, timeout=3600, timeoutStrategy=TimeoutStrategy.RAISE, retry=30):
    """
    获取锁的接口

    参数:
      name: 锁的名字，同时也是文件名
      duration: 锁的有效时长（秒），默认为600秒
      timeout: 等待获取锁的超时时间（秒），默认为3600秒
      timeoutStrategy: 超时策略，枚举类型 TimeoutStrategy，有 RAISE、GIVEUP、FORCE 三种取值

    返回:
      成功获取锁后返回 token 字符串，格式为 "name-pyFilename-pid_threadId-acquireTime-duration"
      若获取失败：若超时策略为 GIVEUP，则返回 None；若超时策略为 RAISE，则抛出异常
    """
    startTime = time.time()
    lockFile = get_lock_file_path(name)
    currentPyFile = get_py_filename()
    currentPid = os.getpid()
    currentThreadId = threading.get_ident()

    while True:
        currentTime = time.time()
        if currentTime - startTime >= timeout:
            log.info("等待锁超时，当前策略为：{}".format(timeoutStrategy.name))
            if timeoutStrategy == TimeoutStrategy.RAISE:
                raise LockAcquisitionTimeoutError("获取锁 {} 超时".format(name))
            elif timeoutStrategy == TimeoutStrategy.GIVEUP:
                return None
            elif timeoutStrategy == TimeoutStrategy.FORCE:
                # 强制清除锁文件
                if lockFile.exists():
                    try:
                        os.remove(lockFile)
                        log.warning("超时后强制清除锁：{}".format(name))
                    except Exception as e:
                        log.error("强制清除锁失败：{}，错误：{}".format(name, e))
                        raise LockAcquisitionTimeoutError("强制清除锁失败: {}".format(name))
                # 立即尝试获取锁，不做延时
        try:
            # 构造 token 格式：name-pyFilename-pid_threadId-acquireTime-duration
            acquireTime = int(time.time())
            token = "{}-{}-{}_{}-{}-{}".format(
                name, currentPyFile, currentPid, currentThreadId, acquireTime, duration
            )
            # 尝试以独占方式创建文件（若文件已存在会抛出 FileExistsError）
            with open(lockFile, "x", encoding="utf-8") as f:
                f.write(token)
            log.debug("成功获取锁：{}".format(token))
            return token
        except FileExistsError:
            # 锁文件已存在，读取已有的 token 信息
            existingToken = read_token_from_file(lockFile)
            if existingToken is None:
                log.warning("锁文件存在但读取失败，尝试删除锁文件：{}".format(name))
                try:
                    os.remove(lockFile)
                    log.success("删除异常锁文件成功：{}".format(name))
                except Exception as e:
                    log.error("删除锁文件失败：{}，错误：{}".format(name, e))
            else:
                if is_lock_expired(existingToken):
                    log.warning("检测到锁已过期，准备删除旧锁：{}".format(existingToken))
                    try:
                        os.remove(lockFile)
                        log.success("删除过期锁成功：{}".format(name))
                    except Exception as e:
                        log.error("删除过期锁失败：{}，错误：{}".format(name, e))
                        # 若删除失败，则继续等待
                else:
                    log.warning("锁 {} 当前被占用，token信息：{}".format(name, existingToken))
        # 每30秒轮询一次
        sleepTime = retry
        remainingTime = timeout - (time.time() - startTime)
        if remainingTime < sleepTime:
            sleepTime = remainingTime
        if sleepTime > 0:
            time.sleep(sleepTime)
        else:
            continue


def release(name, token):
    """
    释放锁的接口

    参数:
      name: 锁的名字
      token: 获取锁时返回的 token；如果传入 "FORCE" 则表示强制释放锁
    """
    lockFile = get_lock_file_path(name)
    if token == "FORCE":
        log.warning("使用 FORCE 标识强制释放锁：{}".format(name))
        if lockFile.exists():
            try:
                os.remove(lockFile)
                log.success("强制释放锁成功：{}".format(name))
            except Exception as e:
                log.error("强制释放锁失败：{}，错误：{}".format(name, e))
        else:
            log.error("锁文件不存在，无法强制释放：{}".format(name))
        return

    if not lockFile.exists():
        log.error("锁文件不存在，无法释放：{}".format(name))
        return

    existingToken = read_token_from_file(lockFile)
    if existingToken != token:
        log.error("token 不匹配，无法释放锁：{}，当前锁 token：{}，传入 token：{}".format(name, existingToken, token))
        return
    try:
        os.remove(lockFile)
        log.debug("成功释放锁：{}".format(token))
    except Exception as e:
        log.error("释放锁失败：{}，错误：{}".format(token, e))


# 定义支持 with 语句的上下文管理器
class Lock:
    """
    锁上下文管理器，支持 with 语句
    用法示例：
        with Lock("myLock", duration=600, timeout=3600, timeoutStrategy=TimeoutStrategy.RAISE) as token:
            # 执行需要锁保护的代码
    """

    def __init__(self, name, duration=600, timeout=3600, timeoutStrategy=TimeoutStrategy.RAISE, retry=30):
        self.name = name
        self.duration = duration
        self.timeout = timeout
        self.timeoutStrategy = timeoutStrategy
        self.retry = retry
        self.token = None

    def __enter__(self):
        self.token = acquire(self.name, self.duration, self.timeout, self.timeoutStrategy, self.retry)
        return self.token

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.token:
            release(self.name, self.token)


def query():
    """
    查询当前系统上所有的锁信息

    返回:
      dict，键为锁的名字，值为锁文件中存储的 token 信息
    """
    lockDict = {}
    if not LOCK_DIR.exists():
        log.info("锁目录不存在")
        return lockDict
    for lockFile in LOCK_DIR.iterdir():
        if lockFile.is_file():
            try:
                token = lockFile.read_text(encoding="utf-8").strip()
                lockDict[lockFile.name] = token
            except Exception as e:
                log.error("读取锁文件失败：{}，错误：{}".format(lockFile.name, e))
    return lockDict


# Demo 用例
if __name__ == "__main__":
    import random

    def demo_acquire_and_release(lockName):
        """
        演示直接调用 acquire 和 release 接口
        """
        try:
            token = acquire(lockName, duration=10, timeout=30, timeoutStrategy=TimeoutStrategy.FORCE, retry=3)
            if token:
                log.success("Demo: 获取锁成功，token: {}".format(token))
                # 模拟执行一些任务
                time.sleep(random.randint(1, 5))
                release(lockName, token)
            else:
                log.info("Demo: 获取锁失败，放弃获取")
        except Exception as e:
            log.error("Demo: 异常: {}".format(e))

    def demo_with_lock(lockName):
        """
        演示使用 with 语句进行锁的自动管理
        """
        try:
            with Lock(lockName, duration=10, timeout=30, timeoutStrategy=TimeoutStrategy.GIVEUP, retry=3) as token:
                if token:
                    log.success("Demo with: 获取锁成功，token: {}".format(token))
                    time.sleep(random.randint(1, 5))
                else:
                    log.info("Demo with: 未能获取锁")
        except Exception as e:
            log.error("Demo with: 异常: {}".format(e))

    # 定义锁名称（也作为锁文件名）
    lockName = "browserLock"

    # 模拟多线程场景：多个线程同时尝试获取同一个锁
    threadList = []
    for i in range(3):
        t = threading.Thread(target=demo_acquire_and_release, args=(lockName,))
        t.start()
        threadList.append(t)
    for t in threadList:
        t.join()

    # 查询当前系统上的锁信息
    currentLocks = query()
    log.info("当前锁信息: {}".format(currentLocks))

    # 使用 with 语句演示获取锁
    demo_with_lock(lockName)
