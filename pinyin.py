from itertools import chain
from pypinyin import Style, pinyin


def to_pinyin(s):
    """
    转拼音
    :param s: 字符串或列表
    :type s: str or list
    :return: 拼音字符串
    >>> to_pinyin('你好吗') -> 'ni3hao3ma'
    >>> to_pinyin(['你好', '吗']) -> 'ni3hao3ma'

    应用：
        print(sorted(['美国', '中国', '日本'], key=to_pinyin))  # ['美国', '日本', '中国']
        to_pinyin(dic.get("title", "")).lower() # 不区分大小写
    """
    return "".join(chain.from_iterable(pinyin(s, style=Style.TONE3)))


def to_pinyin_lower(s):
    """
    转拼音并转为小写
    :param s: 字符串或列表
    :return: 小写拼音字符串
    """
    return to_pinyin(s).lower()
