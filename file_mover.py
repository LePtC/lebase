# encoding=utf-8
"""
本文件的用途：
把新爬下来的头像合入base，合入时自动检查哪些是有更新的加以重命名
"""

import os
import shutil
from datetime import datetime

from lebase.strings import strli


def filemove_rename(pathSrc, pathDst, ext_=".png"):
    """传入 .ext 必须带点"""
    if "." in ext_:
        ext = ext_
    else:
        ext = "." + ext_

    # 初始化计数器
    total_png_files = 0
    moved_files = 0
    renamed_and_moved_files = 0
    skipped_files = 0
    renamed_files_list = []

    # 确保目标路径存在
    # if not os.path.exists(pathDst):
    #     os.makedirs(pathDst)

    # 遍历源目录中的所有文件
    for file_name in os.listdir(pathSrc):
        if file_name.endswith(ext):
            total_png_files += 1
            source_file = os.path.join(pathSrc, file_name)
            target_file = os.path.join(pathDst, file_name)

            # 检查文件是否已经存在于目标目录
            if os.path.exists(target_file):
                # 比较文件大小
                if os.path.getsize(source_file) != os.path.getsize(target_file):
                    # 获取现有文件的创建日期 ctime，update: 修改日期 mtime 似乎更准确
                    creation_date = datetime.fromtimestamp(os.path.getmtime(target_file)).strftime("%Y%m%d")

                    # 如果直接使用file_name，会得到example.png-yyyymmdd.png这样的文件名
                    new_name = f"{os.path.splitext(file_name)[0]}-{creation_date}{ext}"
                    new_target_file = os.path.join(pathDst, new_name)
                    if os.path.exists(new_target_file):
                        # 如果要重命名的目标也存在，则不用执行啥了，回头可手动删
                        print("[warn] 重命名的也存在:", new_target_file)
                    else:
                        os.rename(target_file, new_target_file)
                        renamed_files_list.append(new_name)
                        # 移动新文件
                        shutil.move(source_file, target_file)
                        renamed_and_moved_files += 1
                else:
                    # 如果大小相同，则跳过文件
                    skipped_files += 1
                    # update: 如果大小相同，则删除源文件
                    os.remove(source_file)
            else:
                # 如果目标目录中不存在文件，则移动新文件
                shutil.move(source_file, target_file)
                moved_files += 1

    # 打印总结信息
    print(f"在'{pathSrc}'路径下的总.png文件数: {total_png_files}")
    print(f"直接移动到'{pathDst}'的文件数: {moved_files}")
    print(f"重命名并移动到'{pathDst}'的文件数: {renamed_and_moved_files}")
    print(f"由于大小完全相同而跳过的文件数: {skipped_files}")
    if renamed_files_list:
        print("重命名的文件:", strli(renamed_files_list))


def filemove_overwrite(pathSrc, pathDst, ext=".png"):
    count = 0
    # 遍历源目录中的所有文件
    for file_name in os.listdir(pathSrc):
        if file_name.endswith(ext):
            source_file = os.path.join(pathSrc, file_name)
            target_file = os.path.join(pathDst, file_name)

            # 移动文件，如果有同名文件则覆盖
            shutil.move(source_file, target_file)
            count += 1

    print(f"filemove_overwrite: {count}个{ext}文件已从'{pathSrc}'移动到'{pathDst}'")


def filemove_copy(pathSrc, pathDst, ext=".png"):
    count = 0
    # 遍历源目录中的所有文件
    for file_name in os.listdir(pathSrc):
        if file_name.endswith(ext):
            source_file = os.path.join(pathSrc, file_name)
            target_file = os.path.join(pathDst, file_name)

            # 复制文件，如果有同名文件则覆盖
            shutil.copy2(source_file, target_file)
            count += 1

    print(f"filemove_copy: {count}个{ext}文件已从'{pathSrc}'拷贝覆盖到'{pathDst}'")


if __name__ == "__main__":

    # from levar import lev
    # filemove_rename(lev.copyto, lev.picbase)

    pass
