# -*- coding: utf-8 -*-
"""
字符串显示格式化模块
包含字符串显示、列表打印等格式化功能
"""
import sys
import unicodedata


def fmt_size(num, suffix="", digits=1, lower_k=False):
    """
    将字节数（或任意数值）转换为可读性更高的字符串表示，自动选择合适的单位（K/M/G/T/P/E/Z/Y）。

    参数：
        num (float|int)：待转换的数值（如字节数）。
        suffix (str)：单位后缀，默认为空字符串。
        digits (int)：小数点保留位数，默认为1。若为0则为整数。
        lower_k (bool)：是否将K单位小写（如k、M、G...），默认为False（K大写）。

    返回：
        str：格式化后的字符串，如 '1.2M'、'512K'、'100'。

    示例：
        fmt_size(1024) -> '1.0K'
        fmt_size(1024, digits=0) -> '1K'
        fmt_size(1536, digits=0, lower_k=True) -> '2k'
        fmt_size(1048576) -> '1.0M'
    """
    units = ["", "K", "M", "G", "T", "P", "E", "Z", "Y"]
    if lower_k:
        units[1] = "k"
    for unit in units:
        if abs(num) < 1024.0:
            fmt = f"%.{digits}f" if digits > 0 else "%d"
            return (fmt % num) + unit + suffix
        num /= 1024.0
    fmt = f"%.{digits}f" if digits > 0 else "%d"
    return (fmt % num) + "Y" + suffix


def str_pad(any_input, target_width=16):
    """
    根据字符宽度（全角字符计2，半角字符计1）计算字符串宽度，
    若不足 target_width，则在末尾补充空格直到达到 target_width。

    参数:
      s: 输入字符串
      target_width: 目标宽度，默认为16

    返回:
      补齐空格后的字符串
    """
    current_width = 0
    s = str(any_input)
    for ch in s:
        # 如果字符为全角或宽字符，则计宽度2，否则计1
        if unicodedata.east_asian_width(ch) in ("F", "W"):
            current_width += 2
        else:
            current_width += 1

    # 如果宽度不足，补足空格
    if current_width < target_width:
        s += " " * (target_width - current_width)
    return s


def str_lst(lst, name=""):
    """
    格式化打印列表信息
    """
    if lst:
        length = len(lst)
        if length < 6:
            ret = f"{lst}"
        else:
            n = lst_len_classifier(length)
            abbr = f"{lst[:n]}"[:-1] + " ... " + f"{lst[-n:]}"[1:]

            ret = f"{abbr} len={length}"
    else:
        ret = "len=0"

    if name:
        ret = f"{name}: {ret}"
    return ret


def lst_len_classifier(length):
    """
    列表长度分类器
    """
    thresholds = [1, 3, 7, 10, 20, 30]
    for i in range(len(thresholds)):
        if length <= thresholds[i]:
            return i
    return 6


def print_single_line(msg):
    """\r 是回车符，将光标移到当前行的开头
    end 参数防止 print 函数输出新行
    flush() 强制刷新输出缓冲区，确保消息立即显示
    """
    print("\r" + msg, end="")
    sys.stdout.flush()


def get_len_zh2(txt):
    """
    返回字符串的显示宽度：
    - 中文宽度2
    - 树状符号（│、├、└、─）宽度1
    - 其它宽度1
    :param txt: 字符串
    :return: 显示宽度
    """
    tree_chars = set("│├└─")
    real_len = 0
    for ch in str(txt):
        if "\u4e00" <= ch <= "\u9fff":  # 中文
            real_len += 2
        elif ch in tree_chars:
            real_len += 1
        else:
            real_len += 1
    return real_len


if __name__ == "__main__":

    # 示例用法
    print("文件大小格式化:", fmt_size(1024))
    print("字符串补齐:", repr(str_pad("测试", 10)))
    test_list = [1, 2, 3, 4, 5, 6, 7, 8]
    print("列表显示:", str_lst(test_list, "测试列表"))
    print("中文字符串长度:", get_len_zh2("中文abc"))

    import time

    # 示例使用
    length = [1, 2, 3, 4, 5, 6, 7, 9, 10, 11, 19, 20, 22, 33]
    for n in length:
        print_single_line(str_lst(list(range(n))))
        time.sleep(1)
