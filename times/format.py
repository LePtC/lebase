# -*- coding: utf-8 -*-
"""
用途：时间字符串格式转换库
狸子要处理的时间格式有这几种：unix (float)、str (taskId)、chs（中文时间）、tuple（很少用到）
app 用到的：taskId（半日爬虫）、fsid（filesystem）、str2lunar（笔记农历）

prompt：

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
    - 日志记录：使用`log.info(string)`、`log.warning(string)`函数进行日志输出（已由 from lebase.log import log 模块提供）。
    - 注释和文档：代码中添加必要的中文注释，提供中文的说明文档。
    - 示例用例：提供各类场景的demo示例，演示程序的使用方法和效果。
    - 尽量使用现成库函数，遵循最佳实践
"""

import time
import re
from datetime import datetime, timedelta, date, time as datetime_time
from lebase.log import log
from lebase.safes import ensure_num
from lebase.strings import mma_replace


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
    from dateutil import parser as dtParser
    import dateparser

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
            log.warning("无法将元组转换为时间戳: " + str(e))
            return None

    # 4. 字符串类型
    if isinstance(timeVar, str):
        text = timeVar.strip()
        if not text:
            log.warning("空字符串无法解析")
            return None

        # log.debug("解析字符串: " + text)
        if form:
            return _str2unix(timeVar, form)

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
                log.warning("从 Epoch 格式解析失败: " + str(e))

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
                log.warning("纯数字转换为时间戳失败: " + str(e))

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
                log.warning("dateparser 解析异常: " + str(e))
        else:
            log.warning("未安装 dateparser 库，跳过该解析步骤")

        # 如果 dateparser 未解析成功，尝试 dateutil.parser
        if not dt and dtParser is not None:
            try:
                dt = dtParser.parse(text, fuzzy=True)
            except Exception as e:
                log.warning("dateutil.parser 解析异常: " + str(e))
                return None

        if not dt:
            log.warning("无法解析时间字符串: " + text)
            return None

        # 如果解析结果仅包含日期（时分秒均为 0），且原字符串中不包含明显的时间信息，则默认设为中午 12 点
        if dt.hour == 0 and dt.minute == 0 and dt.second == 0:
            if not re.search(r"[\d:时分]", text):
                dt = dt.replace(hour=12, minute=0, second=0)
                log.debug("仅解析到日期，默认设置为中午 12 点")

        log.debug("通过解析器解析到日期: " + dt.strftime("%Y-%m-%d %H:%M:%S"))
        return convert_to_unix(dt)

    log.warning("无法识别的时间类型: " + str(type(timeVar)))
    return None


def str2tuple(stime, form=""):
    """字符串时间转为元组时间"""
    s = str(stime)
    return time.strptime(s, form)


def _str2unix(stime, form=""):
    """字符串时间转unix时间，仅内部使用，外部应该用any2unix"""
    s = str(stime)
    return int(time.mktime(str2tuple(s, form)))


def unix2str(ftime_=0.0, form="%Y%m%d%H%M%S"):
    """unix时间转字符串时间"""
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
        return "0"


def unix2taskId(rtime=0.0, offset=0.0):
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


def taskId2fmt(tm):
    return tm[:4] + "." + tm[4:6] + "." + tm[6:8] + "-" + tm[8:]


def taskId2chs(date, form="%Y年%m月%d日（%a）"):
    s1 = (
        time.strftime(form.encode("unicode_escape").decode("utf8"), any2tuple(date))
        .encode("utf-8")
        .decode("unicode_escape")
    )
    return mma_replace(s1, week_eng2chs)


def unix2chsrq(ftime):
    s = unix2str(ftime, "%m月%d日")
    if s.startswith("0"):
        s = s[1:]
    return s.replace("月0", "月")


def unix2chssk(ftime):
    s = unix2str(ftime, "%H点%M分")
    if s.startswith("0"):
        s = s[1:]
    return s


