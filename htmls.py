# 导入BeautifulSoup库，用于解析html
from bs4 import BeautifulSoup


# 定义一个函数，接受一个html字符串作为参数
def parse_links(html):
    # 创建一个BeautifulSoup对象，指定解析器为html.parser
    soup = BeautifulSoup(html, "html.parser")
    # 创建一个空列表，用于存储链接
    links = []
    # 遍历soup对象中的所有<a>标签
    for a in soup.find_all("a"):
        # 获取<a>标签的href属性，即链接
        href = a.get("href")
        # 如果链接不为空，且不在links列表中，就添加到links列表中
        if href and href not in links:
            links.append(href)
    # 返回links列表
    return links
