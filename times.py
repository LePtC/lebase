# -*- coding: utf-8 -*-
"""
用途：时间字符串格式转换库
狸子要处理的时间格式有这几种：unix (float)、str (taskId)、chs（中文时间）、tuple（很少用到）
app 用到的：taskId（半日爬虫）、fsid（filesystem）、str2info（笔记农历）
"""

import random
import re
import time
from datetime import date, datetime
from datetime import time as datetime_time
from datetime import timedelta

import dateparser
from dateutil import parser as dtParser

from lebase.log import log
from lebase.safes import ensure_num, ensure_numstr
from lebase.strings import mma_replace

# ----------------------------
# 万能格式转换
# ----------------------------

"""
写一个python函数any2unix，传入一个时间变量（可能是字符串、int、float、tuple、DateTime对象等等），返回unixtime时间戳（浮点数，秒制而非毫秒，系统当地时区，通常是UTC+8），传入的字符串可能是很多格式的，还可能包含少量无关字符串，包括且不限于以下几种：

2025020311（yyyymmddhh）
20250203113000
20250203113000.000
20250203（缺省时间的情况下时间赋为当天中午12点）
250203
2025年2月3日
25年2月3日
25年2月3
25年.0203
2023年10月5日 14時48分
现在（需结合系统时间识别）
5 hours ago
Tomorrow noon
Next Monday 9:00 AM
Epoch + 1696502880 seconds
2023-W40-5 （周数表示）
Day 278 of 2023 14:48
今天（取现在时间）
昨天（取24小时前时间）
明天
2天前
一周前
去年的今天
25-02-03
25,02,03-11:30
2023-10-05 14:48:00,123（理解为带毫秒）
Feb.3（缺省年份时认为是今年）
5th October 2023 at 2:48pm
October the Fifth, Twenty Twenty-Three
🔵 2023 ✨ 10 🍁 5 ⏰ 14:48 🔚
2024-07-03 08:15:00
UTC2024-07-03T08:15:00Z
2024-07-03 08:15:00Z
10/05/2023 02:48 PM
05/10/2023 14:48
05.10.2023 14:48
1700000000（unixtime的字符串化）
1700000000000（还有可能传入毫秒制的unixtime，当存在歧义时，取更接近当前时间的解释）
"@1696502880" （带符号的时间戳）

注：时间字符串的前后还可能包含一些与时间无关的文本，你需要学会从文本中提取时间部分

你认为能否在一个函数中支持识别以上所有格式？有没有可能发生歧义或无法解读？请先举例分析，然后给出解决方案，最后编码实现

- 代码要求：
    - 代码规范：变量名采用简短明了的小驼峰式命名，函数名则保持`snake_case`风格。
    - 模块化设计：独立的功能尽量抽取为独立的函数，避免将过多功能写在一个函数中。
    - 日志记录：使用`log.info(string)`、`log.warn(string)`函数进行日志输出（已由 from lebase.log import log 模块提供）。
    - 注释和文档：代码中添加必要的中文注释，提供中文的说明文档。
    - 示例用例：提供各类场景的demo示例，演示程序的使用方法和效果。
    - 尽量使用现成库函数，遵循最佳实践
"""


def convert_to_unix(dt):
    """
    将 datetime 对象转换为 Unix 时间戳（秒）
    如果 dt 为 tz-aware，则直接调用 .timestamp()，
    否则假定为系统本地时间。
    """
    if dt.tzinfo is not None:
        return dt.timestamp()
    else:
        return time.mktime(dt.timetuple()) + dt.microsecond / 1e6


