# encoding=utf-8
"""
用途：
    FileJson类，提供成员变量来存储json文件名和路径
    统一提供叫impo的成员函数，负责读取该文件，检查是否合法的，成功则返回dict
        可选参数：如果读取发现文件不存在，则创建该文件，内容为空，然后返回空dict
TODO：
    统一带创建时间、创建者、最后修改时间、最后修改者等信息
"""
import json
from pathlib import Path


def json_get(file_name):
    with open(file_name, "r", encoding="UTF-8") as f:
        ret = json.load(f)
    return ret


def json_save(dic, filename, mode="w"):

    if not filename.endswith(".json"):
        filename += ".json"
    try:
        with open(filename, mode, encoding="utf-8", newline="") as file:
            json.dump(dic, file, ensure_ascii=False)

    except Exception as e:
        print(f"json_save {filename} error: {e}")

    return 0


class JsonFile(dict):
    def __init__(self, filename, path=""):
        super().__init__()  # 调用父类的构造函数
        self.filename = filename
        self.path = Path(path)
        self.full_path = self.path / filename
        self.impo(create_if_not_exists=True)

    def impo(self, create_if_not_exists=False):
        try:
            with open(self.full_path, "r", encoding="utf-8") as file:
                data = file.read()
                print(f"成功读取了 {len(data)} 字节")
                self.update(self.__validate_json(data))
        except FileNotFoundError:
            if create_if_not_exists:
                with open(self.full_path, "w", encoding="utf-8") as file:
                    file.write("{}")  # 创建一个空的json文件
                print("文件不存在，已创建一个空文件")
            else:
                # raise FileNotFoundError("文件不存在，不做处理")
                print("文件不存在，不做处理")
            return {}

    def expo(self, data_dict, update=True):
        if update:
            for key, value in data_dict.items():
                if key in self:
                    print(f"键 '{key}' 将从 {self[key]} 更新为 {value}")
            self.update(data_dict)
        else:
            self.clear()
            self.update(data_dict)
            print(f"将覆盖 {self.fname} 整个文件更新")
        with open(self.pathfile, "w", encoding="utf-8") as file:
            json.dump(self, file, ensure_ascii=False, indent=4)

    def __validate_json(self, json_data):
        try:
            return json.loads(json_data)
        except json.JSONDecodeError:
            raise ValueError("文件不包含有效的json数据")


if __name__ == "__main__":

    # ----------------------------
    # 测试
    # ----------------------------

    from levar import lev

    json_lefac = JsonFile("lefac.json", lev.appdata)
    print(json_lefac.dic)

    new_data = {"key5": "value5"}
    # json_lefac.expo(new_data)  # 默认追加内容
    json_lefac.expo(new_data, update=False)  # 覆盖内容

    # ----------------------------
    # 生产
    # ----------------------------

    # input("按任意键退出 \n ")
    # print(0)
    pass
