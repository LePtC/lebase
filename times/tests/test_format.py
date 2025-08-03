import time
from datetime import datetime

from lebase.times import format


def test_any2unix():
    result = format.any2unix("1970-01-01 08:00:00")
    assert isinstance(result, float)


def test_any2unix_str():
    ts = format.any2unix("2025020311")
    assert isinstance(ts, float)
    assert ts > 0


def test_any2unix_datetime():
    now = datetime.now()
    ts = format.any2unix(now)
    assert abs(ts - time.mktime(now.timetuple())) < 5


def test_unix2chs():
    result = format.unix2chs(0)
    assert isinstance(result, str)


def test_nearest_yyyymm():
    """测试 nearest_yyyymm 函数"""
    from lebase.times.datecalc import nearest_yyyymm
    
    # 测试当前时间
    result = nearest_yyyymm()
    assert isinstance(result, str)
    assert len(result) == 6
    assert result.isdigit()
    
    # 测试指定时间（2024年1月10日，15号前，应该返回202401）
    test_time = 1704844800  # 2024-01-10 00:00:00
    result = nearest_yyyymm(test_time)
    assert result == "202401"
    
    # 测试指定时间（2024年1月20日，15号后，应该返回202402）
    test_time = 1705708800  # 2024-01-20 00:00:00
    result = nearest_yyyymm(test_time)
    assert result == "202402"
    
    # 测试偏移量
    test_time = 1704844800  # 2024-01-10 00:00:00
    result = nearest_yyyymm(test_time, offset=1)
    assert result == "202402"
    
    # 测试负偏移量
    result = nearest_yyyymm(test_time, offset=-1)
    assert result == "202312"


if __name__ == "__main__":
    import pytest

    pytest.main([__file__])
