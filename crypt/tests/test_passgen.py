# -*- coding: utf-8 -*-
"""
测试 passgen.py 中的关键函数
"""

import string
import unittest

from lebase.crypt.passgen import generate_random_password


class TestPassGen(unittest.TestCase):
    """测试密码生成函数"""

    def test_generate_random_password_default(self):
        """测试默认参数生成密码"""
        result = generate_random_password(10)
        self.assertEqual(len(result), 10)
        self.assertTrue(all(c in string.ascii_letters + string.digits for c in result))

    def test_generate_random_password_digits(self):
        """测试仅数字密码"""
        result = generate_random_password(8, "1")
        self.assertEqual(len(result), 8)
        self.assertTrue(all(c in string.digits for c in result))

    def test_generate_random_password_letters(self):
        """测试仅字母密码"""
        result = generate_random_password(8, "a")
        self.assertEqual(len(result), 8)
        self.assertTrue(all(c in string.ascii_letters for c in result))

    def test_generate_random_password_alphanumeric(self):
        """测试字母数字密码"""
        result = generate_random_password(8, "1a")
        self.assertEqual(len(result), 8)
        self.assertTrue(all(c in string.ascii_letters + string.digits for c in result))

    def test_generate_random_password_special_chars(self):
        """测试包含特殊字符的密码"""
        result = generate_random_password(8, "1a!")
        self.assertEqual(len(result), 8)
        self.assertTrue(all(c in string.ascii_letters + string.digits + "!@#$%^&*_+<>?=." for c in result))

    def test_generate_random_password_all_punctuation(self):
        """测试包含所有标点符号的密码"""
        result = generate_random_password(8, "1a!~")
        self.assertEqual(len(result), 8)
        self.assertTrue(all(c in string.ascii_letters + string.digits + string.punctuation for c in result))

    def test_generate_random_password_invalid_charset(self):
        """测试无效字符集"""
        result = generate_random_password(8, "invalid")
        self.assertEqual(result, "Invalid character set specified.")

    def test_different_lengths(self):
        """测试不同长度的密码生成"""
        for length in [1, 5, 10, 20]:
            result = generate_random_password(length)
            self.assertEqual(len(result), length)

    def test_zero_length(self):
        """测试长度为0的密码"""
        result = generate_random_password(0)
        self.assertEqual(result, "")


if __name__ == "__main__":
    unittest.main()