def parse_by_regex(text):
    """
    利用正则表达式匹配常见的纯数字日期格式：
        - 14 位: YYYYMMDDHHMMSS（可带小数部分）
        - 12 位: YYYYMMDDHHMM
        - 10 位: YYYYMMDDHH（需判断年份是否合理）
        - 8 位:  YYYYMMDD（缺省时间默认中午12点）
        - 6 位:  YYMMDD（默认补全年份，并设置为中午12点）
    返回 datetime 对象（若能成功解析），否则返回 None。
    """
    patterns = [
        (r"(\d{14})(\.\d+)?", "ymdhms"),
        (r"(\d{12})", "ymdhm"),
        (r"(\d{10})", "ymdh"),
        (r"(\d{8})", "ymd"),
        (r"(\d{6})", "yymmdd"),
    ]
    for pattern, fmt in patterns:
        m = re.search(pattern, text)
        if m:
            numStr = m.group(1)
            try:
                if fmt == "ymdhms":
                    year = int(numStr[0:4])
                    month = int(numStr[4:6])
                    day = int(numStr[6:8])
                    hour = int(numStr[8:10])
                    minute = int(numStr[10:12])
                    second = int(numStr[12:14])
                    micro = 0
                    if m.group(2):
                        # 小数部分转换为微秒
                        frac = float(m.group(2))
                        micro = int(round(frac * 1e6))
                    return datetime(year, month, day, hour, minute, second, micro)
                elif fmt == "ymdhm":
                    year = int(numStr[0:4])
                    month = int(numStr[4:6])
                    day = int(numStr[6:8])
                    hour = int(numStr[8:10])
                    minute = int(numStr[10:12])
                    return datetime(year, month, day, hour, minute, 0)
                elif fmt == "ymdh":
                    year = int(numStr[0:4])
                    month = int(numStr[4:6])
                    day = int(numStr[6:8])
                    hour = int(numStr[8:10])
                    # 判断年份等是否合理
                    if 1900 <= year <= 2100 and 1 <= month <= 12 and 1 <= day <= 31 and hour < 24:
                        return datetime(year, month, day, hour, 0, 0)
                    # 若不合理，则可能应按 Unix 时间戳处理
                elif fmt == "ymd":
                    year = int(numStr[0:4])
                    month = int(numStr[4:6])
                    day = int(numStr[6:8])
                    # 默认时间设为中午 12 点
                    return datetime(year, month, day, 12, 0, 0)
                elif fmt == "yymmdd":
                    year = int(numStr[0:2])
                    # 若年份小于 70，则认为是 2000 年，否则 1900 年
                    if year < 70:
                        year += 2000
                    else:
                        year += 1900
                    month = int(numStr[2:4])
                    day = int(numStr[4:6])
                    return datetime(year, month, day, 12, 0, 0)
            except Exception:  # as e:
                # log.warn("正则解析日期失败: " + str(e))
                continue
    return None


def parse_special_format(text):
    """
    处理特殊格式，如：
      - "Day 278 of 2023 14:48"：解析为2023年的第278天，带时间部分
      - "2023-W40-5"：ISO周数表示法，默认时间为中午12点；若有时间信息则解析之
      - "去年的今天"：取当前时间的去年的对应日期（若当天为2月29日则采用平年日期）
      - "一周前"：当前时间减去一周
    返回 datetime 对象（若能成功解析），否则返回 None。
    """
    # 处理 "Day 278 of 2023 14:48" 格式（忽略大小写）
    m = re.search(r"Day\s+(\d+)\s+of\s+(\d{4})(.*)", text, re.IGNORECASE)
    if m:
        try:
            dayOfYear = int(m.group(1))
            year = int(m.group(2))
            timePart = m.group(3).strip()
            # 根据年初日期加上 dayOfYear-1 天
            baseDate = datetime(year, 1, 1) + timedelta(days=dayOfYear - 1)
            # 尝试解析时间部分，例如 "14:48" 或 "14時48分"
            if timePart:
                mTime = re.search(r"(\d{1,2}):(\d{1,2})(?::(\d{1,2}))?", timePart)
                if mTime:
                    hour = int(mTime.group(1))
                    minute = int(mTime.group(2))
                    second = int(mTime.group(3)) if mTime.group(3) else 0
                    baseDate = baseDate.replace(hour=hour, minute=minute, second=second)
                else:
                    mTime2 = re.search(r"(\d{1,2})[時:：](\d{1,2})", timePart)
                    if mTime2:
                        hour = int(mTime2.group(1))
                        minute = int(mTime2.group(2))
                        baseDate = baseDate.replace(hour=hour, minute=minute)
            else:
                baseDate = baseDate.replace(hour=12, minute=0, second=0)
            return baseDate
        except Exception as e:
            log.warn("解析 'Day xxx of yyyy' 格式失败: " + str(e))

    # 处理 "2023-W40-5" 格式
    m = re.search(r"(\d{4})-W(\d{1,2})-(\d)", text)
    if m:
        try:
            year = int(m.group(1))
            week = int(m.group(2))
            weekday = int(m.group(3))
            dtDate = date.fromisocalendar(year, week, weekday)
            dtObj = datetime.combine(dtDate, datetime_time(12, 0, 0))
            # 检查是否附带时间信息
            remaining = text[m.end() :].strip()
            if remaining:
                mTime = re.search(r"(\d{1,2}):(\d{1,2})(?::(\d{1,2}))?", remaining)
                if mTime:
                    hour = int(mTime.group(1))
                    minute = int(mTime.group(2))
                    second = int(mTime.group(3)) if mTime.group(3) else 0
                    dtObj = dtObj.replace(hour=hour, minute=minute, second=second)
                else:
                    mTime2 = re.search(r"(\d{1,2})[時:：](\d{1,2})", remaining)
                    if mTime2:
                        hour = int(mTime2.group(1))
                        minute = int(mTime2.group(2))
                        dtObj = dtObj.replace(hour=hour, minute=minute)
            return dtObj
        except Exception as e:
            log.warn("解析 'YYYY-Www-d' 格式失败: " + str(e))

    # 处理 "去年的今天"
    if "去年的今天" in text:
        try:
            nowDt = datetime.now()
            try:
                dtObj = nowDt.replace(year=nowDt.year - 1)
            except ValueError:
                # 处理2月29日等问题，简单减去365天
                dtObj = nowDt - timedelta(days=365)
            return dtObj
        except Exception as e:
            log.warn("解析 '去年的今天' 失败: " + str(e))

    # 处理 "一周前"
    if "一周前" in text:
        try:
            nowDt = datetime.now()
            dtObj = nowDt - timedelta(weeks=1)
            return dtObj
        except Exception as e:
            log.warn("解析 '一周前' 失败: " + str(e))

    # 未匹配到特殊格式，返回 None
    return None


