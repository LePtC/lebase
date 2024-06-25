def lidic2table(liDic, f=0, cols=[]):
    """list of dict（通常来自数据库）转换成 2d list
    f: 数据缺失的地方填充什么
    """
    if cols:
        return lidic2table_cols(liDic, cols, f)
    else:
        li2d = []
        head = []
        for x in liDic:
            row = []
            for k in x.keys():
                if k not in head:
                    head.append(k)
                    li2d = table_append(li2d, f)
            for k in head:
                row.append(x.get(k, f))
            li2d.append(row)
        return [head] + li2d


def table_append(li2d, elem=0):
    """2d list 右侧续一列"""
    return [row + [elem] for row in li2d]


def lidic2table_cols(liDic, head, f=0):
    li2d = []
    for x in liDic:
        row = []
        for k in head:
            row.append(x.get(k, f))
        li2d.append(row)
    return [head] + li2d


def table2html(li2d):
    s = "<table><tbody>"
    for line in li2d:
        s += "<tr>"
        for col in line:
            s += f"<td>{col}</td>"
        s += "</tr>"
    s += "</tbody></table>"
    return s
