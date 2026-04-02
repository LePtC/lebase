# -*- coding: utf-8 -*-
import os
import unittest

from crypt.atsihid import (
    generate, decode, to_base64, from_base64, sort, vanity,
    validate_iam, iam_to_32bit, decode_iam_32,
    _EPOCH_MS,
)

# 固定测试参数
_TEST_KEY = bytes.fromhex("ab" * 32)
_TEST_IAM32 = iam_to_32bit("PC01")  # 高 2 位为 0，低 30 位编码 "$PC01"
_TEST_TIME = 1000  # 1 second after epoch


class TestValidateIAM(unittest.TestCase):
    def test_valid(self):
        self.assertTrue(validate_iam("PC01"))
        self.assertTrue(validate_iam("A"))
        self.assertTrue(validate_iam("DEVVM"))
        self.assertTrue(validate_iam("Q2"))

    def test_empty(self):
        self.assertFalse(validate_iam(""))

    def test_reserved(self):
        self.assertFalse(validate_iam("LO"))
        self.assertFalse(validate_iam("UNK"))
        self.assertFalse(validate_iam("VM"))

    def test_starts_with_digit(self):
        self.assertFalse(validate_iam("1PC"))

    def test_lowercase(self):
        self.assertFalse(validate_iam("pc01"))
        self.assertFalse(validate_iam("Pc01"))

    def test_special_chars(self):
        self.assertFalse(validate_iam("PC-01"))
        self.assertFalse(validate_iam("PC_01"))


class TestIAMEncoding(unittest.TestCase):
    def test_roundtrip_short(self):
        """短 IAM 左补 $ 后能正确往返。"""
        for iam in ["A", "PC", "PC01", "Q2"]:
            val = iam_to_32bit(iam)
            self.assertEqual(val >> 30, 0, f"高 2 位应为 0: {iam}")
            decoded = decode_iam_32(val)
            self.assertEqual(decoded, iam, f"往返失败: {iam}")

    def test_roundtrip_exact_5(self):
        """正好 5 字符的 IAM。"""
        iam = "ABCDE"
        val = iam_to_32bit(iam)
        self.assertEqual(decode_iam_32(val), iam)

    def test_truncation(self):
        """超过 5 字符截断前 5 个。"""
        val = iam_to_32bit("ABCDEFGH")
        self.assertEqual(decode_iam_32(val), "ABCDE")

    def test_high_bits_zero(self):
        """所有合法 IAM 编码后高 2 位都为 0。"""
        for iam in ["A", "Z9", "PC01", "ZZZZZ"]:
            val = iam_to_32bit(iam)
            self.assertEqual(val >> 30, 0)


class TestGenerate(unittest.TestCase):
    def _gen(self, app_id=1, **kw):
        return generate(app_id, _key=_TEST_KEY, _iam32=_TEST_IAM32, _time_ms=_TEST_TIME, **kw)

    def test_length(self):
        uid = self._gen()
        self.assertEqual(len(uid), 16)

    def test_app_id_encoded(self):
        uid = self._gen(app_id=0x00FF)
        self.assertEqual(uid[0:2], b"\x00\xff")

    def test_time_encoded(self):
        uid = self._gen()
        t = int.from_bytes(uid[2:8], "big")
        self.assertEqual(t, _TEST_TIME)

    def test_deterministic_with_fixed_seq(self):
        uid1 = self._gen(sequential=True)
        uid2 = self._gen(sequential=True)
        # seq should differ
        self.assertNotEqual(uid1, uid2)

    def test_app_id_out_of_range(self):
        with self.assertRaises(ValueError):
            self._gen(app_id=70000)


