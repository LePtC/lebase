# -*- coding: utf-8 -*-
"""
随机字符串生成模块
"""

import random
import string
from typing import Optional


def generate_random_string(length: int, char_set: Optional[str] = None) -> str:
    """
    生成指定长度的随机字符串

    Args:
        length: 要生成的字符串长度
        char_set: 字符集，如果不指定则默认使用字母和数字

    Returns:
        生成的随机字符串
    """
    if char_set is None:
        char_set = string.ascii_letters + string.digits

    return "".join(random.choices(char_set, k=length))


def generate_random_string_choices(length: int, char_set: str = "1a") -> str:
    """
    使用random.choices生成指定长度的随机字符串（兼容passgen.py的字符集选项）

    Args:
        length: 要生成的字符串长度
        char_set: 字符集类型
            - "1": 仅数字
            - "a": 仅字母
            - "1a": 数字和字母（默认）
            - "1a!": 数字、字母和特殊字符(!@#$%^&*_+<>?=.)
            - "1a!~": 数字、字母和所有标点符号

    Returns:
        生成的随机字符串
    """
    # 根据char_set参数选择字符集
    if char_set == "1":
        characters = string.digits
    elif char_set == "a":
        characters = string.ascii_letters
    elif char_set == "1a":
        characters = string.ascii_letters + string.digits
    elif char_set == "1a!":
        characters = string.ascii_letters + string.digits + "!@#$%^&*_+<>?=."
    elif char_set == "1a!~":
        characters = string.ascii_letters + string.digits + string.punctuation
    else:
        characters = char_set  # 直接使用传入的字符串作为字符集

    return "".join(random.choices(characters, k=length))


if __name__ == "__main__":
    # 测试代码
    print(generate_random_string(10))
    print(generate_random_string_choices(10))
    print(generate_random_string_choices(10, "1a!"))
