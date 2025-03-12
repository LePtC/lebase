# -*- coding: utf-8 -*-
from lebase.log import log


# ----------------------------
# dict 操作工具
# ----------------------------


def keychange(x: dict, keybefore: str, keyafter: str):
    if keybefore in x:
        x[keyafter] = x[keybefore]
        x.pop(keybefore, None)
    return x


def safeget(d, k, f=""):
    """在 dict.get 之前还判断下是否是 dict 对象以防 Nonetype 报错"""
    if isinstance(d, dict):
        return d.get(k, f)
    else:
        return f


def count_elements(one_d_list):
    # initialize an empty dictionary to store the output
    output = {}
    # loop through each element in the input list
    for element in one_d_list:
        # check if the element is already in the dictionary
        if element in output:
            # increment the value by one
            output[element] += 1
        else:
            # add the element as a key and set the value to one
            output[element] = 1
    # return the output dictionary
    return output


def get_dic_path(dic, path):
    """
    mypath = ["data", "cursor", "all_count"]
    mypath = ["data", "replies", 1, "like"]
    mypath = ["data", "replies", 1, "content", "message"]
    mypath = ["data", "replies", 1, "replies", 1, "content", "message"]
    """
    value = dic
    for i in range(len(path)):
        key = path[i]
        if isinstance(value, dict) and key in value:
            value = value[key]
        elif isinstance(value, list) and isinstance(key, int):
            return [get_dic_path(item, path[i + 1 :]) for item in value]
        else:
            return -1
    return value


def lidic_remove_dupkey(liDic):
    """暂时要求传入liDic已sort好"""
    # keys = []
    lastkey = ""
    ret = []
    for d in liDic:
        # if d['_id'] not in keys: # too slow
        if d["_id"] != lastkey:
            ret.append(d)
            lastkey = d["_id"]
    print(f"lidic_remove_dupkey: len in: {len(liDic)} out: {len(ret)}")
    return ret


def get_key_from_value(dicTid, my_string):
    for key, value in dicTid.items():
        if value == my_string:
            return key
    raise ValueError(f"Value {my_string} does not exist in the dictionary.")


def check_for_update(dicSrc, dicDst):
    # 检查dicSrc中的每个键值对是否在dicDst中有且值相同
    for key, value in dicSrc.items():
        if key not in dicDst or dicDst[key] != value:
            return True  # 如果有不同，则返回True表示需要更新
    return False  # 如果所有键值对都匹配，则返回False


def check_useless(inputDict, uselessKeys=[]):
    """
    检查传入的字典中是否除了指定的无用键（uselessKeys）以外没有其它的键。

    参数:
        inputDict (dict): 需要检查的字典。
        uselessKeys (list): 无用键列表，默认为 ["_id", "mid", "rtime"]。

    返回:
        bool: 如果字典中仅包含无用键（或为空字典），则返回 True；如果存在其它非无用键，则返回 False。

    """
    # 检查输入是否为字典
    if not isinstance(inputDict, dict):
        log.error("传入的参数不是一个字典类型！")
        return True

    # 获取字典中所有的键，并打印日志
    dictKeys = set(inputDict.keys())
    # log.info("传入字典的所有键为: {}".format(dictKeys))

    # 将无用键列表转换为集合，便于后续比较
    uselessKeysSet = set(uselessKeys)
    # log.info("无用键集合为: {}".format(uselessKeysSet))

    # 计算字典中除了无用键以外的其它键
    extraKeys = dictKeys - uselessKeysSet
    # log.info("字典中额外的键为: {}".format(extraKeys))

    # 根据是否存在额外的键返回结果
    if not extraKeys:
        log.warn(f"此数据无用: {inputDict}")
        return True
    else:
        # log.info("字典有有用键")
        return False


if __name__ == "__main__":
    # 用例 1: 字典中包含全部无用键
    testDict1 = {"_id": 123, "mid": 456, "rtime": 789}
    result1 = check_useless(testDict1, uselessKeys=["_id", "mid", "rtime"])
    print("用例 1 结果:", result1)  # 预期 True

    # 用例 2: 字典中仅包含部分无用键
    testDict2 = {"_id": 123, "mid": 456}
    result2 = check_useless(testDict2, uselessKeys=["_id", "mid", "rtime"])
    print("用例 2 结果:", result2)  # 预期 True

    # 用例 3: 字典中包含无用键以及其它额外键
    testDict3 = {"_id": 123, "mid": 456, "rtime": 789, "name": "Alice"}
    result3 = check_useless(testDict3, uselessKeys=["_id", "mid", "rtime"])
    print("用例 3 结果:", result3)  # 预期 False

    # 用例 4: 空字典
    testDict4 = {}
    result4 = check_useless(testDict4)
    print("用例 4 结果:", result4)  # 预期 True

    # 用例 5: 非字典类型输入
    testDict5 = "不是字典"
    result5 = check_useless(testDict5)
    print("用例 5 结果:", result5)  # 预期 False
