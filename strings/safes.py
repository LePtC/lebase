# -*- coding: utf-8 -*-
"""
字符串安全处理模块
包含字符串安全处理、过滤等功能
"""
import re
from typing import Union
from urllib import parse

from lebase.ensures import ensure_str
from lelog.logs import log

from .display import get_len_zh2


def str_safe(txt: Union[str, bytes]) -> str:
    """
    安全字符串处理
    """
    return encode_non_chinese(ensure_str(txt))


def str_maxlen(txt: str, maxLen: int = 60) -> str:
    """
    限制字符串最大长度
    """
    if len(txt) > maxLen * 2 + 2:
        return txt[:maxLen] + " ... " + txt[-maxLen:]
    else:
        return txt


def str_log(txt: Union[str, bytes], maxLen: int = 60) -> str:
    """
    日志安全字符串处理
    """
    return str_maxlen(encode_non_chinese(ensure_str(txt)), maxLen)


def filt_non_char(sentence: str) -> str:
    """
    过滤非中英文和数字
    cite: https://blog.csdn.net/keyue123/article/details/96436131
    """
    # 方法一 re.sub('[^\w\u4e00-\u9fff]+', '', sentence)
    # 方法二
    return re.sub("[^\u4e00-\u9fa5^a-z^A-Z^0-9]", "", sentence)


def filt_non_chinese(sentence: str) -> str:
    """
    过滤非中文字符
    """
    return re.sub(
        r"[^ -~\u4e00-\u9fa5，。？！、；：" "（）《》〈〉【】『』「」﹃﹄〔〕]",
        "",
        sentence,
    )


def sanitize_filename(filename: str) -> str:
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
    fullName = filename.strip()

    # ----------------使总长度不大于255个字符（一个汉字是2个字符）----------------
    if get_len_zh2(fullName) > 253:
        fullName = fullName[:253]  # TODO 你这也没除以2啊

    # Windows文件名禁止使用的字符
    forbiddenChars = '<>:"/\\|?*'
    # 全角字符映射
    fullWidthChars = "＜＞：＂／＼｜？＊"
    charMapping = {forb: full for forb, full in zip(forbiddenChars, fullWidthChars)}

    # 替换禁止字符为全角字符
    sanitized = "".join(charMapping.get(char, char) for char in fullName)
    # 删除仍然存在的禁止字符
    sanitized = "".join(char for char in sanitized if char not in forbiddenChars)
    # 去除开头和结尾的空格和点，防止Windows系统无法识别
    # sanitized = sanitized.strip().strip('.')

    return sanitized


def encode_non_chinese(txt: Union[str, bytes]) -> str:
    """
    编码非中文字符
    """
    regCn = re.compile(r"[^ -~\u4e00-\u9fa5，。？！、；：" "（）《》〈〉【】『』「」﹃﹄〔〕]")

    def replace_url_encode(matchobj):
        # print("  -  ", matchobj.group(0))
        return parse.quote(matchobj.group(0))

    return regCn.sub(replace_url_encode, ensure_str(txt))


def decode_non_chinese(txt: Union[str, bytes]) -> str:
    """
    解码非中文字符
    """
    return parse.unquote(ensure_str(txt))


if __name__ == "__main__":
    # 示例用法
    txt = "这是一个测试©字符串"
    print("安全字符串处理:", str_safe(txt))

    longText = "这是一个非常长的测试字符串，用于测试截断功能"
    print("限制长度:", str_maxlen(longText, maxLen=10))

    filename = 'test<file>:"name"'
    print("文件名处理:", sanitize_filename(filename))
