# -*- coding: utf-8 -*-
"""
HTML字符串处理模块
包含处理HTML标签、链接解析等功能
"""
import re

from bs4 import BeautifulSoup


def filt_htmltag(html_str):
    """使用BeautifulSoup清除HTML标签
    cite: https://stackoverflow.com/questions/753052/strip-html-from-strings-in-python
    比 filt_tag 更准确，但不知道是否性能慢些？
    """
    soup = BeautifulSoup(html_str, features="lxml")
    return soup.get_text()


def filt_tag(raw_html):
    """使用正则表达式清除HTML标签
    https://www.codegrepper.com/code-examples/html/regex+to+remove+html+tags+python
    """
    cleanr = re.compile("<.*?>")
    cleantext = re.sub(cleanr, "", raw_html)
    return cleantext


def filt_base64(html_str):
    """清除Base64编码的图片，给makemid存html时节省空间用"""
    return re.sub('<img src="data:image/png;base64,[^>]*>', "", html_str)


def filt_js(html_str):
    """清除JavaScript代码，给makemid存html时节省空间用"""
    return re.sub("<script[^<]*</script>", "", html_str)


def filt_weixintag(text):
    """
    微信文章特色标记处理
    """
    ret = text.replace("/ Unsplash", "\n").replace("/Unsplash", "\n")
    ret = ret.replace("/图虫创意", "\n图\n")
    return ret


def parse_links(html):
    """
    解析HTML中的链接
    """
    soup = BeautifulSoup(html, "html.parser")
    links = []
    for a in soup.find_all("a"):
        href = a.get("href")
        if href and href not in links:
            links.append(href)
    return links


if __name__ == "__main__":
    # 示例用法
    html_text = "<p>这是一个<b>测试</b>文本</p>"
    print("原文本:", html_text)
    print("清除HTML标签后:", filt_htmltag(html_text))

    links_html = '<p>链接1<a href="http://example.com">示例</a>和链接2<a href="http://test.com">测试</a></p>'
    print("解析链接:", parse_links(links_html))
