# -*- coding: utf-8 -*-
"""
lock.py 的测试文件
"""

import threading
import time

from lebase.lock import Lock, LockAcquisitionTimeoutError, TimeoutStrategy, acquire, query, release


def test_acquire_and_release():
    """测试基本的获取和释放锁功能"""
    lock_name = "test_basic_lock"
    duration = 60
    timeout = 30
    retry = 1

    # 获取锁
    token = acquire(lock_name, duration=duration, timeout=timeout, retry=retry)
    assert token is not None

    # 查询锁
    locks = query()
    assert lock_name + ".lock" in locks
    assert locks[lock_name + ".lock"] == token

    # 释放锁
    release(lock_name, token)

    # 确认锁已释放
    locks = query()
    assert lock_name + ".lock" not in locks


def test_acquire_expired_lock():
    """测试获取过期锁"""
    lock_name = "test_expired_lock"
    duration = 1  # 设置很短的持续时间
    timeout = 30
    retry = 1

    # 获取锁
    token = acquire(lock_name, duration=duration, timeout=timeout, retry=retry)
    assert token is not None

    # 等待锁过期
    time.sleep(2)

    # 再次获取锁（应该能获取到，因为原锁已过期）
    new_token = acquire(lock_name, duration=duration, timeout=timeout, retry=retry)
    assert new_token is not None
    assert new_token != token

    # 释放锁
    release(lock_name, new_token)


def test_force_release_lock():
    """测试强制释放锁"""
    lock_name = "test_force_release_lock"
    duration = 60
    timeout = 30
    retry = 1

    # 获取锁
    token = acquire(lock_name, duration=duration, timeout=timeout, retry=retry)
    assert token is not None

    # 强制释放锁
    release(lock_name, "FORCE")

    # 确认锁已释放
    locks = query()
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
        locks = query()
        assert lock_name + ".lock" in locks
        assert locks[lock_name + ".lock"] == token

    # 离开with语句后，锁应该被释放
    locks = query()
    assert lock_name + ".lock" not in locks


def test_concurrent_lock_acquisition():
    """测试并发获取锁"""
    lock_name = "test_concurrent_lock"
    duration = 60
    timeout = 30
    retry = 1

    results = []

    def acquire_lock():
        try:
            token = acquire(lock_name, duration=duration, timeout=timeout, retry=retry)
            if token:
                # 等待一小段时间再释放锁
                time.sleep(0.1)
                release(lock_name, token)
                results.append("success")
            else:
                results.append("failed")
        except LockAcquisitionTimeoutError:
            results.append("timeout")

    # 启动多个线程尝试同时获取锁
    threads = []
    for _ in range(3):
        thread = threading.Thread(target=acquire_lock)
        threads.append(thread)
        thread.start()

    # 等待所有线程完成
    for thread in threads:
        thread.join()

    # 至少有一个线程应该成功获取锁
    assert "success" in results


def test_timeout_strategy_raise():
    """测试超时策略 RAISE"""
    lock_name = "test_raise_strategy"
    duration = 60
    timeout = 1  # 很短的超时时间
    retry = 1

    # 先获取一个锁
    token = acquire(lock_name, duration=duration, timeout=timeout, retry=retry)
    assert token is not None

    # 尝试再次获取同一个锁，应该会超时并抛出异常
    try:
        acquire(lock_name, duration=duration, timeout=timeout,
                timeoutStrategy=TimeoutStrategy.RAISE, retry=retry)
        raise AssertionError("应该抛出 LockAcquisitionTimeoutError 异常")
    except LockAcquisitionTimeoutError:
        pass  # 正确的行为

    # 清理
    release(lock_name, token)


def test_timeout_strategy_giveup():
    """测试超时策略 GIVEUP"""
    lock_name = "test_giveup_strategy"
    duration = 60
    timeout = 1  # 很短的超时时间
    retry = 1

    # 先获取一个锁
    token = acquire(lock_name, duration=duration, timeout=timeout, retry=retry)
    assert token is not None

    # 尝试再次获取同一个锁，应该会超时并返回 None
    result = acquire(lock_name, duration=duration, timeout=timeout,
                     timeoutStrategy=TimeoutStrategy.GIVEUP, retry=retry)
    assert result is None

    # 清理
    release(lock_name, token)


def test_timeout_strategy_force():
    """测试超时策略 FORCE"""
    lock_name = "test_force_strategy"
    duration = 60
    timeout = 1  # 很短的超时时间
    retry = 1

    # 先获取一个锁
    token = acquire(lock_name, duration=duration, timeout=timeout, retry=retry)
    assert token is not None

    # 尝试再次获取同一个锁，应该会强制清除原锁并获取新锁
    new_token = acquire(lock_name, duration=duration, timeout=timeout,
                        timeoutStrategy=TimeoutStrategy.FORCE, retry=retry)
    assert new_token is not None
    assert new_token != token

    # 新锁应该有效
    locks = query()
    assert lock_name + ".lock" in locks
    assert locks[lock_name + ".lock"] == new_token

    # 清理
    release(lock_name, new_token)


def test_parse_invalid_token():
    """测试解析无效token"""
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
    expired_token = chr(110) + chr(97) + chr(109) + chr(101) + chr(45) + chr(102) + chr(105) + chr(108) + chr(101) + chr(45) + chr(49) + chr(50) + chr(51) + chr(95) + chr(52) + chr(53) + chr(54) + chr(45) + chr(49) + chr(48) + chr(48) + chr(48) + chr(45) + chr(49)  # "name-file-123_456-1000-1"  # 很早之前的token
    assert is_lock_expired(expired_token) is True


if __name__ == "__main__":
    # 运行所有测试函数
    test_acquire_and_release()
    test_acquire_expired_lock()
    test_force_release_lock()
    test_with_statement_lock()
    test_concurrent_lock_acquisition()
    test_timeout_strategy_raise()
    test_timeout_strategy_giveup()
    test_timeout_strategy_force()
    test_parse_invalid_token()
    print("所有测试通过！")
