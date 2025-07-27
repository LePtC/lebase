# -*- coding: utf-8 -*-
"""
字符串解析模块测试
"""
import unittest

from lebase.strings.parsers import parse_numbers, parse_urls


class TestParsers(unittest.TestCase):

    def test_parse_numbers(self):
        """测试parse_numbers函数"""
        # 测试基本数字提取
        input_string = "UID303266889 UID3546816515672666"
        result = parse_numbers(input_string)
        self.assertEqual(result, [303266889, 3546816515672666])

        # 测试混合文本
        input_string = "测试123文本456测试789"
        result = parse_numbers(input_string)
        self.assertEqual(result, [123, 456, 789])

        # 测试无数字的情况
        input_string = "测试文本"
        result = parse_numbers(input_string)
        self.assertEqual(result, [])

    def test_parse_urls(self):
        """测试parse_urls函数"""
        # 测试HTTP URL
        text = "访问 http://example.com 和 https://test.com"
        result = parse_urls(text)
        self.assertEqual(result, ["http://example.com", "https://test.com"])

        # 测试FTP URL
        text = "下载 ftp://ftp.example.com/file.txt"
        result = parse_urls(text)
        self.assertEqual(result, ["ftp://ftp.example.com/file.txt"])

        # 测试WWW URL
        text = "访问 www.example.com"
        result = parse_urls(text)
        self.assertEqual(result, ["www.example.com"])

        # 测试混合URL
        text = "链接1: http://example.com 链接2: ftp://ftp.test.com 链接3: www.demo.com"
        result = parse_urls(text)
        expected = ["http://example.com", "ftp://ftp.test.com", "www.demo.com"]
        self.assertEqual(result, expected)

        # 测试无URL的情况
        text = "这是普通文本"
        result = parse_urls(text)
        self.assertEqual(result, [])


if __name__ == "__main__":
    unittest.main()
