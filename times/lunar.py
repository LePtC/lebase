from lebase.times.format import str2unix, unix2str
from lebase.strings import mma_replace
# from lefile.csv import csv_get  # TODO lebase 这种底层函数需要消除对 lefile 这种较上层的依赖？

LUNAR = None
week_eng2chs = {"Mon": "一", "Tue": "二", "Wed": "三", "Thu": "四", "Fri": "五", "Sat": "六", "Sun": "日"}


def csv_get(path):
    """
    读取csv文件，返回二维list
    """
    import csv
    with open(path, encoding="utf-8") as f:
        return list(csv.reader(f))


def str2info(s, path="lunar.csv"):
    """
    8位字符串时间转狸子日程用 info（周几，农历，节日，几岁）
    :param s: 8位日期字符串（如20220101）
    :param path: lunar.csv 路径，默认当前目录
    :return: [周几, 农历/节日]，如 ['六', '腊月廿九']
    """
    global LUNAR
    if LUNAR is None:
        li = csv_get(path)

        def f(a, b):
            return a if b in a else b

        LUNAR = {x[0].replace(".", ""): f(x[1], x[2]) for x in li}
    if LUNAR.get(str(s), ""):
        t = str2unix(str(s))
        w = mma_replace(unix2str(t, "%a"), week_eng2chs).replace("周", "")
        ret = [w, LUNAR.get(str(s), "")]
        return ret
    else:
        return []
