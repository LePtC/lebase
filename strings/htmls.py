# -*- coding: utf-8 -*-
"""
HTML字符串处理模块
包含处理HTML标签、链接解析等功能
"""
import re

from bs4 import BeautifulSoup


def filt_html_tags(html_str):
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


def filt_wechat_tags(text):
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
        headtxt = filt_html_tags(txt.split("</h1>")[0])
    else:
        headtxt = filt_html_tags(txt)

    return headtxt[: min([10, len(headtxt)])]


def get_main_domain(url):
    import tldextract

    ext = tldextract.extract(url)
    if ext.registered_domain:
        return ext.registered_domain
    elif ext.suffix:
        return f"{ext.domain}.{ext.suffix}"
    else:
        return ext.domain


if __name__ == "__main__":
    # 示例用法
    html_text = "<p>这是一个<b>测试</b>文本</p>"
    print("原文本:", html_text)
    print("清除HTML标签后:", filt_html_tags(html_text))

    links_html = '<p>链接1<a href="http://example.com">示例</a>和链接2<a href="http://test.com">测试</a></p>'
    print("解析链接:", parse_links(links_html))
