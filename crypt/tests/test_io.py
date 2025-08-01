# -*- coding: utf-8 -*-
"""
测试 io.py 中的关键函数
"""

import unittest

from lebase.crypt.io import decrypt_password, derive_key, encrypt_password


class TestIO(unittest.TestCase):
    """测试密码加解密函数"""

    def test_derive_key(self):
        """测试密钥派生函数"""
        master_password = "test_master_password"  # noqa: S105
        salt = b"test_salt_16_bytes"

        key = derive_key(master_password, salt)
        self.assertIsInstance(key, bytes)
        self.assertEqual(len(key), 44)  # Fernet 密钥长度为 44 字节

    def test_encrypt_and_decrypt_password(self):
        """测试密码加密和解密"""
        master_password = "test_master_password"  # noqa: S105
        plain_password = "test_plain_password"  # noqa: S105

        # 加密
        encrypted = encrypt_password(master_password, plain_password)
        self.assertIsInstance(encrypted, str)
        self.assertIn(":", encrypted)  # 格式为 salt:encrypted_data

        # 解密
        decrypted = decrypt_password(master_password, encrypted)
        self.assertEqual(decrypted, plain_password)

    def test_encrypt_decrypt_with_special_chars(self):
        """测试包含特殊字符的密码加密解密"""
        master_password = "master!@#$%"  # noqa: S105
        plain_password = "plain!@#$%^&*()"  # noqa: S105

        encrypted = encrypt_password(master_password, plain_password)
        decrypted = decrypt_password(master_password, encrypted)
        self.assertEqual(decrypted, plain_password)

    def test_encrypt_decrypt_with_unicode(self):
        """测试包含Unicode字符的密码加密解密"""
        master_password = "主密码"  # noqa: S105
        plain_password = "明文密码123"  # noqa: S105

        encrypted = encrypt_password(master_password, plain_password)
        decrypted = decrypt_password(master_password, encrypted)
        self.assertEqual(decrypted, plain_password)

    def test_decrypt_with_wrong_master_password(self):
        """测试使用错误的主密码解密"""
        master_password = "correct_master_password"  # noqa: S105
        plain_password = "test_password"  # noqa: S105

        encrypted = encrypt_password(master_password, plain_password)

        # 使用错误的主密码解密
        wrong_master = "wrong_master_password"
        decrypted = decrypt_password(wrong_master, encrypted)
        self.assertIsNone(decrypted)

    def test_decrypt_invalid_format(self):
        """测试解密格式错误的密文"""
        master_password = "test_master_password"  # noqa: S105

        # 测试格式错误的密文
        invalid_encrypted = "invalid_format"
        decrypted = decrypt_password(master_password, invalid_encrypted)
        self.assertIsNone(decrypted)

    def test_derive_key_different_salts(self):
        """测试不同salt生成的密钥不同"""
        master_password = "test_master_password"  # noqa: S105
        salt1 = b"salt1_16_bytes_"
        salt2 = b"salt2_16_bytes_"

        key1 = derive_key(master_password, salt1)
        key2 = derive_key(master_password, salt2)

        self.assertNotEqual(key1, key2)


if __name__ == "__main__":
    unittest.main()
