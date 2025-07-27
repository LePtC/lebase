# ----------------------------
# 数组操作（不用 numpy 的话）
# ----------------------------


def transpose(lst):
    """
    二维 list 转置
    warning: 不等长列表会被裁短 lst=[[1,2],[3,4],[5]] gives you [[1,3,5]]
    """
    return list(map(list, zip(*lst)))


def flatten(lst):
    """auth: 霜落"""
    from itertools import chain
    if isinstance(lst, list):
        return list(chain.from_iterable(map(flatten, lst)))
    else:
        return [lst]


def filt_null(lstStr):
    return [x for x in lstStr if x]


def listset(lstFirst):
    """
    去重且尽可能保留原 list 的顺序
    """
    if not lstFirst:  # 防空表格报错
        return []

    if isinstance(lstFirst[0], list):  # 二维表格提取首列去重然后用字典恢复
        dicRecover = {r[0]: r for r in lstFirst}
        lst0 = listset([r[0] for r in lstFirst])  # 递归到一维情形处理
        lstSecond = [dicRecover[i] for i in lst0]
        return lstSecond

    else:
        try:
            # lstSecond = list(set(lstFirst))
            # lstSecond.sort(key=lstFirst.index)
            lstSecond = list(dict.fromkeys(lstFirst))  # 这个方案速度神一样快
            return lstSecond

        except Exception as e:
            print(f"[error] listset 失败 err: {e}")
            return lstFirst


def safe_li0(lstInput):
    """传入 list，返回 lstInput[0]，防空数组"""
    if len(lstInput) <= 0:
        return ""
    else:
        return lstInput[0]


# ----------------------------
# 方便制作 table
# ----------------------------


def lidic2table(lstDic, f=0, cols=None):
    """list of dict（通常来自数据库）转换成 2d list
    f: 数据缺失的地方填充什么
    """
    if cols:
        return lidic2table_cols(lstDic, cols, f)
    else:
        lst2d = []
        head = []
        for x in lstDic:
            row = []
            for k in x.keys():
                if k not in head:
                    head.append(k)
                    lst2d = table_append(lst2d, f)
            for k in head:
                row.append(x.get(k, f))
            lst2d.append(row)
        return [head, *lst2d]


def table_append(lst2d, elem=0):
    """2d list 右侧续一列"""
    return [[*row, elem] for row in lst2d]


def lidic2table_cols(lstDic, head, f=0):
    lst2d = []
    for x in lstDic:
        row = []
        for k in head:
            row.append(x.get(k, f))
        lst2d.append(row)
    return [head, *lst2d]


def table2html(lst2d):
    s = "<table><tbody>"
    for line in lst2d:
        s += "<tr>"
        for col in line:
            s += f"<td>{col}</td>"
        s += "</tr>"
    s += "</tbody></table>"
    return s


def compare(standardList, compareList):
    """
    比较两个列表，返回compareList中相对于standardList的多余和缺少的元素（均按从小到大排序）。

    参数：
        standardList (list): 标准列表
        compareList (list): 待比较列表

    返回：
        tuple: (extra, missing)
            extra: 在compareList中但不在standardList中的元素，按从小到大排序。
            missing: 在standardList中但不在compareList中的元素，按从小到大排序。
    """
    # 使用集合求差集，再转成列表排序
    extra = sorted(list(set(compareList) - set(standardList)))
    missing = sorted(list(set(standardList) - set(compareList)))

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
