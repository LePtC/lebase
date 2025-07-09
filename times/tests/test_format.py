from lebase.times import format
import time
from datetime import datetime


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