def unix2chs(ftime_=0.0):
    if not ftime_:
        ftime = time.time()
    else:
        ftime = ftime_
    t = ensure_num(ftime)
    s = unix2str(t, "%Y年")
    return s + unix2chsrq(t) + " " + unix2str(t, "%H:%M:%S")


def unix2fsid(unix_time):
    millisecond = int(unix_time * 100) % 100
    str_millisecond = f"{millisecond:02d}"
    return int(unix2str(unix_time, form="%Y%m%d%H%M%S") + str_millisecond)


def any2tuple(stime):
    return time.localtime(any2unix(stime))


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
                # log.warning("正则解析日期失败: " + str(e))
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
            log.warning("解析 'Day xxx of yyyy' 格式失败: " + str(e))

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
            log.warning("解析 'YYYY-Www-d' 格式失败: " + str(e))

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
            log.warning("解析 '去年的今天' 失败: " + str(e))

    # 处理 "一周前"
    if "一周前" in text:
        try:
            nowDt = datetime.now()
            dtObj = nowDt - timedelta(weeks=1)
            return dtObj
        except Exception as e:
            log.warning("解析 '一周前' 失败: " + str(e))

    # 未匹配到特殊格式，返回 None
    return None


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


if __name__ == "__main__":

    # ----------------------------
    # 测试
    # ----------------------------

    print(unix2str(time.time(), form="%Y.%m.%d"))

    print(unix2chs(time.time()))

    # print(str2tuple("5天前"))
    # 这个函数只能是 any2unix 的底层，上层应用应使用 unix2tuple(any2unix(input))

    # ----------------------------
    # 测试
    # ----------------------------

    test_inputs = [
        "2025020311",  # yyyymmddhh
        "20250203113000",  # yyyymmddHHMMSS
        "20250203113000.000",  # 带小数秒
        "20250203",  # 仅日期，默认中午12点
        "250203",  # YYMMDD
        "2025年2月3日",  # 中文格式
        "25年2月3日",  # 两位年份中文
        "2023年10月5日 14時48分",  # 带时间的中文格式
        "现在",  # 当前时间
        "5 hours ago",  # 英文相对时间
        "Tomorrow noon",  # 明天中午
        "Next Monday 9:00 AM",  # 下周一上午
        "Epoch + 1696502880 seconds",  # 包含 Epoch 说明的格式
        "2023-W40-5",  # ISO 周数表示（可能需要 dateparser 支持）
        "Day 278 of 2023 14:48",  # 年中的第几天
        "今天",  # 今天
        "昨天",  # 昨天
        "明天",  # 明天
        "2天前",  # 相对时间中文
        "一周前",  # 相对时间中文
        "去年的今天",  # 相对描述
        "25-02-03",  # 带分隔符的日期
        "25,02,03-11:30",  # 带分隔符和时间
        "2023-10-05 14:48:00,123",  # 带毫秒
        "Feb.3",  # 英文简写，缺省年份认为今年
        "5th October 2023 at 2:48pm",  # 英文复杂描述
        "October the Fifth, Twenty Twenty-Three",  # 英文文字描述
        "🔵 2023 ✨ 10 🍁 5 ⏰ 14:48 🔚",  # 带特殊符号
        "2024-07-03 08:15:00",  # 标准格式
        "UTC2024-07-03T08:15:00Z",  # 带 UTC 标识
        "2024-07-03 08:15:00Z",  # 带 Z 后缀
        "10/05/2023 02:48 PM",  # 美式日期
        "05/10/2023 14:48",  # 欧式日期
        "05.10.2023 14:48",  # 带点分隔
        "1700000000",  # Unix 时间戳（秒）
        "1700000000000",  # Unix 时间戳（毫秒）
        "@1696502880",  # 带 @ 的时间戳
        "2025年03月08日23",  # 识别成23年的bug
        "2025年03月08日23点",
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

    print(unix2chs(any2unix("2025年03月08日23", form="%Y年%m月%d日%H")))
    # 输出应为2025-03-08 23:00:00
