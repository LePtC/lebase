import os
from typing import Dict, List, Tuple

from lebase.strings import replace_rule
from lebase.times.format import any2unix, unix2str
from lefile.csv import read_csv
from lelog.logs import log

dicLunar: Dict[str, str] = {}
dicHoliday: Dict[str, List[str]] = {}

weekEngToChs: Dict[str, str] = {
    "Mon": "一",
    "Tue": "二",
    "Wed": "三",
    "Thu": "四",
    "Fri": "五",
    "Sat": "六",
    "Sun": "日",
}  # TODO 这个跟format里定义的不一样……


# 只在首次调用时加载农历数据
def load_lunar() -> None:
    """
    加载农历数据
    """
    global dicLunar
    global dicHoliday
    if not dicLunar or not dicHoliday:
        # 假设 lunar.csv 就在当前目录
        path = os.path.join(os.path.dirname(__file__), "lunar.csv")
        # path = lev.fac / "lebase/times/lunar.csv"
        nongli = read_csv(path)

        if not dicLunar:

            def f(a: str, b: str) -> str:
                return a if b in a else b

            dicLunar = {x[0].replace(".", ""): f(x[1], x[2]) for x in nongli}

        if not dicHoliday:
            dicHoliday = {x[0]: x[1:] for x in nongli}


def str2lunar(dateStr: str) -> List[str]:
    """
    8位字符串时间转狸子日程用 info（周几，农历，节日，几岁）

    Args:
        dateStr: 8位日期字符串（如20220101）

    Returns:
        List[str]: [周几, 农历/节日]，如 ['六', '腊月廿九']
    """
    global dicLunar
    if not dicLunar:
        load_lunar()

    if dicLunar.get(str(dateStr), ""):
        t = any2unix(str(dateStr))
        if t is not None:
            w = replace_rule(str(unix2str(t, "%a")), weekEngToChs).replace("周", "")
            ret = [w, dicLunar.get(str(dateStr), "")]
            return ret
    return []


def get_lunar_holiday(now: float) -> Tuple[str, str]:
    """
    获取农历节日信息

    Args:
        now: 时间戳

    Returns:
        Tuple[str, str]: (农历日期, 节日信息)
    """
    global dicHoliday
    if not dicHoliday:
        load_lunar()

    lunar = dicHoliday.get(unix2str(now, "%Y.%m.%d"), ["未查到"])

    holidayList = lunar[1].split(" ")
    lunarDate = lunar[0]

    holiday = "、"
    for x in holidayList:
        if "节" in x or "日" in x or "清明" in x or "除夕" in x:
            holiday += x + "、"
    holiday = holiday[1:-1]
    if holiday:
        holiday += "，"
    log.info(f"{lunarDate} {holiday}")
    return lunarDate, holiday


if __name__ == "__main__":
    print(str2lunar("20220101"))

    import time

    now = time.time()
    get_lunar_holiday(now)
