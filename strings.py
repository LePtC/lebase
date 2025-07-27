# -*- coding: utf-8 -*-
"""
Level 0.5（可被 lebase.times 引用）
str开头的接口都是返回string

该文件已重构，函数已移至以下模块：
- lebase.strings.htmls - HTML处理相关函数
- lebase.strings.display - 字符串显示格式化相关函数
- lebase.strings.operates - 字符串操作相关函数
- lebase.strings.safes - 字符串安全处理相关函数
"""

# 为保持向后兼容性，从新模块导入所有函数
from lebase.strings.htmls import *
from lebase.strings.display import *
from lebase.strings.operates import *
from lebase.strings.safes import *


if __name__ == "__main__":
    # 示例用法
    print("字符串模块已正确导入")
    print("sizeof_fmt示例:", sizeof_fmt(1024))
    print("filt_htmltag示例:", filt_htmltag("<p>测试<b>文本</b></p>"))

