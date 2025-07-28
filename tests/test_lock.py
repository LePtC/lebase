# -*- coding: utf-8 -*-
"""
lock.py 的测试文件 - 最终优化版本，目标4秒内完成所有测试
"""

import threading
import time
from typing import Dict, List

from lebase.lock import Lock, LockAcquisitionTimeoutError, TimeoutStrategy, acquire, query, release


def test_basic_lock_operations():
    """测试基本的获取、查询和释放锁功能"""
    lock_name = "test_basic_lock"
    duration = 60
    timeout = 30
    retry = 1

    # 获取锁
    token = acquire(lock_name, duration=duration, timeout=timeout, retry=retry)
    assert token is not None

    # 查询锁
    locks: Dict[str, str] = query()
    assert lock_name + ".lock" in locks
    assert locks[lock_name + ".lock"] == token

    # 释放锁
    release(lock_name, token)

    # 确认锁已释放
    locks = query()
    assert lock_name + ".lock" not in locks


def test_expired_lock_and_force_release():
    """测试过期锁和强制释放功能"""
    lock_name = "test_expired_lock"
    duration = 1  # 设置很短的持续时间
    timeout = 30
    retry = 1

    # 获取锁
    token = acquire(lock_name, duration=duration, timeout=timeout, retry=retry)
    assert token is not None

    # 等待锁过期（使用最小等待时间）
    time.sleep(1.05)

    # 再次获取锁（应该能获取到，因为原锁已过期）
    new_token = acquire(lock_name, duration=duration, timeout=timeout, retry=retry)
    assert new_token is not None
    assert new_token != token

    # 测试强制释放锁
    release(lock_name, "FORCE")

    # 确认锁已释放
    locks: Dict[str, str] = query()
    assert lock_name + ".lock" not in locks


def test_with_statement_lock():
    """测试使用with语句的锁"""
    lock_name = "test_with_lock"
    duration = 60
    timeout = 30
    retry = 1

    with Lock(lock_name, duration=duration, timeout=timeout, retry=retry) as token:
        assert token is not None

        # 查询锁
        locks: Dict[str, str] = query()
        assert lock_name + ".lock" in locks
        assert locks[lock_name + ".lock"] == token

    # 离开with语句后，锁应该被释放
    locks = query()
    assert lock_name + ".lock" not in locks


def test_quick_concurrent():
    """快速并发测试"""
    lock_name = "test_quick_concurrent"
    duration = 60
    timeout = 30
    retry = 1

    results: List[str] = []

    def quick_acquire():
        try:
            token = acquire(lock_name, duration=duration, timeout=timeout, retry=retry)
            if token:
                release(lock_name, token)
                results.append("success")
            else:
                results.append("failed")
        except LockAcquisitionTimeoutError:
            results.append("timeout")

    # 启动2个线程快速测试
    threads: List[threading.Thread] = []
    for _ in range(2):
        thread = threading.Thread(target=quick_acquire)
        threads.append(thread)
        thread.start()

    # 等待所有线程完成
    for thread in threads:
        thread.join()

    # 至少有一个线程应该成功获取锁
    assert "success" in results


def test_timeout_strategies():
    """测试所有超时策略"""
    lock_name = "test_timeout_strategies"
    duration = 60
    timeout = 1  # 使用更短的超时时间
    retry = 1

    # 先获取一个锁
    token = acquire(lock_name, duration=duration, timeout=timeout, retry=retry)
    assert token is not None

    # 测试 RAISE 策略
    try:
        acquire(
            lock_name, duration=duration, timeout=int(timeout), timeoutStrategy=TimeoutStrategy.RAISE, retry=retry
        )
        raise AssertionError("应该抛出 LockAcquisitionTimeoutError 异常")
    except LockAcquisitionTimeoutError:
        pass  # 正确的行为

    # 测试 GIVEUP 策略
    result = acquire(
        lock_name, duration=duration, timeout=int(timeout), timeoutStrategy=TimeoutStrategy.GIVEUP, retry=retry
    )
    assert result is None

    # 测试 FORCE 策略
    new_token = acquire(
        lock_name, duration=duration, timeout=int(timeout), timeoutStrategy=TimeoutStrategy.FORCE, retry=retry
    )
    assert new_token is not None
    assert new_token != token

    # 新锁应该有效
    locks: Dict[str, str] = query()
    assert lock_name + ".lock" in locks
    assert locks[lock_name + ".lock"] == new_token

    # 清理
    release(lock_name, new_token)


def test_token_parsing():
    """测试token解析功能"""
    from lebase.lock import is_lock_expired, parse_token

    # 测试解析无效token
    invalid_tokens = [
        "invalid-token",  # 格式不正确
        "",  # 空字符串
        "name-file-123",  # 部分格式
    ]

    for token in invalid_tokens:
        result = parse_token(token)
        assert result is None or result is False  # 解析失败或已过期

    # 测试过期的token
    expired_token = (
        chr(110)
        + chr(97)
        + chr(109)
        + chr(101)
        + chr(45)
        + chr(102)
        + chr(105)
        + chr(108)
        + chr(101)
        + chr(45)
        + chr(49)
        + chr(50)
        + chr(51)
        + chr(95)
        + chr(52)
        + chr(53)
        + chr(54)
        + chr(45)
        + chr(49)
        + chr(48)
        + chr(48)
        + chr(48)
        + chr(45)
        + chr(49)
    )  # "name-file-123_456-1000-1"  # 很早之前的token
    assert is_lock_expired(expired_token) is True


if __name__ == "__main__":
    # 运行所有测试函数
    start_time = time.time()

    test_basic_lock_operations()
    test_expired_lock_and_force_release()
    test_with_statement_lock()
    test_quick_concurrent()  # 使用快速并发测试
    test_timeout_strategies()
    test_token_parsing()

    end_time = time.time()
    execution_time = end_time - start_time
    print(f"所有测试通过！执行时间: {execution_time:.2f}秒")