def any2unix(timeVar, form=""):
    """
    将任意格式的时间变量转换为 Unix 时间戳（秒）。
    支持的类型包括：datetime对象、数字、元组、字符串等。
    对于字符串，优先通过正则匹配常见数字格式，再采用 dateparser 或 dateutil.parser 解析。
    返回系统当地时区（通常为 UTC+8）的 Unix 时间戳（浮点数，单位秒）。

    支持的字符串格式包括但不限于：
        - 纯数字日期格式：2025020311、20250203113000、20250203（缺省时间默认中午12点）、250203 等
        - 中文日期格式：2025年2月3日、25年2月3日、今天、昨天、明天、去年的今天 等
        - 英文自然语言：5 hours ago、Tomorrow noon、Next Monday 9:00 AM、5th October 2023 at 2:48pm 等
        - 带有额外文本或特殊符号的混合字符串
        - Unix 时间戳（秒或毫秒）：1700000000, 1700000000000, "@1696502880" 等
        - 其他特殊格式：ISO 周数、年份中的第几天等

    注意：由于时间表达存在歧义（例如纯数字可能既是日期又是时间戳），在部分场景下可能会产生不同解释，
    本函数采用启发式规则，可能无法覆盖所有边界情况。
    """

    # 1. 如果是 datetime 对象，直接转换
    if isinstance(timeVar, datetime):
        dt = timeVar
        log.debug("输入为 datetime 对象")
        return convert_to_unix(dt)

    # 2. 数字类型：int 或 float
    if isinstance(timeVar, (int, float)):
        candidate = float(timeVar)
        nowTime = time.time()
        # 如果数字远大于当前时间，则可能为毫秒级时间戳
        if candidate > nowTime * 10:
            candidate_sec = candidate / 1000.0
            log.debug("检测到数字为毫秒级时间戳，转换为秒制")
            return candidate_sec
        else:
            # log.debug("检测到数字为秒级时间戳")
            return candidate

    # 3. 元组类型（例如 time.localtime() 返回的元组）
    if isinstance(timeVar, tuple):
        try:
            ts = time.mktime(timeVar)
            log.debug("从元组转换为时间戳")
            return float(ts)
        except Exception as e:
            log.warn("无法将元组转换为时间戳: " + str(e))
            return None

    # 4. 字符串类型
    if isinstance(timeVar, str):
        text = timeVar.strip()
        if not text:
            log.warn("空字符串无法解析")
            return None

        # log.debug("解析字符串: " + text)
        if form:
            return str2unix(timeVar, form)

        # 去除可能的前导 '@'
        if text.startswith("@"):
            text = text[1:].strip()

        # 处理 "Epoch + 1696502880 seconds" 这类格式
        epochMatch = re.search(r"(?i)epoch.*?(\d+)", text)
        if epochMatch:
            num = epochMatch.group(1)
            try:
                candidate = float(num)
                nowTime = time.time()
                if candidate > nowTime * 10:
                    candidate = candidate / 1000.0
                log.debug("从 Epoch 格式中解析到时间戳")
                return candidate
            except Exception as e:
                log.warn("从 Epoch 格式解析失败: " + str(e))

        # 优先尝试正则匹配数字日期格式
        dt = parse_by_regex(text)
        if dt:
            # log.debug("通过正则表达式解析到日期: " + dt.strftime("%Y-%m-%d %H:%M:%S"))
            return convert_to_unix(dt)

        # 如果字符串为纯数字（可能为 Unix 时间戳）
        numericMatch = re.fullmatch(r"\d+(\.\d+)?", text)
        if numericMatch:
            try:
                candidate = float(text)
                nowTime = time.time()
                if candidate > nowTime * 10:
                    candidate_sec = candidate / 1000.0
                    log.debug("检测到纯数字为毫秒级时间戳，转换为秒制")
                    return candidate_sec
                else:
                    log.debug("检测到纯数字为秒级时间戳")
                    return candidate
            except Exception as e:
                log.warn("纯数字转换为时间戳失败: " + str(e))

        # 尝试使用特殊格式解析（覆盖 Day xxx, YYYY-Www-d, 去年的今天, 一周前 等）
        specialDt = parse_special_format(text)
        if specialDt is not None:
            log.info("通过自定义规则解析到日期: " + specialDt.strftime("%Y-%m-%d %H:%M:%S"))
            return convert_to_unix(specialDt)

        # 尝试使用 dateparser 解析（支持中文及自然语言描述）
        dt = None
        if dateparser is not None:
            try:
                dt = dateparser.parse(text, settings={"TIMEZONE": "Asia/Shanghai", "RETURN_AS_TIMEZONE_AWARE": False})
            except Exception as e:
                log.warn("dateparser 解析异常: " + str(e))
        else:
            log.warn("未安装 dateparser 库，跳过该解析步骤")

        # 如果 dateparser 未解析成功，尝试 dateutil.parser
        if not dt and dtParser is not None:
            try:
                dt = dtParser.parse(text, fuzzy=True)
            except Exception as e:
                log.warn("dateutil.parser 解析异常: " + str(e))
                return None

        if not dt:
            log.warn("无法解析时间字符串: " + text)
            return None

        # 如果解析结果仅包含日期（时分秒均为 0），且原字符串中不包含明显的时间信息，则默认设为中午 12 点
        if dt.hour == 0 and dt.minute == 0 and dt.second == 0:
            if not re.search(r"[\d:时分]", text):
                dt = dt.replace(hour=12, minute=0, second=0)
                log.debug("仅解析到日期，默认设置为中午 12 点")

        log.debug("通过解析器解析到日期: " + dt.strftime("%Y-%m-%d %H:%M:%S"))
        return convert_to_unix(dt)

    log.warn("无法识别的时间类型: " + str(type(timeVar)))
    return None


