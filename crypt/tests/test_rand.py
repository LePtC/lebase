# -*- coding: utf-8 -*-
"""
测试 rand.py 中的关键函数
"""

import string
import unittest

from lebase.crypt.rand import generate_random_string, generate_random_string_choices


class TestRand(unittest.TestCase):
    """测试随机字符串生成函数"""

    def test_generate_random_string(self):
        """测试基本随机字符串生成"""
        # 测试默认字符集
        result = generate_random_string(10)
        self.assertEqual(len(result), 10)
        self.assertTrue(all(c in string.ascii_letters + string.digits for c in result))

        # 测试自定义字符集
        result = generate_random_string(5, "abc")
        self.assertEqual(len(result), 5)
        self.assertTrue(all(c in "abc" for c in result))

    def test_generate_random_string_choices(self):
        """测试带字符集选项的随机字符串生成"""
        # 测试数字
        result = generate_random_string_choices(8, "1")
        self.assertEqual(len(result), 8)
        self.assertTrue(all(c in string.digits for c in result))

        # 测试字母
        result = generate_random_string_choices(8, "a")
        self.assertEqual(len(result), 8)
        self.assertTrue(all(c in string.ascii_letters for c in result))

        # 测试字母和数字
        result = generate_random_string_choices(8, "1a")
        self.assertEqual(len(result), 8)
        self.assertTrue(all(c in string.ascii_letters + string.digits for c in result))

        # 测试包含特殊字符
        result = generate_random_string_choices(8, "1a!")
        self.assertEqual(len(result), 8)
        self.assertTrue(all(c in string.ascii_letters + string.digits + "!@#$%^&*_+<>?=." for c in result))

    def test_different_lengths(self):
        """测试不同长度的字符串生成"""
        for length in [1, 5, 10, 20]:
            result = generate_random_string(length)
            self.assertEqual(len(result), length)

            result = generate_random_string_choices(length)
            self.assertEqual(len(result), length)

    def test_empty_string(self):
        """测试长度为0的字符串生成"""
        result = generate_random_string(0)
        self.assertEqual(result, "")

        result = generate_random_string_choices(0)
        self.assertEqual(result, "")


if __name__ == "__main__":
    unittest.main()
