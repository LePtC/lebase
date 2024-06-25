# encoding=utf-8
"""
Level 0.5（可被 lebase.times 引用）
times 更高阶，因此 ensure_taskId 放在 times
"""
import math
import io


def ensure_str(s):
    """
    一个比 str 更普适的强制字符串转换（对于 MongoId Object 可以返回 print 出的字串）
    """
    if isinstance(s, str):
        return s
    elif isinstance(s, (int, float)):  # 自动控制在4位小数格式，如果不需要那可以直接用 str
        return ensure_numstr(s)
    else:
        try:
            return str(s)
        except Exception:
            return print2str(s)


def print2str(*args, **kwargs):
    """
    cite: https://stackoverflow.com/questions/39823303/python3-print-to-string
    """
    output = io.StringIO()
    print(*args, file=output, **kwargs)
    contents = output.getvalue()
    output.close()
    return contents


def ensure_li(strOrLi):
    if isinstance(strOrLi, list):
        li = strOrLi
    else:
        li = [strOrLi]
    return li


def is_number(s):
    try:
        x = float(s)
        if math.isnan(x):
            return False
        return True
    # except ValueError:
    except Exception:
        return False


def ensure_num(strOrNum):
    """
    确保是数
    """
    if isinstance(strOrNum, int) or isinstance(strOrNum, float):
        return strOrNum
    else:
        try:
            return float(strOrNum)
        except Exception as e:
            print(f"ensure.num error: {e}")
            return -1


def ensure_numstr(strOrNum, tofix=4):
    """
    如果传入的是字符串，则返回字符串
    如果是 int，则返回无小数位字符串
    如果是 float，则返回默认4小数位字符串
    """
    if not is_number(strOrNum):
        return strOrNum
    if isinstance(strOrNum, int):
        return str(strOrNum)  # format(strOrNum,'.0f')
    return format(float(strOrNum), "." + str(int(tofix)) + "f")


def ensure_quoted(path):
    # 检查路径两端是否有引号
    if not (path.startswith('"') and path.endswith('"')):
        return f'"{path}"'  # 添加引号
    return path  # 已有引号，直接返回


if __name__ == "__main__":

    # 示例使用
    path_with_quotes = '"C:\\Program Files\\MyApp\\app.exe"'
    path_without_quotes = "C:\\Program Files\\MyApp\\app.exe"

    print(ensure_quoted(path_with_quotes))  # 输出： "C:\\Program Files\\MyApp\\app.exe"
    print(ensure_quoted(path_without_quotes))  # 输出： "C:\\Program Files\\MyApp\\app.exe"
