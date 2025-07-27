import re


def parse_numbers(input_string: str) -> list:
    """
    从输入字符串中提取所有连续数字序列，并以 int 列表形式返回。

    参数:
    input_string (str): 含有数字和其它字符的字符串

    返回:
    list[int]: 提取到的所有数字序列（整型列表）
    """
    # \d+ 表示匹配一个或多个连续数字
    digit_strings = re.findall(r"\d+", input_string)
    return list(map(int, digit_strings))


def parse_urls(text: str) -> list:
    r"""
    传入一个包含文本的字符串，从中提取所有形式的URL，返回它们组成的列表。
    1. 支持以 http:// 或 https:// 开头
    2. 支持以 ftp:// 开头
    3. 支持以 www. 开头
    [^\s] 匹配除空白字符（空格、换行等）之外的所有字符，以尽量捕获完整的URL
    """
    pattern = r"(?:https?://|ftp://|www\.)[^\s]+"
    return re.findall(pattern, text)


if __name__ == "__main__":

    upsString = """
        UID303266889
    UID3546816515672666
    UID3546713662950281
    UID227346677
    UID1040675491
    UID3546836109363304
    UID:1040675491
    UID:434712824
    """
    result = parse_numbers(upsString)
    print(result)
