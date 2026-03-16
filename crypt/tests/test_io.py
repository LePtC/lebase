# -*- coding: utf-8 -*-
"""
测试 io.py 中的关键函数（PBKDF2-SHA256 600k + AES-256-GCM）
"""

import unittest

from lebase.crypt.io import decrypt_password, derive_key, encrypt_password


class TestIO(unittest.TestCase):
    """测试密码加解密函数"""

    def test_derive_key_length(self):
        """派生密钥应为 32 字节（AES-256）"""
        key = derive_key("test_master_password", b"test_salt_16byte")
        self.assertIsInstance(key, bytes)
        self.assertEqual(len(key), 32)

    def test_derive_key_deterministic(self):
        """相同密码 + salt 应得到相同密钥"""
        salt = b"fixed_salt_16byt"
        key1 = derive_key("same_password", salt)
        key2 = derive_key("same_password", salt)
        self.assertEqual(key1, key2)

    def test_derive_key_different_salts(self):
        """不同 salt 应得到不同密钥"""
        key1 = derive_key("same_password", b"salt1_16_bytes__")
        key2 = derive_key("same_password", b"salt2_16_bytes__")
        self.assertNotEqual(key1, key2)

    def test_encrypt_format(self):
        """加密结果应为 salt:iv:ciphertext 三段格式"""
        encrypted = encrypt_password("master", "plain")
        parts = encrypted.split(":")
        self.assertEqual(len(parts), 3)
        # 每段应为合法 base64url
        for part in parts:
            self.assertGreater(len(part), 0)

    def test_encrypt_produces_different_output(self):
        """相同输入每次加密结果应不同（随机 salt + IV）"""
        enc1 = encrypt_password("master", "plain")
        enc2 = encrypt_password("master", "plain")
        self.assertNotEqual(enc1, enc2)

    def test_encrypt_decrypt_roundtrip(self):
        """加密后能正确解密还原明文"""
        master = "test_master_password"  # noqa: S105
        plain = "test_plain_password"  # noqa: S105
        encrypted = encrypt_password(master, plain)
        self.assertEqual(decrypt_password(master, encrypted), plain)

    def test_encrypt_decrypt_special_chars(self):
        """包含特殊字符的密码能正确加解密"""
        master = "master!@#$%"  # noqa: S105
        plain = "plain!@#$%^&*()"  # noqa: S105
        encrypted = encrypt_password(master, plain)
        self.assertEqual(decrypt_password(master, encrypted), plain)

    def test_encrypt_decrypt_unicode(self):
        """包含中文等 Unicode 字符的密码能正确加解密"""
        master = "主密码"  # noqa: S105
        plain = "明文密码123"  # noqa: S105
        encrypted = encrypt_password(master, plain)
        self.assertEqual(decrypt_password(master, encrypted), plain)

    def test_wrong_master_password(self):
        """错误主密码解密应返回 None（GCM 认证失败）"""
        encrypted = encrypt_password("correct_master", "secret")  # noqa: S105
        self.assertIsNone(decrypt_password("wrong_master", encrypted))

    def test_tampered_ciphertext(self):
        """篡改密文后解密应返回 None（GCM 完整性校验）"""
        encrypted = encrypt_password("master", "secret")  # noqa: S105
        salt, iv, ct = encrypted.split(":")
        tampered = salt + ":" + iv + ":" + ct[:-4] + "AAAA"
        self.assertIsNone(decrypt_password("master", tampered))

    def test_invalid_format(self):
        """格式错误的密文解密应返回 None"""
        self.assertIsNone(decrypt_password("master", "invalid_format"))
        self.assertIsNone(decrypt_password("master", "only:two"))


if __name__ == "__main__":
    unittest.main()
