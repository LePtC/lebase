# -*- coding: utf-8 -*-
"""
日期区间与推算相关函数
"""
from datetime import datetime, timedelta
from lebase.times.format import any2unix, unix2str, any2taskId, unix2taskId


def convert_days_ago(days_string):
    """应对newbing或B站智能把近期时间自动转x天前"""
    days = int(days_string.split("天前")[0])  # 提取天数
    new_date = datetime.now() - timedelta(days=days)  # 计算新日期
    return new_date.timetuple()  # .strftime("%Y年%m月%d日")  # 返回格式化的日期


def cal_day_diff(stime, stime2):
    return int((any2unix(stime) - any2unix(stime2)) / 8640) / 10


def taskId2ndayago(stime: str, days: float):
    """
    str2str(shifted) 时间平移函数
    在氘化氢 BYK 和 pyfac 里曾叫 few_days_ago
    """
    return unix2taskId(any2unix(stime) - 3600 * 24 * days)


def time_str_list(t_start: str, t_end: str, interval=12):
    """
    根据起止时间,间隔生成字符串时间的列表
    :param t_start: 开始时间
    :param t_end: 结束时间
    :param interval: 间隔（小时），默认为12。
    :return: 包含两端，每隔 interval 个小时的时间列表。
    >>> time_str_list('2020040611',"2020040723")
    ['2020040611', '2020040623', '2020040711', '2020040723']
    """
    # 字符串时间转unix时间
    u_start, u_end = any2unix(t_start), any2unix(t_end)
    # 生成时间列表
    time_list = range(int(u_start), int(u_end) + 1, interval * 3600)
    # 转换回字符串格式
    ret = [any2taskId(unix2str(_)) for _ in time_list]
    return ret


def get_liTaskId_halfmonth(yyyy_start, mm_start, yyyy_end, mm_end):
    """
    输入：起止年月
    输出：半月精度的 timelist
    """
    li = []
    yyyy = yyyy_start
    while yyyy <= yyyy_end:
        mm = 1
        if yyyy == yyyy_start:
            mm = mm_start
        mm_end_cur = 12
        if yyyy == yyyy_end:
            mm_end_cur = mm_end
        while mm <= mm_end_cur:
            li.append(str(yyyy) + ["", "0"][mm < 10] + str(mm) + "0111")
            li.append(str(yyyy) + ["", "0"][mm < 10] + str(mm) + "1511")
            mm += 1
        yyyy += 1

    return list(map(lambda x: str(x), li))


def lastday_of_month(month):
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

    nextmonth1 = any2unix(s, form="%Y%m%d%H")
    return unix2str(nextmonth1 - 24 * 3600)[:8]


def nearest_saturday():
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
    days_forward = (target - weekday) % 7
    days_backward = (weekday - target) % 7

    # 根据哪边更近选择日期
    if days_forward <= days_backward:
        nearest = today + timedelta(days=days_forward)
    else:
        nearest = today - timedelta(days=days_backward)

    return nearest.strftime("%Y%m%d")


if __name__ == "__main__":

    # ----------------------------
    # 测试
    # ----------------------------

    print(nearest_saturday())

    pass