# 兼容指定 format 的字符串转换为 Unix 时间戳


def str2tuple(stime, form=""):
    """字符串时间转为元组时间"""
    s = str(stime)
    return time.strptime(s, form)


def str2unix(stime, form=""):
    """字符串时间转unix时间"""
    s = str(stime)
    return int(time.mktime(str2tuple(s, form)))


# ----------------------------
# taskId 涉及自定义的半日量化
# ----------------------------


def any2taskId(anytime, length=10):
    """
    任意格式智能识别然后转 taskId
    替换原 any2taskId、str2taskId
    """
    return unix2taskId(any2unix(anytime))


def is_taskId(f):
    """
    注：只认 8 位数且 11 点触发的是 taskId
    """
    return re.match(r"^20\d{8}$", f) and (f.endswith(("11", "23")))


def is_rtime(s):
    if any2unix("2017123123") < any2unix(s) < any2unix("2099123123"):
        return True
    else:
        return False


def filt_rtime(dic):
    for x in dic:
        if isinstance(dic[x], (float, int)):
            if is_rtime(dic[x]):
                dic[x] = unix2chs(dic[x])
    return dic


# ----------------------------
# unix 转成各种
# ----------------------------


def unix2str(ftime_="", form="%Y%m%d%H%M%S"):
    """unix时间转字符串时间"""
    # return time.strftime(form.encode('unicode_escape').decode('utf8'),
    #   time.localtime(ftime)).encode('utf-8').decode('unicode_escape')
    if not ftime_:
        ftime = time.time()
    else:
        ftime = ftime_
    tm = any2unix(ftime)
    try:
        if tm > 0:
            return time.strftime(form, time.localtime(tm))
        else:
            return "0"
    except Exception as e:
        print(f"unix2str({ftime}, {form}) error: {e}")
        # sys.exit()


def unix2taskId(rtime=0, offset=0):
    """
    按半天量化为 11 点或 23 点（从10~22点都属于11am，22~10属于23pm）
    offset 以天为单位
    输出：10 位 taskId 字符串
    注：此函数在原来的项目里叫 ds_belong
    202207 发现bug，不能写作 rtime=time.time() 会导致此参数不动态更新
    """
    if rtime <= 0:
        rtime_ = time.time()
    else:
        rtime_ = rtime

    tm = rtime_ + offset * 3600 * 24
    now = time.localtime(tm)
    hour = int(time.strftime("%H", now))
    if 9 <= hour < 21:
        hourt = 11
    else:
        hourt = 23
    if hour < 9:
        return time.strftime("%Y%m%d", time.localtime(tm - 3600 * 12)) + str(hourt)
    else:
        return time.strftime("%Y%m%d", now) + str(hourt)


