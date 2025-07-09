import os

from lebase.log import log
from lebase.strings import mma_replace
from lebase.times.format import any2unix, unix2str
from lefile.csv import csv_get

dicNongli = {}
dicHoliday = {}

week_eng2chs = {"Mon": "一", "Tue": "二", "Wed": "三", "Thu": "四", "Fri": "五", "Sat": "六", "Sun": "日"}  # TODO 这个跟format里定义的不一样……

# 只在首次调用时加载农历数据


def load_lunar():
    global dicNongli
    global dicHoliday
    if not dicNongli or not dicHoliday:
        # 假设 lunar.csv 就在当前目录
        path = os.path.join(os.path.dirname(__file__), "lunar.csv")
        # path = lev.fac / "lebase/times/lunar.csv"
        nongli = csv_get(path)

        if not dicNongli:

            def f(a, b):
                return a if b in a else b

            dicNongli = {x[0].replace(".", ""): f(x[1], x[2]) for x in nongli}

        if not dicHoliday:
            dicHoliday = {x[0]: x[1:] for x in nongli}


def str2lunar(s):
    """
    8位字符串时间转狸子日程用 info（周几，农历，节日，几岁）
    :param s: 8位日期字符串（如20220101）
    :param path: lunar.csv 路径，默认当前目录
    :return: [周几, 农历/节日]，如 ['六', '腊月廿九']
    """
    global dicNongli
    if not dicNongli:
        load_lunar()

    if dicNongli.get(str(s), ""):
        t = any2unix(str(s))
        w = mma_replace(str(unix2str(t, "%a")), week_eng2chs).replace("周", "")
        ret = [w, dicNongli.get(str(s), "")]
        return ret
    else:
        return []


def get_lunar_holiday(now):
    global dicHoliday
    if not dicHoliday:
        load_lunar()

    lunar = dicHoliday.get(unix2str(now, form="%Y.%m.%d"), ["未查到"])
    # lunar = dicHoliday.get("2022.09.10", ['未查到'])

    holidayli = lunar[1].split(" ")
    lunar = lunar[0]

    holiday = "、"
    for x in holidayli:
        if "节" in x or "日" in x or "清明" in x or "除夕" in x:
            holiday += x + "、"
    holiday = holiday[1:-1]
    if holiday:
        holiday += "，"
    log.info(f"{lunar} {holiday}")
    return lunar, holiday


if __name__ == "__main__":

    print(str2lunar("20220101"))

    import time
    now = time.time()
    get_lunar_holiday(now)
