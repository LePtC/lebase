# -*- coding: utf-8 -*-
"""
字符串操作模块
包含字符串替换、修剪等操作功能
"""
import re

from lebase.ensures import ensure_str


def replace_rule(s, rule):
    """
    约等于 MMA 的 /. 功能
    仅适用于字符串
    auth: 氘化氢
    """
    for key, value in rule.items():
        s = s.replace(ensure_str(key), ensure_str(value))
    return s


def trim_tail(s, t):
    """
    去除字符串尾部指定字符串
    """
    if s.endswith(t):
        return s[: -len(t)]
    else:
        return s


def filt_blank(s, rule=None):
    """
    清除指定的空白字符
    """
    if rule is None:
        rule = ["\n", "\r", "\t", " ", "&nbsp;"]

    return replace_rule(ensure_str(s).strip(), {x: "" for x in rule})


def filt_dupblank(text):
    """
    清除连续重复的空格和换行符
    """
    return re.sub(" +", " ", re.sub("\n+", "\n\n", text))


if __name__ == "__main__":
    # 示例用法
    text = "这 是\t一个\n测试  字符串\r\n"
    print("原文本:", repr(text))
    print("清除空白字符后:", repr(filt_blank(text)))

    s = "这是一个测试字符串测试"
    print("去除尾部字符串:", trim_tail(s, "测试"))
