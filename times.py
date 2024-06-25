# encoding=utf-8
"""
用途：时间字符串格式转换库
狸子要处理的时间格式有这几种：unix (float)、str (taskId)、chs（中文时间）、tuple（很少用到）
app 用到的：taskId（半日爬虫）、fsid（filesystem）、str2info（笔记农历）
"""
import time
from datetime import datetime, timedelta
import re

from lebase.ensure import ensure_str, is_number, ensure_num
from lebase.strings import mma_replace


def logtime(now=None):
    if now is not None:
        __now = now
    else:
        __now = time.localtime(time.time())
    return time.strftime("%m/%d %H:%M:%S", __now)


def ensure_taskId(anytime, length=10):
    """
    任意格式智能识别然后转 taskId
    """
    if isinstance(anytime, (float, int)):
        ret = unix2taskId(safe_mili(anytime))
    else:
        ret = str2taskId(anytime)

    return ret[: min([length, len(ret)])]


def str2taskId(s):
    # 首先判断是否纯数字
    if re.match(r"^\d*$", str(s)):
        s = str(s)
        if s.startswith("201") or s.startswith("202"):
            test = unix2taskId(str2unix(s))
            if is_taskId(test):  # 尝试纯数字字符串时间
                return test

    if is_number(s):
        if is_rtime(s):  # 尝试 unix 时间
            return unix2taskId(float(s))

    if isinstance(s, str):  # 尝试 chs 时间（科技号 data.csv 用过这种格式…）
        txt = (
            re.sub(r"年(\d)月", r"0\1", s).replace("年", "").replace("月", "").replace("日", "")
        )  # TODO 未处理（周几）
        if len(txt) == 6:  # 只精确到月则认定为1号
            txt += "0111"
        elif len(txt) == 8:
            txt += "11"
        return txt

    # printlog.warn(f'totaskId fail: {ensure.st(s)}')
    print(f"str2taskId fail: {ensure_str(s)}")
    return s


def ensure_unixtime(anytime):
    """
    任意格式智能识别然后转 unix 时间
    """
    if isinstance(anytime, (float, int)):
        return safe_mili(anytime)
    else:
        return str2unix(ensure_taskId(anytime, length=99))


def is_taskId(f):
    """
    注：只认 8 位数且 11 点触发的是 taskId
    """
    return re.match(r"^20\d{8}$", f) and (f.endswith(("11", "23")))


def is_rtime(s):
    s = safe_mili(ensure_num(s))
    if str2unix("2017123123") < s < str2unix("2099123123"):
        return True
    else:
        return False


def filt_rtime(dic):
    for x in dic:
        if isinstance(dic[x], (float, int)):
            if is_rtime(dic[x]):
                dic[x] = unix2chs(dic[x])
    return dic


def safe_mili(rtime):
    """
    毫秒格式兼容性保证
    """
    if rtime > str2unix("2999123111"):
        return rtime / 1000
    else:
        return rtime


def unix2str(ftime_="", form="%Y%m%d%H%M%S"):
    """unix时间转字符串时间"""
    # return time.strftime(form.encode('unicode_escape').decode('utf8'),
    #   time.localtime(ftime)).encode('utf-8').decode('unicode_escape')
    if not ftime_:
        ftime = time.time()
    else:
        ftime = ftime_
    tm = safe_mili(ftime)
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


# 纯数字字符串时间转成各种 -----------


def str2tuple(stime, form=""):
    """字符串时间转为元组时间"""
    s = str(stime)
    if "天前" in s:
        return convert_days_ago(s)
    if form == "":
        flag = False
        if "年" in stime:
            form = "%Y年%m月%d日"
            flag = True
        elif "-" in stime:
            form = "%Y-%m-%d"
            flag = True
        elif "/" in stime:
            form = "%Y/%m/%d"
            flag = True
        else:
            form = "%Y%m%d" + ["", "%H"][len(s) >= 10] + ["", "%M"][len(s) >= 12] + ["", "%S"][len(s) >= 14]
            if len(s) % 2 == 1:
                s = s[:-1]

        if flag:
            if len(stime) > len(form) + 2:
                form += " %H:%M"
            if len(stime) > len(form) + 2:
                form += ":%S"

    return time.strptime(s, form)


def convert_days_ago(days_string):
    """应对newbing或B站智能把近期时间自动转x天前"""
    days = int(days_string.split("天前")[0])  # 提取天数
    new_date = datetime.now() - timedelta(days=days)  # 计算新日期
    return new_date.timetuple()  # .strftime("%Y年%m月%d日")  # 返回格式化的日期


def str2unix(stime: str, form=""):
    """字符串时间转unix时间"""
    return int(time.mktime(str2tuple(stime, form)))


def cal_day_diff(stime, stime2):
    return int((ensure_unixtime(stime) - ensure_unixtime(stime2)) / 8640) / 10


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


def taskId2chs(date, form="%Y年%m月%d日（%a）"):
    # _form = mma_Replace(form, rule_eng2chs)
    s1 = (
        time.strftime(form.encode("unicode_escape").decode("utf8"), str2tuple(date))
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


# ----------------------------
# 时间工具
# ----------------------------


def taskId2ndayago(stime: str, days: float):
    """
    str2str(shifted) 时间平移函数
    在氘化氢 BYK 和 pyfac 里曾叫 few_days_ago
    """
    return unix2taskId(str2unix(stime) - 3600 * 24 * days)


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
    u_start, u_end = str2unix(t_start), str2unix(t_end)
    # 生成时间列表
    time_list = range(u_start, u_end + 1, interval * 3600)
    # 转换回字符串格式
    ret = [ensure_taskId(unix2str(_)) for _ in time_list]
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

    nextmonth1 = str2unix(s, form="%Y%m%d%H")
    return unix2str(nextmonth1 - 24 * 3600)[:8]


if __name__ == "__main__":

    # ----------------------------
    # 测试
    # ----------------------------

    print(logtime())

    print(str2taskId("2022年02月03日"))

    print(unix2str(time.time(), form="%Y.%m.%d"))
    print(time_str_list("2022011923", "2022012123"))

    print(unix2chs(time.time()))
    # print(str2info("20210506"))

    print(str2tuple("5天前"))

    # ----------------------------
    # 生产
    # ----------------------------

    # input("按任意键退出 \n ")
    # print(0)
    pass