class TestDecode(unittest.TestCase):
    def test_roundtrip(self):
        uid = generate(42, _key=_TEST_KEY, _iam32=_TEST_IAM32, _time_ms=_TEST_TIME)
        info = decode(uid, _key=_TEST_KEY)
        self.assertEqual(info["app_id"], 42)
        self.assertEqual(info["time_ms"], _TEST_TIME)
        self.assertTrue(info["is_iam"])
        self.assertEqual(info["iam"], "PC01")
        self.assertTrue(info["hmac_ok"])

    def test_ip_field_also_present(self):
        """即使是 IAM 模式，IP 字段也应有值（供兼容展示）。"""
        uid = generate(1, _key=_TEST_KEY, _iam32=_TEST_IAM32, _time_ms=_TEST_TIME)
        info = decode(uid, _key=_TEST_KEY)
        self.assertIn("ip", info)
        self.assertIsInstance(info["ip"], str)

    def test_traditional_ip_detected(self):
        """高 2 位非零时 is_iam 应为 False。"""
        ip32 = (192 << 24) | (168 << 16) | (1 << 8) | 100  # 192.168.1.100, 高 2 位 = 11
        uid = generate(1, _key=_TEST_KEY, _iam32=ip32, _time_ms=_TEST_TIME)
        info = decode(uid, _key=_TEST_KEY)
        self.assertFalse(info["is_iam"])
        self.assertEqual(info["ip"], "192.168.1.100")
        self.assertTrue(info["hmac_ok"])

    def test_tampered_fails_hmac(self):
        uid = generate(1, _key=_TEST_KEY, _iam32=_TEST_IAM32, _time_ms=_TEST_TIME)
        bad = uid[:15] + bytes([uid[15] ^ 0x01])
        info = decode(bad, _key=_TEST_KEY)
        self.assertFalse(info["hmac_ok"])

    def test_wrong_key_fails_hmac(self):
        uid = generate(1, _key=_TEST_KEY, _iam32=_TEST_IAM32, _time_ms=_TEST_TIME)
        wrong_key = bytes.fromhex("cd" * 32)
        info = decode(uid, _key=wrong_key)
        self.assertFalse(info["hmac_ok"])

    def test_time_unix(self):
        uid = generate(1, _key=_TEST_KEY, _iam32=_TEST_IAM32, _time_ms=_TEST_TIME)
        info = decode(uid, _key=_TEST_KEY)
        expected_unix = (_EPOCH_MS + _TEST_TIME) / 1000.0
        self.assertAlmostEqual(info["time_unix"], expected_unix, places=3)


class TestBase64(unittest.TestCase):
    def test_roundtrip(self):
        uid = generate(1, _key=_TEST_KEY, _iam32=_TEST_IAM32, _time_ms=_TEST_TIME)
        b64 = to_base64(uid)
        self.assertIsInstance(b64, str)
        self.assertEqual(len(b64), 22)
        self.assertEqual(from_base64(b64), uid)

    def test_zero_id(self):
        uid = b"\x00" * 16
        b64 = to_base64(uid)
        self.assertEqual(b64, "$" * 22)
        self.assertEqual(from_base64(b64), uid)

    def test_max_id(self):
        uid = b"\xff" * 16
        b64 = to_base64(uid)
        self.assertEqual(len(b64), 22)
        self.assertEqual(from_base64(b64), uid)

    def test_fixed_length(self):
        uid = b"\x00" * 15 + b"\x01"
        b64 = to_base64(uid)
        self.assertEqual(len(b64), 22)
        self.assertTrue(b64.startswith("$"))
        self.assertEqual(from_base64(b64), uid)

    def test_invalid_char(self):
        with self.assertRaises(ValueError):
            from_base64("!" * 22)

    def test_invalid_length(self):
        with self.assertRaises(ValueError):
            from_base64("abc")

    def test_sort_order_preserved(self):
        """字符串字典序应与字节大端序一致。"""
        uids = [
            generate(1, _key=_TEST_KEY, _iam32=_TEST_IAM32, _time_ms=t)
            for t in [1000, 2000, 3000]
        ]
        b64s = [to_base64(u) for u in uids]
        self.assertEqual(b64s, sorted(b64s))


