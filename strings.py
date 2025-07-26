# -*- coding: utf-8 -*-
"""
Level 0.5（可被 lebase.times 引用）
str开头的接口都是返回string
"""
import re
import sys
import unicodedata
from urllib import parse

import tldextract
from bs4 import BeautifulSoup

from lelog.logs import log
from lebase.safes import ensure_str


def mma_replace(s: str, rule: dict):
    """
    约等于 MMA 的 /. 功能
    仅适用于字符串
    auth: 氘化氢
    """
    for keys in rule:
        s = s.replace(ensure_str(keys), ensure_str(rule[keys]))
    return s


def sizeof_fmt(num, suffix="", digits=1, lower_k=False):
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
        sizeof_fmt(1024) -> '1.0K'
        sizeof_fmt(1024, digits=0) -> '1K'
        sizeof_fmt(1536, digits=0, lower_k=True) -> '2k'
        sizeof_fmt(1048576) -> '1.0M'
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


def strlog(txt, maxlen=60):
    return str_maxlen(non_cn_encode(ensure_str(txt)), maxlen)


def strpad(anyInput, target_width=16):
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
    s = str(anyInput)
    for ch in s:
        # 如果字符为全角或宽字符，则计宽度2，否则计1
        if unicodedata.east_asian_width(ch) in ('F', 'W'):
            current_width += 2
        else:
            current_width += 1

    # 如果宽度不足，补足空格
    if current_width < target_width:
        s += ' ' * (target_width - current_width)
    return s


# ----------------------------
# filters
# ----------------------------

def trim_tail(s, t):
    if s.endswith(t):
        return s[: -len(t)]
    else:
        return s


def filt_nonchar(sentence):
    """
    过滤非中英文和数字
    cite: https://blog.csdn.net/keyue123/article/details/96436131
    """
    # 方法一 re.sub('[^\w\u4e00-\u9fff]+', '', sentence)
    # 方法二
    return re.sub("[^\u4e00-\u9fa5^a-z^A-Z^0-9]", "", sentence)


def filt_non_cn(sentence):
    return re.sub(
        "[^ -~^\\u4e00-\\u9fa5^，^。^？^！^、^；^：^“^”（^）^《^》^〈^〉^【^】^『^』^「^」^﹃^﹄^〔^〕]",
        "",
        sentence,
    )


def filt_blank(s, rule=["\n", "\r", "\t", " ", "&nbsp;"]):
    """
    清除全部空格和换行符
    """
    return mma_replace(ensure_str(s).strip(), {x: "" for x in rule})


def filt_dupblank(text):
    """
    清除连续重复的空格和换行符
    """
    return re.sub(" +", " ", re.sub("\n+", "\n\n", text))


def filt_htmltag(html_str):
    """cite: https://stackoverflow.com/questions/753052/strip-html-from-strings-in-python
    比 filt_tag 更准确，但不知道是否性能慢些？
    """
    soup = BeautifulSoup(html_str, features="lxml")
    return soup.get_text()


def filt_tag(raw_html):
    """https://www.codegrepper.com/code-examples/html/regex+to+remove+html+tags+python"""
    cleanr = re.compile("<.*?>")
    cleantext = re.sub(cleanr, "", raw_html)
    return cleantext


def filt_base64(html_str):
    """给makemid存html时节省空间用"""
    return re.sub('<img src="data:image/png;base64,[^>]*>', "", html_str)


def filt_js(html_str):
    """给makemid存html时节省空间用"""
    return re.sub("<script[^<]*</script>", "", html_str)


def filt_weixintag(text):
    """
    微信文章特色标记处理
    """
    ret = text.replace("/ Unsplash", "\n").replace("/Unsplash", "\n")
    ret = ret.replace("/图虫创意", "\n图\n")
    return ret


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
        if '\u4e00' <= ch <= '\u9fff':  # 中文
            real_len += 2
        elif ch in tree_chars:
            real_len += 1
        else:
            real_len += 1
    return real_len


# ----------------------------
# 打印 list 信息
# ----------------------------


def strli(lst, name=""):
    if lst:
        length = len(lst)
        if length < 6:
            ret = f"{lst}"
        else:
            n = list_length_classifier(length)
            abbr = f"{lst[:n]}"[:-1] + " ... " + f"{lst[-n:]}"[1:]

            ret = f"{abbr} len={length}"
    else:
        ret = "len=0"

    if name:
        ret = f"{name}: {ret}"
    return ret


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


# ----------------------------
# 各种 parser
# ----------------------------

# >>> "<h1>swwww<h1>22ddd".split('<h1>')
# ['', 'swwww', '22ddd']
def split_by_tag(htm, tag="<h1"):
    """输入：html长string
    输出：按<h1.. 分割，全部连起来等于原字符串
    """
    li = htm.split(tag)
    for i in range(1, len(li)):
        li[i] = tag + li[i]
    return li


def extract_head_txt(txt):
    """输入html(chapter)，可能以 '<h1 id="' 开头也可能以 p 开头，要求提取不带 tag 的纯文本并控制长度"""
    # print(txt[:390])
    # return txt[:16].replace('<h1 id="', '') # 早期做法

    if "</h1>" in txt:
        headtxt = filt_htmltag(txt.split("</h1>")[0])
    else:
        headtxt = filt_htmltag(txt)

    return headtxt[: min([10, len(headtxt)])]


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
    """
    传入一个包含文本的字符串，从中提取所有形式的URL，返回它们组成的列表。
    """
    # 简单可行的匹配模式示例：
    # 1. 支持以 http:// 或 https:// 开头
    # 2. 支持以 ftp:// 开头
    # 3. 支持以 www. 开头
    # [^\s] 匹配除空白字符（空格、换行等）之外的所有字符，以尽量捕获完整的URL
    pattern = r"(?:https?://|ftp://|www\.)[^\s]+"

    return re.findall(pattern, text)


def get_main_domain(url):
    ext = tldextract.extract(url)
    if ext.registered_domain:
        return ext.registered_domain
    elif ext.suffix:
        return f"{ext.domain}.{ext.suffix}"
    else:
        return ext.domain


if __name__ == "__main__":

    # test_print_list

    import time

    # 示例使用
    length = [1, 2, 3, 4, 5, 6, 7, 9, 10, 11, 19, 20, 22, 33]
    for n in length:
        print_1line(strli(list(range(n))))
        time.sleep(1)

    # test_mid_parser
    # upsString = """
    #     UID303266889
    # UID3546816515672666
    # UID3546713662950281
    # UID227346677
    # UID1040675491
    # UID3546836109363304
    # UID:1040675491
    # UID:434712824
    # """
    # result = parse_numbers(upsString)
    # print(result)
    # 结果示例:
    # ['303266889', '3546816515672666', '3546713662950281',
    #  '227346677', '1040675491', '3546836109363304',
    #  '1040675491', '434712824']

    pass
