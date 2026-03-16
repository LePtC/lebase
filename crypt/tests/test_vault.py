# -*- coding: utf-8 -*-
"""
测试 vault.py —— PBKDF2-SHA256 + AES-256-GCM 密码箱
注意：每次 open_vault / append_entry / update_entry / delete_entry 都执行一次 PBKDF2（600k），
      测试耗时较长（每个操作约 1-2s），属正常现象。
"""

import json
import os
import shutil
import tempfile
import unittest

from lebase.crypt.vault import (
    append_entry,
    create_vault,
    decrypt_entry,
    delete_entry,
    derive_vault_key,
    encrypt_entry,
    export_vault,
    open_vault,
    update_entry,
)


class TestVault(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.master = "test_master_password_2026"

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def _tmp(self, name="vault.json"):
        return os.path.join(self.tmpdir, name)

    # ── 低层函数 ─────────────────────────────────────────────────────

    def test_derive_vault_key_length(self):
        """派生密钥应为 32 字节"""
        key = derive_vault_key("password", "AAAAAAAAAAAAAAAAAAAAAA==")
        self.assertEqual(len(key), 32)

    def test_derive_vault_key_deterministic(self):
        """相同密码 + salt → 相同密钥"""
        saltB64 = "AAAAAAAAAAAAAAAAAAAAAA=="
        self.assertEqual(derive_vault_key("pwd", saltB64), derive_vault_key("pwd", saltB64))

    def test_derive_vault_key_different_salts(self):
        """不同 salt → 不同密钥"""
        k1 = derive_vault_key("pwd", "AAAAAAAAAAAAAAAAAAAAAA==")
        k2 = derive_vault_key("pwd", "BAAAAAAAAAAAAAAAAAAAAA==")
        self.assertNotEqual(k1, k2)

    def test_encrypt_decrypt_entry_roundtrip(self):
        """条目加解密还原一致"""
        key = derive_vault_key("pwd", "AAAAAAAAAAAAAAAAAAAAAA==")
        entry = {"name": "mongodb", "host": "1.2.3.4", "pass": "secret", "tag": ["db", "ro"]}
        self.assertEqual(decrypt_entry(key, encrypt_entry(key, entry)), entry)

    def test_encrypt_entry_random_iv(self):
        """每次加密结果不同（随机 IV）"""
        key = derive_vault_key("pwd", "AAAAAAAAAAAAAAAAAAAAAA==")
        entry = {"name": "test"}
        self.assertNotEqual(encrypt_entry(key, entry), encrypt_entry(key, entry))

    # ── create_vault ─────────────────────────────────────────────────

    def test_create_vault_creates_file(self):
        """create_vault 生成有效结构的文件"""
        path = self._tmp()
        create_vault(path, self.master)
        self.assertTrue(os.path.isfile(path))
        data = json.loads(open(path, encoding="utf-8").read())
        self.assertEqual(data["version"], 1)
        self.assertIn("canary", data)
        self.assertIn("kdf", data)
        self.assertEqual(data["entries"], [])

    def test_create_vault_existing_raises(self):
        """文件已存在时抛出 FileExistsError"""
        path = self._tmp()
        create_vault(path, self.master)
        with self.assertRaises(FileExistsError):
            create_vault(path, self.master)

    # ── open_vault ───────────────────────────────────────────────────

    def test_open_vault_empty(self):
        """空密码本返回空列表"""
        path = self._tmp()
        create_vault(path, self.master)
        self.assertEqual(open_vault(path, self.master), [])

    def test_open_vault_wrong_password(self):
        """错误主密码抛出 ValueError"""
        path = self._tmp()
        create_vault(path, self.master)
        with self.assertRaises(ValueError):
            open_vault(path, "wrong_password")

    # ── append_entry ─────────────────────────────────────────────────

    def test_append_and_open(self):
        """追加后能正确读取，含 _id / _created_at / _updated_at 元字段"""
        path = self._tmp()
        create_vault(path, self.master)
        entry = {"name": "mongodb", "host": "1.2.3.4", "pass": "s3cr3t", "tag": ["db"]}
        eid = append_entry(path, self.master, entry)
        entries = open_vault(path, self.master)
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["name"], "mongodb")
        self.assertEqual(entries[0]["pass"], "s3cr3t")
        self.assertEqual(entries[0]["_id"], eid)
        self.assertIn("_created_at", entries[0])
        self.assertIn("_updated_at", entries[0])

    def test_append_multiple(self):
        """多条追加互不干扰"""
        path = self._tmp()
        create_vault(path, self.master)
        for i in range(3):
            append_entry(path, self.master, {"name": f"entry{i}"})
        entries = open_vault(path, self.master)
        self.assertEqual(len(entries), 3)
        self.assertEqual({e["name"] for e in entries}, {"entry0", "entry1", "entry2"})

    # ── update_entry ─────────────────────────────────────────────────

    def test_update_entry(self):
        """更新后内容变更，_updated_at 也更新"""
        path = self._tmp()
        create_vault(path, self.master)
        eid = append_entry(path, self.master, {"name": "old", "pass": "oldpass"})
        ok = update_entry(path, self.master, eid, {"name": "new", "pass": "newpass"})
        self.assertTrue(ok)
        entries = open_vault(path, self.master)
        self.assertEqual(entries[0]["name"], "new")
        self.assertEqual(entries[0]["pass"], "newpass")

    def test_update_entry_not_found(self):
        """更新不存在的 id 返回 False"""
        path = self._tmp()
        create_vault(path, self.master)
        self.assertFalse(update_entry(path, self.master, "no-such-id", {"name": "x"}))

    # ── delete_entry ─────────────────────────────────────────────────

    def test_delete_entry(self):
        """删除后条目消失"""
        path = self._tmp()
        create_vault(path, self.master)
        eid = append_entry(path, self.master, {"name": "todelete"})
        self.assertTrue(delete_entry(path, self.master, eid))
        self.assertEqual(open_vault(path, self.master), [])

    def test_delete_entry_not_found(self):
        """删除不存在的 id 返回 False"""
        path = self._tmp()
        create_vault(path, self.master)
        self.assertFalse(delete_entry(path, self.master, "no-such-id"))

    # ── export_vault ─────────────────────────────────────────────────

    def test_export_vault_all(self):
        """导出全部：新密码可读，旧密码不可读"""
        src = self._tmp("src.json")
        dest = self._tmp("dest.json")
        create_vault(src, self.master)
        append_entry(src, self.master, {"name": "entry1"})
        append_entry(src, self.master, {"name": "entry2"})

        new_master = "new_master_2026"
        export_vault(src, self.master, dest, new_master)

        entries = open_vault(dest, new_master)
        self.assertEqual(len(entries), 2)
        with self.assertRaises(ValueError):
            open_vault(dest, self.master)

    def test_export_vault_partial(self):
        """仅导出选中条目"""
        src = self._tmp("src.json")
        dest = self._tmp("dest.json")
        create_vault(src, self.master)
        id1 = append_entry(src, self.master, {"name": "entry1"})
        append_entry(src, self.master, {"name": "entry2"})
        id3 = append_entry(src, self.master, {"name": "entry3"})

        export_vault(src, self.master, dest, "new_master", entryIds=[id1, id3])
        entries = open_vault(dest, "new_master")
        self.assertEqual(len(entries), 2)
        self.assertEqual({e["name"] for e in entries}, {"entry1", "entry3"})

    def test_export_vault_wrong_source_password(self):
        """源密码错误时抛出 ValueError"""
        src = self._tmp("src.json")
        dest = self._tmp("dest.json")
        create_vault(src, self.master)
        with self.assertRaises(ValueError):
            export_vault(src, "wrong_master", dest, "new_master")

    def test_export_vault_preserves_ids_and_timestamps(self):
        """导出后保留原始 id 和 created_at"""
        src = self._tmp("src.json")
        dest = self._tmp("dest.json")
        create_vault(src, self.master)
        eid = append_entry(src, self.master, {"name": "entry1"})
        export_vault(src, self.master, dest, "new_master")

        entries = open_vault(dest, "new_master")
        self.assertEqual(entries[0]["_id"], eid)


if __name__ == "__main__":
    unittest.main()