def unix2chsp(ftime: float):
    """unix时间转中文上下午"""
    hour = int(unix2str(ftime, form="%H"))
    if 4 <= hour <= 6:
        return "凌晨"
    elif 7 <= hour <= 11:
        return "早上"
    elif 12 <= hour <= 14:
        return "中午"
    elif 15 <= hour <= 18:
        return "下午"
    elif 19 <= hour <= 23:
        return "晚上"
    else:
        return "深夜"


# 中文时间 -----------

week_eng2chs = {
    "Mon": "周一",
    "Tue": "周二",
    "Wed": "周三",
    "Thu": "周四",
    "Fri": "周五",
    "Sat": "周六",
    "Sun": "周日",
    "11时": "昼",
    "23时": "夜",
}
# rule_eng2chs = {'yyyy':'%Y','mm':'%m','dd':'%d',
#   'hh':'%H','mm':'%M','周w':'%a'}


def taskId2fmt(tm):
    return tm[:4] + "." + tm[4:6] + "." + tm[6:8] + "-" + tm[8:]


def taskId2chs(date, form="%Y年%m月%d日（%a）"):
    # _form = mma_Replace(form, rule_eng2chs)
    s1 = (
        time.strftime(form.encode("unicode_escape").decode("utf8"), any2tuple(date))
        .encode("utf-8")
        .decode("unicode_escape")
    )
    return mma_replace(s1, week_eng2chs)


def unix2chsrq(ftime):
    """unix时间转中文日期，消除占位零"""
    s = unix2str(ftime, "%m月%d日")
    if s.startswith("0"):
        s = s[1:]
    return s.replace("月0", "月")


def unix2chssk(ftime):
    """unix时间转中文时刻，消除占位零"""
    s = unix2str(ftime, "%H点%M分")
    if s.startswith("0"):
        s = s[1:]
    return s  # .replace("点0","点")


def unix2chs(ftime_=""):
    if not ftime_:
        ftime = time.time()
    else:
        ftime = ftime_
    t = ensure_num(ftime)  # + 8*3600
    s = unix2str(t, "%Y年")
    # return s+unix2chsrq(t)+' '+unix2chssk(t)
    return s + unix2chsrq(t) + " " + unix2str(t, "%H:%M:%S")


def unix2fsid(unix_time):
    millisecond = int(unix_time * 100) % 100
    str_millisecond = f"{millisecond:02d}"
    return int(unix2str(unix_time, form="%Y%m%d%H%M%S") + str_millisecond)


# 纯数字字符串时间转成各种 -----------


def any2tuple(stime):
    """字符串时间转为元组时间"""
    return time.localtime(any2unix(stime))


def convert_days_ago(days_string):
    """应对newbing或B站智能把近期时间自动转x天前"""
    days = int(days_string.split("天前")[0])  # 提取天数
    new_date = datetime.now() - timedelta(days=days)  # 计算新日期
    return new_date.timetuple()  # .strftime("%Y年%m月%d日")  # 返回格式化的日期


def cal_day_diff(stime, stime2):
    return int((any2unix(stime) - any2unix(stime2)) / 8640) / 10


# ----------------------------
# 时间工具
# ----------------------------


def taskId2ndayago(stime: str, days: float):
    """
    str2str(shifted) 时间平移函数
    在氘化氢 BYK 和 pyfac 里曾叫 few_days_ago
    """
    return unix2taskId(any2unix(stime) - 3600 * 24 * days)


# strstr2str_list
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


def convert_to_timestamp(filename):
    # 使用正则表达式查找日期
    match = re.search(r"(\d{8})", filename)
    if match:
        # 将日期字符串转换为datetime对象
        date_str = match.group(1)
        date_obj = datetime.strptime(date_str, "%Y%m%d")

        # 将datetime对象转换为Unix时间戳
        timestamp = int(time.mktime(date_obj.timetuple())) + 12 * 3600
        return timestamp
    else:
        return "日期格式不正确"


# ----------------------------
# 常用 format
# ----------------------------


def logtime(now=None):
    if now is not None:
        __now = now
    else:
        __now = time.localtime(time.time())
    return time.strftime("%m/%d %H:%M:%S", __now)


# ----------------------------
# timing
# ----------------------------


