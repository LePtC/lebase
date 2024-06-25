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