class TestSort(unittest.TestCase):
    def test_sort_by_app_then_time(self):
        uid_a1_t1 = generate(1, _key=_TEST_KEY, _iam32=_TEST_IAM32, _time_ms=1000)
        uid_a1_t2 = generate(1, _key=_TEST_KEY, _iam32=_TEST_IAM32, _time_ms=2000)
        uid_a2_t1 = generate(2, _key=_TEST_KEY, _iam32=_TEST_IAM32, _time_ms=500)

        result = sort([uid_a2_t1, uid_a1_t2, uid_a1_t1])
        self.assertEqual(result[0][:2], (1).to_bytes(2, "big"))
        self.assertEqual(result[2][:2], (2).to_bytes(2, "big"))
        self.assertLess(result[0][2:8], result[1][2:8])

    def test_sort_reverse(self):
        uids = [
            generate(1, _key=_TEST_KEY, _iam32=_TEST_IAM32, _time_ms=t)
            for t in [100, 300, 200]
        ]
        result = sort(uids, reverse=True)
        times = [int.from_bytes(u[2:8], "big") for u in result]
        self.assertEqual(times, sorted(times, reverse=True))


class TestVanity(unittest.TestCase):
    def test_exact_match(self):
        """搜索 'LPC' 子串 (case-insensitive)，应在合理搜索空间内找到。"""
        results = vanity(
            app_id=1,
            target="LPC",
            seconds=5.0,
            case_sensitive=False,
            time_origin_ms=0,
            max_wall_seconds=30,
            _key=_TEST_KEY,
            _iam32=_TEST_IAM32,
        )
        self.assertTrue(len(results) > 0)
        best = results[0]
        self.assertEqual(best["score"], 3)
        self.assertIn("lpc", best["base64"].lower())

    def test_case_sensitive(self):
        """case_sensitive=True 搜索短子串应能命中。"""
        results = vanity(
            app_id=1,
            target="ab",
            seconds=1.0,
            case_sensitive=True,
            time_origin_ms=0,
            max_wall_seconds=10,
            _key=_TEST_KEY,
            _iam32=_TEST_IAM32,
        )
        self.assertTrue(len(results) > 0)
        best = results[0]
        self.assertEqual(best["score"], 2)
        self.assertIn("ab", best["base64"])

    def test_fuzzy_fallback(self):
        """极短搜索时间 + 长子串 → 应返回模糊候选。"""
        results = vanity(
            app_id=1,
            target="ZZZZZZZZZZ",
            seconds=0.01,
            case_sensitive=True,
            time_origin_ms=0,
            max_wall_seconds=5,
            _key=_TEST_KEY,
            _iam32=_TEST_IAM32,
        )
        self.assertTrue(len(results) > 0)
        self.assertLess(results[0]["score"], 10)

    def test_wall_timeout(self):
        """max_wall_seconds 应限制搜索时间并返回已有结果。"""
        import time as _time
        t0 = _time.monotonic()
        results = vanity(
            app_id=1,
            target="ZZZZZ",
            seconds=100.0,
            case_sensitive=True,
            time_origin_ms=0,
            max_wall_seconds=2,
            _key=_TEST_KEY,
            _iam32=_TEST_IAM32,
        )
        elapsed = _time.monotonic() - t0
        self.assertLess(elapsed, 5)
        self.assertTrue(len(results) > 0)

    def test_empty_target_raises(self):
        with self.assertRaises(ValueError):
            vanity(app_id=1, target="", _key=_TEST_KEY, _iam32=_TEST_IAM32)

    def test_result_is_valid_atsihid(self):
        """搜索结果应是合法的 ATSIHID (HMAC 校验通过)。"""
        results = vanity(
            app_id=1,
            target="a",
            seconds=0.1,
            time_origin_ms=0,
            max_wall_seconds=10,
            _key=_TEST_KEY,
            _iam32=_TEST_IAM32,
        )
        self.assertTrue(len(results) > 0)
        for r in results[:3]:
            info = decode(r["uid"], _key=_TEST_KEY)
            self.assertTrue(info["hmac_ok"])
            self.assertEqual(info["app_id"], 1)


if __name__ == "__main__":
    unittest.main()