class Clock:

    borntime = 0
    withtime = 0
    name = "未命名"

    def __init__(self, processname="未命名"):
        self.name = processname  # 是否需要 ensure.st(processname)？
        self.borntime = time.time()

    def __enter__(self):
        self.withtime = time.time()
        log.info(f"开始：{self.name}")
        return self

    def __exit__(self, type, value, trace):
        log.info(f"完毕：{self.name}（用时：{ensure_numstr(time.time() - self.withtime)} s）")


# ----------------------------
# progress logger
# ----------------------------


def print_progress(start_time, countNum, totalNum, detail=""):

    elapsed_time = int(time.time() - start_time)
    remaining_time = ((totalNum - countNum) / countNum) * elapsed_time if countNum else 0

    percentage = (countNum / totalNum) * 100 if totalNum else 0
    textProgress = f"{countNum} / {totalNum} ({percentage:.1f}%) T: {elapsed_time} / {remaining_time:.0f} s {detail}"
    print(f"\r{textProgress}", end="", flush=True)

    return textProgress


class Progress:
    """
    进度打印日志类，通过 with 语法管理进度记录的开始、更新和结束。

    Attributes:
        totalNum (int): 总任务数量
        startTime (float): 任务开始时的时间戳
        countNum (int): 当前已处理的任务数量
        printStep (int): 每隔多少步打印一次进度信息
    """

    def __init__(self, totalNum, msg="", printStep=1, logStep=0):
        """
        初始化进度日志对象。

        Args:
            totalNum (int): 总任务数量
            msg (str): 开始时输出的日志信息
            printStep (int): 每隔多少步打印一次进度信息，缺省值为1
            logStep (int): 在 printStep 基础上，每隔多少个 printStep 打印一次进度信息，缺省值为0（关闭）
        """
        self.totalNum = totalNum
        self.msg = msg
        self.printStep = printStep if printStep > 0 else 1  # 确保 printStep 为正整数
        self.logStep = logStep
        self.startTime = time.time()
        self.countNum = 0
        # 输出开始日志信息
        log.info("开始 " + msg + " ...")

    def __enter__(self):
        """
        进入 with 语句时调用，返回对象自身。
        """
        return self

    def tik(self, detail=""):
        """
        更新进度，计数器加一，并根据 printStep 判断是否打印当前进度信息。
        注意：若总任务数无法整除 printStep，仍保证最后一次进度（100%）能打印出来。

        Args:
            detail (str): 当前任务的详细描述信息
        """
        self.countNum += 1
        # 只有当步数是 printStep 的整数倍或者完成最后一步时，才打印进度信息
        if (self.countNum % self.printStep == 0) or (self.countNum == self.totalNum):
            msg = self.print_progress(detail)
            if self.logStep > 0:
                if (self.countNum // self.printStep % self.logStep == 0) or (self.countNum == self.totalNum):
                    print("")  # 换行
                    log.info(msg)

    def fin(self, detail=""):
        """
        适用于 batchSize 不整除时最后批上传后直接完成？
        """
        self.countNum = self.totalNum - 1
        self.tik(detail)

    def print_progress(self, detail=""):
        """
        打印当前进度信息，包括已处理数量、总数量、百分比、已用时间和估计剩余时间。

        Args:
            detail (str): 当前任务的详细描述信息
        """
        elapsedTime = int(time.time() - self.startTime)
        remainingTime = int(self.calc_remaining_time(elapsedTime, self.countNum, self.totalNum))
        percentage = self.calc_percentage(self.countNum, self.totalNum)
        textProgress = (
            f"{self.countNum} / {self.totalNum} "
            f"({percentage:.1f}%) T: {elapsedTime} / {remainingTime} s "
            f"{detail}"
        )
        # \r 回到行首，end="" 不换行，flush 确保实时输出
        print(f"\r{textProgress}", end="", flush=True)
        return textProgress

    @staticmethod
    def calc_remaining_time(elapsedTime, countNum, totalNum):
        """
        计算估计的剩余时间。

        Args:
            elapsedTime (int): 已用时间（秒）
            countNum (int): 当前已处理任务数
            totalNum (int): 总任务数

        Returns:
            float: 估计剩余时间（秒）
        """
        if countNum:
            return ((totalNum - countNum) / countNum) * elapsedTime
        else:
            return 0

    @staticmethod
    def calc_percentage(countNum, totalNum):
        """
        计算已处理任务的百分比。

        Args:
            countNum (int): 当前已处理任务数
            totalNum (int): 总任务数

        Returns:
            float: 完成百分比
        """
        if totalNum:
            return (countNum / totalNum) * 100
        else:
            return 0

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        离开 with 语句时调用，输出结束日志和换行符。
        如果在任务处理中发生异常，则记录警告日志。

        Args:
            exc_type: 异常类型
            exc_val: 异常值
            exc_tb: 异常追踪信息
        """
        # 输出换行符，确保终端输出整洁
        print("")
        elapsedTime = time.time() - self.startTime
        if exc_type:
            # 如果出现异常，则记录警告日志
            log.warn(f"任务：{self.msg} 异常终止，用时：{elapsedTime:.1f} s")
        else:
            log.success(f"任务：{self.msg} 成功完成，用时：{elapsedTime:.1f} s")


"""
写一个python类来保障运行间隔的最低时长，入参minTime、plusRandom，负责sleep(minTime+plusRandom) 单位为秒
plusRandom要乘以0~1范围随机数，可以缺省，缺省值为0
提供with的调用方法，把代码块本身运行时间也考虑进来，如果代码块本身运行时间 > 计划的(minTime+plusRandom) 则无需再添加sleep
- 代码要求：
    - 代码风格统一，变量名采用简短明了的小驼峰式命名，函数名则保持`snake_case`风格。
    - 提高代码的可读性和可维护性，添加必要的中文注释，提供中文的说明文档。
    - 日志记录：使用`log.info(string)`、`log.warn(string)`函数进行日志输出（已由 from lebase.log import log 模块提供）。
    - 示例用例：提供各类场景的demo示例，演示程序的使用方法和效果。
    - 尽量使用现成库函数，遵循最佳实践
"""


class SleepGuard:
    """
    运行间隔保障类，用于确保两次操作之间至少间隔指定的时间（包含一定随机性）。

    参数:
        minTime: 最低运行间隔时间（单位：秒）。
        plusRandom: 额外时间随机增量（单位：秒），在实际间隔时间中会乘以0~1范围内的随机数，默认值为0。

    使用方式:
        使用 with 语句调用该类，在退出 with 块时会根据代码块的实际运行时间决定是否需要额外 sleep。

    说明:
        - 进入上下文时记录开始时间。
        - 离开上下文时计算代码块运行的实际时间。
        - 如果实际运行时间小于计划的间隔（minTime + plusRandom*随机数），则调用 sleep 延时剩余时间；
          否则直接返回，不做延时。
    """

    def __init__(self, minTime, plusRandom=0):
        self.minTime = minTime  # 最低运行间隔
        self.plusRandom = plusRandom  # 随机增量
        # 计算计划的总间隔时间（随机因子取值范围 [0,1)）
        self.planTime = self.minTime + self.plusRandom * random.uniform(0, 1)
        log.debug("初始化SleepGuard: planTime = {:.3f}秒".format(self.planTime))
        self.startTime = None

    def __enter__(self):
        # 记录进入上下文的时间
        self.startTime = time.time()
        log.debug("进入SleepGuard上下文，记录开始时间：{:.3f}".format(self.startTime))
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # 计算代码块实际运行时间
        elapsedTime = time.time() - self.startTime
        log.debug("退出SleepGuard上下文，代码块运行时间：{:.3f}秒".format(elapsedTime))
        # 如果运行时间不足计划时间，则休眠剩余时间
        if elapsedTime < self.planTime:
            sleepTime = self.planTime - elapsedTime
            log.info("实际运行时间不足计划时间，休眠 {:.3f} 秒".format(sleepTime))
            time.sleep(sleepTime)
        else:
            log.warn("代码块运行时间超过计划时间，无需休眠")


if __name__ == "__main__":

    # ----------------------------
    # 测试
    # ----------------------------

    test_inputs = [
        #     "2025020311",  # yyyymmddhh
        #     "20250203113000",  # yyyymmddHHMMSS
        #     "20250203113000.000",  # 带小数秒
        #     "20250203",  # 仅日期，默认中午12点
        #     "250203",  # YYMMDD
        #     "2025年2月3日",  # 中文格式
        #     "25年2月3日",  # 两位年份中文
        #     "2023年10月5日 14時48分",  # 带时间的中文格式
        #     "现在",  # 当前时间
        #     "5 hours ago",  # 英文相对时间
        #     "Tomorrow noon",  # 明天中午
        #     "Next Monday 9:00 AM",  # 下周一上午
        #     "Epoch + 1696502880 seconds",  # 包含 Epoch 说明的格式
        #     "2023-W40-5",  # ISO 周数表示（可能需要 dateparser 支持）
        #     "Day 278 of 2023 14:48",  # 年中的第几天
        #     "今天",  # 今天
        #     "昨天",  # 昨天
        #     "明天",  # 明天
        #     "2天前",  # 相对时间中文
        #     "一周前",  # 相对时间中文
        #     "去年的今天",  # 相对描述
        #     "25-02-03",  # 带分隔符的日期
        #     "25,02,03-11:30",  # 带分隔符和时间
        #     "2023-10-05 14:48:00,123",  # 带毫秒
        #     "Feb.3",  # 英文简写，缺省年份认为今年
        #     "5th October 2023 at 2:48pm",  # 英文复杂描述
        #     "October the Fifth, Twenty Twenty-Three",  # 英文文字描述
        #     "🔵 2023 ✨ 10 🍁 5 ⏰ 14:48 🔚",  # 带特殊符号
        #     "2024-07-03 08:15:00",  # 标准格式
        #     "UTC2024-07-03T08:15:00Z",  # 带 UTC 标识
        #     "2024-07-03 08:15:00Z",  # 带 Z 后缀
        #     "10/05/2023 02:48 PM",  # 美式日期
        #     "05/10/2023 14:48",  # 欧式日期
        #     "05.10.2023 14:48",  # 带点分隔
        #     "1700000000",  # Unix 时间戳（秒）
        #     "1700000000000",  # Unix 时间戳（毫秒）
        #     "@1696502880",  # 带 @ 的时间戳
        "2025年03月08日23",  # 识别成23年的bug
        "huaer_fans20250301_100.csv",
        "officalrole20250103_100.csv",
    ]

    for inp in test_inputs:
        ts = any2unix(inp)
        if ts:
            dt_str = datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")
        else:
            dt_str = "解析失败"
        print(f"输入: {inp}\n解析结果: {dt_str}\n{'-' * 40}")

    # print(unix2chs(any2unix("2025年03月08日23", form="%Y年%m月%d日%H")))

    # ----------------------------
    # 测试
    # ----------------------------

    # print(logtime())

    # print(str2taskId("2022年02月03日"))

    # print(unix2str(time.time(), form="%Y.%m.%d"))
    # print(time_str_list("2022011923", "2022012123"))

    # print(unix2chs(time.time()))
    # print(str2info("20210506"))

    # print(str2tuple("5天前"))

    # ----------------------------

    # with Clock(__file__) as ck:
    #     print("Hello")

    # import random

    # def demo_normal_flow():
    #     """
    #     示例1：正常流程的使用方法，模拟处理一系列任务，并实时更新进度信息。
    #     此处设置 printStep=3，即每 3 个任务打印一次进度，最后一步无论如何都会打印。
    #     """
    #     # 模拟任务列表（例如：20 个任务）
    #     someList = [{"name": f"Task{i}"} for i in range(1, 21)]

    #     with Progress(len(someList), f"检查 {len(someList)} 个数据库") as pr:
    #         for task in someList:
    #             time.sleep(random.uniform(0.1, 0.3))  # 模拟任务处理耗时
    #             pr.tik(f"当前任务: {task['name']}")

    # def demo_exception_flow():
    #     """
    #     示例2：处理过程中出现异常的情况，演示如何捕获异常并记录日志。
    #     """
    #     try:
    #         with Progress(totalNum=10, msg="处理 10 个下载", printStep=2, logStep=1) as pr:
    #             for i in range(1, 11):
    #                 time.sleep(0.2)
    #                 # 模拟在第5个任务时抛出异常
    #                 if i == 5:
    #                     raise ValueError("示例异常")
    #                 pr.tik(detail=f"任务{i}")
    #     except Exception as e:
    #         log.warn(f"处理过程中出现异常: {e}")

    # print("===== Demo: 正常流程 =====")
    # demo_normal_flow()
    # print("\n===== Demo: 异常流程 =====")
    # demo_exception_flow()

    # ----------------------------
    # SleepGuard
    # ----------------------------

    # # 示例1：代码块执行时间短于计划间隔
    # log.info("示例1: 代码块执行时间短于计划时间")
    # with SleepGuard(2, 1):  # 计划时间介于2到3秒之间
    #     log.info("执行快速任务")
    #     time.sleep(0.5)  # 模拟任务执行耗时0.5秒

    # # 示例2：代码块执行时间长于计划间隔
    # log.info("示例2: 代码块执行时间长于计划时间")
    # with SleepGuard(2, 1):  # 计划时间介于2到3秒之间
    #     log.info("执行耗时任务")
    #     time.sleep(3)  # 模拟任务执行耗时3秒

    # # 示例3：不使用随机增量（plusRandom缺省）
    # log.info("示例3: plusRandom缺省，仅使用最低间隔")
    # with SleepGuard(2):  # 此时计划时间固定为2秒
    #     log.info("执行任务")
    #     time.sleep(1)  # 模拟任务执行耗时1秒

    # input("按任意键退出 \n ")
    # print(0)
    pass
