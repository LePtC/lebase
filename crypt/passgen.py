# -*- coding: utf-8 -*-
"""
生成所需长度的随机字符串密码
"""
import random
import string


def generate_random_password(length, char_set="1a"):
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
        return "Invalid character set specified."

    # 随机选择指定数量的字符
    random_password = "".join(random.choice(characters) for i in range(length))
    return random_password


if __name__ == "__main__":

    print(generate_random_password(32))
    print(generate_random_password(32, "1a!"))
