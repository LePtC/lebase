# -*- coding: utf-8 -*-
"""
日期区间与推算相关函数
"""
from datetime import datetime, timedelta
from typing import List

from lebase.times.format import any2taskId, any2unix, unix2str, unix2taskId


def convert_days_ago(daysString: str) -> datetime.timetuple:
    """应对newbing或B站智能把近期时间自动转x天前"""
    days = int(daysString.split("天前")[0])  # 提取天数
    newDate = datetime.now() - timedelta(days=days)  # 计算新日期
    return newDate.timetuple()  # .strftime("%Y年%m月%d日")  # 返回格式化的日期


def cal_day_diff(timeStr1: str, timeStr2: str) -> float:
    return int((any2unix(timeStr1) - any2unix(timeStr2)) / 8640) / 10


def taskId2ndayago(timeStr: str, days: float) -> str:
    """
    str2str(shifted) 时间平移函数
    在氘化氢 BYK 和 pyfac 里曾叫 few_days_ago
    """
    return unix2taskId(any2unix(timeStr) - 3600 * 24 * days)


def time_str_list(startTime: str, endTime: str, interval: int = 12) -> List[str]:
    """
    根据起止时间,间隔生成字符串时间的列表
    :param startTime: 开始时间
    :param endTime: 结束时间
    :param interval: 间隔（小时），默认为12。
    :return: 包含两端，每隔 interval 个小时的时间列表。
    >>> time_str_list('2020040611',"2020040723")
    ['2020040611', '2020040623', '2020040711', '2020040723']
    """
    # 字符串时间转unix时间
    uStart, uEnd = any2unix(startTime), any2unix(endTime)
    if uStart is None or uEnd is None:
        return []
    # 生成时间列表
    timeList = range(int(uStart), int(uEnd) + 1, interval * 3600)
    # 转换回字符串格式
    return [any2taskId(unix2str(_)) for _ in timeList]


def get_liTaskId_halfmonth(yearStart: int, monthStart: int, yearEnd: int, monthEnd: int) -> List[str]:
    """
    输入：起止年月
    输出：半月精度的 timelist
    """
    resultList = []
    year = yearStart
    while year <= yearEnd:
        month = 1
        if year == yearStart:
            month = monthStart
        monthEndCur = 12
        if year == yearEnd:
            monthEndCur = monthEnd
        while month <= monthEndCur:
            resultList.append(str(year) + ["", "0"][month < 10] + str(month) + "0111")
            resultList.append(str(year) + ["", "0"][month < 10] + str(month) + "1511")
            month += 1
        year += 1

    return list(map(lambda x: str(x), resultList))


def lastday_of_month(month: str) -> str:
    """输入 202202
    输出 20220228
    """
    n = int(month)
    n += 1
    s = str(n)
    if s.endswith("13"):
        s = str(int(month[:4]) + 1) + "010112"
    else:
        s = s + "0112"

    nextmonth1 = any2unix(s, timeFormat="%Y%m%d%H")
    if nextmonth1 is None:
        return ""
    return unix2str(nextmonth1 - 24 * 3600)[:8]


def nearest_saturday() -> str:
    """
    返回离当前日期最近的周六的日期，格式为 'YYYYMMDD' 字符串。

    算法说明：
    - 获取今天的日期和星期几（星期一为0，星期日为6）。
    - 计算向前（之前的）和向后（之后的）到周六（5）的天数差。
    - 如果向后差距更小或相等，则返回未来的周六；否则返回过去的周六。
    """
    today = datetime.today().date()
    weekday = today.weekday()  # Monday = 0, ..., Saturday = 5, Sunday = 6
    target = 5  # 目标星期（周六）

    # 计算向后和向前的天数差（使用模7保证结果在0~6之间）
    daysForward = (target - weekday) % 7
    daysBackward = (weekday - target) % 7

    # 根据哪边更近选择日期
    if daysForward <= daysBackward:
        nearest = today + timedelta(days=daysForward)
    else:
        nearest = today - timedelta(days=daysBackward)

    return nearest.strftime("%Y%m%d")


if __name__ == "__main__":
    print(nearest_saturday())
    pass
