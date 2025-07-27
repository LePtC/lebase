# ----------------------------
# 数组操作（不用 numpy 的话）
# ----------------------------


def transpose(li):
    """
    二维 list 转置
    warning: 不等长列表会被裁短 li=[[1,2],[3,4],[5]] gives you [[1,3,5]]
    """
    return list(map(list, zip(*li)))


def flatten(L):
    """auth: 霜落"""
    from itertools import chain
    if isinstance(L, list):
        return list(chain.from_iterable(map(flatten, L)))
    else:
        return [L]


def filt_null(liStr):
    return [x for x in liStr if x]


def listset(list1):
    """
    去重且尽可能保留原 list 的顺序
    """
    if not list1:  # 防空表格报错
        return []

    if isinstance(list1[0], list):  # 二维表格提取首列去重然后用字典恢复
        dicRecover = {r[0]: r for r in list1}
        list0 = listset([r[0] for r in list1])  # 递归到一维情形处理
        list2 = [dicRecover[i] for i in list0]
        return list2

    else:
        try:
            # list2 = list(set(list1))
            # list2.sort(key=list1.index)
            list2 = list(dict.fromkeys(list1))  # 这个方案速度神一样快
            return list2

        except Exception as e:
            print(f"[error] listset 失败 err: {e}")
            return list1


def safe_li0(li):
    """传入 list，返回 li[0]，防空数组"""
    if len(li) <= 0:
        return ""
    else:
        return li[0]


# ----------------------------
# 方便制作 table
# ----------------------------


def lidic2table(liDic, f=0, cols=None):
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
        return [head, *li2d]


def table_append(li2d, elem=0):
    """2d list 右侧续一列"""
    return [[*row, elem] for row in li2d]


def lidic2table_cols(liDic, head, f=0):
    li2d = []
    for x in liDic:
        row = []
        for k in head:
            row.append(x.get(k, f))
        li2d.append(row)
    return [head, *li2d]


def table2html(li2d):
    s = "<table><tbody>"
    for line in li2d:
        s += "<tr>"
        for col in line:
            s += f"<td>{col}</td>"
        s += "</tr>"
    s += "</tbody></table>"
    return s


def compare(standard_list, compare_list):
    """
    比较两个列表，返回compare_list中相对于standard_list的多余和缺少的元素（均按从小到大排序）。

    参数：
        standard_list (list): 标准列表
        compare_list (list): 待比较列表

    返回：
        tuple: (extra, missing)
            extra: 在compare_list中但不在standard_list中的元素，按从小到大排序。
            missing: 在standard_list中但不在compare_list中的元素，按从小到大排序。
    """
    # 使用集合求差集，再转成列表排序
    extra = sorted(list(set(compare_list) - set(standard_list)))
    missing = sorted(list(set(standard_list) - set(compare_list)))

    return extra, missing


if __name__ == "__main__":

    # ----------------------------
    # 测试
    # ----------------------------

    standard = [1, 2, 3, 4, 5]
    compareli = [2, 3, 4, 6, 7]
    extra, missing = compare(standard, compareli)
    print("多余的元素:", extra)  # 输出: [6, 7]
    print("缺少的元素:", missing)  # 输出: [1, 5]

    pass
