# -*- coding: utf-8 -*-
"""
字符串安全处理模块
包含字符串安全处理、过滤等功能
"""
import re
from urllib import parse

from lebase.ensures import ensure_str
from lelog.logs import log


def str_safe(txt):
    """
    安全字符串处理
    """
    return encode_non_chinese(ensure_str(txt))


def str_maxlen(txt, maxlen=60):
    """
    限制字符串最大长度
    """
    if len(txt) > maxlen * 2 + 2:
        return txt[:maxlen] + " ... " + txt[-maxlen:]
    else:
        return txt


def str_log(txt, maxlen=60):
    """
    日志安全字符串处理
    """
    return str_maxlen(encode_non_chinese(ensure_str(txt)), maxlen)


def filt_non_char(sentence):
    """
    过滤非中英文和数字
    cite: https://blog.csdn.net/keyue123/article/details/96436131
    """
    # 方法一 re.sub('[^\w\u4e00-\u9fff]+', '', sentence)
    # 方法二
    return re.sub("[^\u4e00-\u9fa5^a-z^A-Z^0-9]", "", sentence)


def filt_non_chinese(sentence):
    """
    过滤非中文字符
    """
    return re.sub(
        "[^ -~^\\u4e00-\\u9fa5^，^。^？^！^、^；^：^“^”（^）^《^》^〈^〉^【^】^『^』^「^」^﹃^﹄^〔^〕]",
        "",
        sentence,
    )


def sanitize_filename(filename):
    """
    传入文件名，检查并返回合法的文件名（默认替换非法字符为换成全角字符）
    （参考了 DrissionPage 的 save_mht 时的 make_valid_name，只不过去掉非法字符改成替换成全角）
    :param filename: 原始文件名
    :return: 处理后的合法文件名
    """
    if not filename:
        log.warning("传入文件名为空")
        return "未命名"

    # ----------------去除前后空格----------------
    full_name = filename.strip()

    # ----------------使总长度不大于255个字符（一个汉字是2个字符）----------------
    if get_len_zh2(full_name) > 253:
        full_name = full_name[:253]  # TODO 你这也没除以2啊

    # Windows文件名禁止使用的字符
    forbidden_chars = '<>:"/\\|?*'
    # 全角字符映射
    full_width_chars = "＜＞：＂／＼｜？＊"
    char_mapping = {forb: full for forb, full in zip(forbidden_chars, full_width_chars)}

    # 替换禁止字符为全角字符
    sanitized = "".join(char_mapping.get(char, char) for char in full_name)
    # 删除仍然存在的禁止字符
    sanitized = "".join(char for char in sanitized if char not in forbidden_chars)
    # 去除开头和结尾的空格和点，防止Windows系统无法识别
    # sanitized = sanitized.strip().strip('.')

    return sanitized


def encode_non_chinese(txt):
    """
    编码非中文字符
    """
    reg_cn = re.compile(
        "[^ -~^\\u4e00-\\u9fa5^，^。^？^！^、^；^：^“^”（^）^《^》^〈^〉^【^】^『^』^「^」^﹃^﹄^〔^〕]"
    )

    def replace_url_encode(matchobj):
        # print("  -  ", matchobj.group(0))
        return parse.quote(matchobj.group(0))

    return reg_cn.sub(replace_url_encode, ensure_str(txt))


def decode_non_chinese(txt):
    """
    解码非中文字符
    """
    return parse.unquote(ensure_str(txt))


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
    txt = "这是一个测试©字符串"
    print("安全字符串处理:", str_safe(txt))

    long_text = "这是一个非常长的测试字符串，用于测试截断功能"
    print("限制长度:", str_maxlen(long_text, maxlen=10))

    filename = 'test<file>:"name"'
    print("文件名处理:", sanitize_filename(filename))
