from lebase.times.clock import logtime, Clock
import time


def test_logtime():
    now = time.localtime()
    result = logtime(now)
    assert isinstance(result, str)
    assert len(result) >= 8


def test_clock_context():
    with Clock("测试计时器") as ck:
        assert isinstance(ck, Clock)


if __name__ == "__main__":
    import pytest
    pytest.main([__file__])
