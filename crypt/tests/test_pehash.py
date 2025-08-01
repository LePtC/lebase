# -*- coding: utf-8 -*-
"""
测试 pehash.py 中的关键函数
"""

import unittest

from lebase.crypt.pehash import get_pehash


class TestPeHash(unittest.TestCase):
    """测试 Peter hash 函数"""

    def test_get_pehash_format(self):
        """测试 pehash 输出格式"""
        result = get_pehash()
        self.assertIsInstance(result, str)
        self.assertEqual(len(result), 8)  # 八位大写 16 进制字符串

        # 验证是否为有效的十六进制字符串
        try:
            int(result, 16)
        except ValueError:
            self.fail("pehash 不是有效的十六进制字符串")

    def test_get_pehash_range(self):
        """测试 pehash 值范围"""
        result = get_pehash()
        value = int(result, 16)

        # 根据代码中的 C = 299792458，结果应该小于这个值
        self.assertLess(value, 299792458)

    def test_get_pehash_consistency(self):
        """测试同一天内 pehash 的一致性"""
        # 由于 pehash 基于当前日期，同一天内应该返回相同值
        result1 = get_pehash()
        result2 = get_pehash()
        self.assertEqual(result1, result2)

    def test_get_pehash_hex_case(self):
        """测试 pehash 输出为大写十六进制"""
        result = get_pehash()
        self.assertEqual(result, result.upper())


if __name__ == "__main__":
    unittest.main()
