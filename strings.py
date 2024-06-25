# encoding=utf-8
"""
Level 0.5（可被 lebase.times 引用）
str开头的接口都是返回string
"""
import re
import sys

from urllib import parse
from lebase.ensure import ensure_str


def mma_replace(s: str, rule: dict):
    """
    约等于 MMA 的 /. 功能
    仅适用于字符串
    auth: 氘化氢
    """
    for keys in rule:
        s = s.replace(ensure_str(keys), ensure_str(rule[keys]))
    return s


regCN = re.compile("[^ -~^\\u4e00-\\u9fa5^，^。^？^！^、^；^：^“^”（^）^《^》^〈^〉^【^】^『^』^「^」^﹃^﹄^〔^〕]")


def url_encode_replace(matchobj):
    # print("  -  ", matchobj.group(0))
    return parse.quote(matchobj.group(0))


def non_cn_encode(txt):
    """过滤除中英文及数字以外的其他炸日志字符，
    解决 win 后端执行时报 'gbk' codec can't encode character
    且不影响肉眼读信息"""
    return regCN.sub(url_encode_replace, ensure_str(txt))


def non_cn_decode(txt):
    return parse.unquote(ensure_str(txt))


def str_safe(txt):
    return non_cn_encode(ensure_str(txt))


def str_maxlen(txt, maxlen=60):
    if len(txt) > maxlen * 2 + 2:
        return txt[:maxlen] + " ... " + txt[-maxlen:]
    else:
        return txt


def strlog(txt):
    return str_maxlen(non_cn_encode(ensure_str(txt)))


def strli(lst):
    if lst:
        length = len(lst)
        if length < 6:
            return f"{lst}"
        else:
            n = list_length_classifier(length)
            abbr = f"{lst[:n]}"[:-1] + " ... " + f"{lst[-n:]}"[1:]

            return f"{abbr} len={length}"
    else:
        return "len=0"


def list_length_classifier(length):
    thresholds = [1, 3, 7, 10, 20, 30]
    for i in range(len(thresholds)):
        if length <= thresholds[i]:
            return i
    return 6


def print_1line(msg):
    """\r 是回车符，将光标移到当前行的开头
    end 参数防止 print 函数输出新行
    flush() 强制刷新输出缓冲区，确保消息立即显示
    """
    print("\r" + msg, end="")
    sys.stdout.flush()


if __name__ == "__main__":
    import time

    # 示例使用
    length = [1, 2, 3, 4, 5, 6, 7, 9, 10, 11, 19, 20, 22, 33]
    for n in length:
        print_1line(strli(list(range(n))))
        time.sleep(1)

    pass
