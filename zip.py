import os
import zipfile


def zipto(sourceFolder, targetZip, ext=[], deep=False, compressionRate=zipfile.ZIP_DEFLATED):
    """
    创建一个.zip文件，包含指定后缀的文件，或者包含所有文件。
    参数:
    targetZip: 目标.zip文件的完整路径名。
    sourceFolder: 源文件夹的完整路径。
    ext: 一个包含文件后缀名的列表，例如['.txt', '.jpg']。默认为空，表示包含所有文件。
    deep: 是否深入子目录
    """
    with zipfile.ZipFile(targetZip, "w", compressionRate) as zipf:
        # 遍历源文件夹
        for root, dirs, files in os.walk(sourceFolder):
            if not deep:
                dirs[:] = []
            for file in files:
                # 如果ext列表不为空，只包含列表中的文件类型
                if ext and not any(file.endswith(e) for e in ext):
                    continue
                # 获取文件的完整路径
                fullPath = os.path.join(root, file)
                # 获取文件相对于源文件夹的路径
                relativePath = os.path.relpath(fullPath, sourceFolder)
                zipf.write(fullPath, relativePath)
                # print(fullPath)  # debug
            if not deep:
                break

    print(f"文件已被打包到 {targetZip}")


def unzipto(sourceZip, targetFolder):
    """
    解压.zip文件到指定目录。
    参数:
    sourceZip: .zip文件的路径。
    targetFolder: 解压目标目录的路径。
    """
    # 确保目标路径存在
    if not os.path.exists(targetFolder):
        os.makedirs(targetFolder)

    # 打开并解压.zip文件
    with zipfile.ZipFile(sourceZip, "r") as zipRef:
        zipRef.extractall(targetFolder)
        print(f"文件已解压到 {targetFolder}")


if __name__ == "__main__":

    # 使用示例
    # zipto(r"C:\source\folder", r"C:\path\to\your\archive.zip", ext=[".txt", ".jpg"])
    # unzipto(r"C:\path\to\your\file.zip", r"C:\target\path")

    from levar import lev

    zipto(lev.copyto, lev.bykzip / ("掉粉周刊.zip"), [".csv"])
    print("-" * 16)
    zipto(lev.copyto, lev.bykzip / ("掉粉周刊.zip"), [".csv"], True)

    pass
