import csv
from lebase.ensure import ensure_str


def csv_get(file_name):
    with open(file_name, "r", encoding="UTF-8") as f:
        ret = list(csv.reader(f))
    if isinstance(ret[0], list):
        ret[0][0] = ret[0][0].replace("\ufeff", "")
    return ret


def csv_save(li, filename, mode="w+", blank=True):

    if not f"{filename}".endswith(".csv"):
        # filename += ".csv"
        raise ValueError(f"csv_save Error: The file '{filename}' has an invalid extension.")
    try:
        with open(filename, mode, encoding="utf-8", newline="") as file:
            writer = csv.writer(file)
            if isinstance(li[0], list):
                for i in range(len(li)):
                    writer.writerow(list(map(ensure_str, li[i])))
            else:
                for i in range(len(li)):
                    writer.writerow(list(map(ensure_str, [li[i]])))

        if not blank:
            remove_blank_lines(filename)

    except Exception as e:
        print(f"export_list {filename} error: {e}")

    return 0


def remove_blank_lines(filename):
    print("remove_blank_lines", filename)
    # 打开要读取和写入的文件
    # filename = "test.txt"
    with open(filename, encoding="utf-8") as f_input:
        # 读取文件内容并去除末尾的换行符或空格
        data = f_input.read().rstrip("\n")
    with open(filename, "w", encoding="utf-8") as f_output:
        # 写入更新后的文件内容
        f_output.write(data)
