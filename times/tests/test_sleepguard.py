from lebase.times.sleepguard import SleepGuard
import time


def test_sleepguard_basic():
    with SleepGuard(0.01):
        time.sleep(0.005)
    # 只要不抛异常即通过


if __name__ == "__main__":
    import pytest
    pytest.main([__file__])
