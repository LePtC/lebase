# -*- coding: utf-8 -*-
"""
字符串操作模块测试
"""
import unittest

from lebase.strings.operates import filt_blank, filt_dup_blank, replace_rule, trim_tail


class TestOperates(unittest.TestCase):

    def test_replace_rule(self):
        """测试replace_rule函数"""
        s = "这是一个测试字符串"
        rule = {"测试": "示例", "字符串": "文本"}
        result = replace_rule(s, rule)
        self.assertEqual(result, "这是一个示例文本")

    def test_trim_tail(self):
        """测试trim_tail函数"""
        s = "这是一个测试字符串测试"
        result = trim_tail(s, "测试")
        self.assertEqual(result, "这是一个测试字符串")

        # 测试不以指定字符串结尾的情况
        s = "这是一个测试字符串"
        result = trim_tail(s, "测试")
        self.assertEqual(result, "这是一个测试字符串")

    def test_filt_blank(self):
        """测试filt_blank函数"""
        s = "这 是\t一个\n测试  字符串\r\n"
        result = filt_blank(s)
        self.assertEqual(result, "这是一个测试字符串")

        # 修复测试，因为函数默认会移除所有类型的空白字符
        s = "这 是\t一个\n测试  字符串\r\n"
        result = filt_blank(s, [" ", "\t"])
        self.assertEqual(result, "这是一个\n测试字符串")

    def test_filt_dup_blank(self):
        """测试filt_dup_blank函数"""
        text = "这  是\n\n\n一个\t\t测试"
        result = filt_dup_blank(text)
        self.assertEqual(result, "这 是\n\n一个\t\t测试")


if __name__ == "__main__":
    unittest.main()
