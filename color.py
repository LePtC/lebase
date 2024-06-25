# encoding=utf-8
"""
用途：彩色化打印信息，跨平台
指定类型而非具体颜色，类似css
"""
from colorama import Fore, Back, Style


def info(text):
    return f"{Fore.CYAN}{text}{Style.RESET_ALL}"


def warn(text):
    return f"{Fore.YELLOW}{text}{Style.RESET_ALL}"


def error(text):
    return f"{Fore.RED}{text}{Style.RESET_ALL}"


def critic(text):
    return f"{Back.RED}{text}{Style.RESET_ALL}"


def times(text):
    return f"{Fore.MAGENTA}{text}{Style.RESET_ALL}"


def good(text):
    return f"{Fore.GREEN}{text}{Style.RESET_ALL}"


def prompt(text):
    return f"{Fore.BLUE}{text}{Style.RESET_ALL}"


def high(text):
    return f"{Back.MAGENTA}{text}{Style.RESET_ALL}"


def bold(text):
    return f"{Style.BRIGHT}{text}{Style.RESET_ALL}"


if __name__ == "__main__":

    # ----------------------------
    # 测试
    # ----------------------------

    print(info('这是一条信息'))
    print(warn('这是一个警告'))
    print(error('这是一个错误'))
    print(time('这是时间'))
    print(good("操作成功"))
    print(prompt("请输入您的选择："))
    print(high("重要信息"))
    print(bold("这是加粗的文本"))

    print("─" * 40)  # 使用Unicode字符'─'来打印40个连续的线条

    # ----------------------------
    # 生产
    # ----------------------------

    # input("按任意键退出 \n ")
    # print(0)
    pass
