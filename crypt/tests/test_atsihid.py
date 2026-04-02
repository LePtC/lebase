# -*- coding: utf-8 -*-
import os
import unittest

from crypt.atsihid import (
    generate, decode, to_base64, from_base64, sort, vanity,
    _EPOCH_MS,
)

# 固定测试参数
_TEST_KEY = bytes.fromhex("ab" * 32)
_TEST_IP = (192 << 24) | (168 << 16) | (1 << 8) | 100  # 192.168.1.100
_TEST_TIME = 1000  # 1 second after epoch


class TestGenerate(unittest.TestCase):
    def _gen(self, app_id=1, **kw):
        return generate(app_id, _key=_TEST_KEY, _ip=_TEST_IP, _time_ms=_TEST_TIME, **kw)

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
        uid = generate(42, _key=_TEST_KEY, _ip=_TEST_IP, _time_ms=_TEST_TIME)
        info = decode(uid, _key=_TEST_KEY)
        self.assertEqual(info["app_id"], 42)
        self.assertEqual(info["time_ms"], _TEST_TIME)
        self.assertEqual(info["ip"], "192.168.1.100")
        self.assertTrue(info["hmac_ok"])

    def test_tampered_fails_hmac(self):
        uid = generate(1, _key=_TEST_KEY, _ip=_TEST_IP, _time_ms=_TEST_TIME)
        # flip a bit in the obfuscated tail
        bad = uid[:15] + bytes([uid[15] ^ 0x01])
        info = decode(bad, _key=_TEST_KEY)
        self.assertFalse(info["hmac_ok"])

    def test_wrong_key_fails_hmac(self):
        uid = generate(1, _key=_TEST_KEY, _ip=_TEST_IP, _time_ms=_TEST_TIME)
        wrong_key = bytes.fromhex("cd" * 32)
        info = decode(uid, _key=wrong_key)
        self.assertFalse(info["hmac_ok"])

    def test_time_unix(self):
        uid = generate(1, _key=_TEST_KEY, _ip=_TEST_IP, _time_ms=_TEST_TIME)
        info = decode(uid, _key=_TEST_KEY)
        expected_unix = (_EPOCH_MS + _TEST_TIME) / 1000.0
        self.assertAlmostEqual(info["time_unix"], expected_unix, places=3)


class TestBase64(unittest.TestCase):
    def test_roundtrip(self):
        uid = generate(1, _key=_TEST_KEY, _ip=_TEST_IP, _time_ms=_TEST_TIME)
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
        # small value should still produce 22 chars
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
            generate(1, _key=_TEST_KEY, _ip=_TEST_IP, _time_ms=t)
            for t in [1000, 2000, 3000]
        ]
        b64s = [to_base64(u) for u in uids]
        self.assertEqual(b64s, sorted(b64s))


class TestSort(unittest.TestCase):
    def test_sort_by_app_then_time(self):
        uid_a1_t1 = generate(1, _key=_TEST_KEY, _ip=_TEST_IP, _time_ms=1000)
        uid_a1_t2 = generate(1, _key=_TEST_KEY, _ip=_TEST_IP, _time_ms=2000)
        uid_a2_t1 = generate(2, _key=_TEST_KEY, _ip=_TEST_IP, _time_ms=500)

        result = sort([uid_a2_t1, uid_a1_t2, uid_a1_t1])
        self.assertEqual(result[0][:2], (1).to_bytes(2, "big"))  # app 1 first
        self.assertEqual(result[2][:2], (2).to_bytes(2, "big"))  # app 2 last
        # within app 1, t1 < t2
        self.assertLess(result[0][2:8], result[1][2:8])

    def test_sort_reverse(self):
        uids = [
            generate(1, _key=_TEST_KEY, _ip=_TEST_IP, _time_ms=t)
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
            _ip=_TEST_IP,
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
            _ip=_TEST_IP,
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
            _ip=_TEST_IP,
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
            _ip=_TEST_IP,
        )
        elapsed = _time.monotonic() - t0
        self.assertLess(elapsed, 5)  # 应在几秒内返回
        self.assertTrue(len(results) > 0)

    def test_empty_target_raises(self):
        with self.assertRaises(ValueError):
            vanity(app_id=1, target="", _key=_TEST_KEY, _ip=_TEST_IP)

    def test_result_is_valid_atsihid(self):
        """搜索结果应是合法的 ATSIHID (HMAC 校验通过)。"""
        results = vanity(
            app_id=1,
            target="a",
            seconds=0.1,
            time_origin_ms=0,
            max_wall_seconds=10,
            _key=_TEST_KEY,
            _ip=_TEST_IP,
        )
        self.assertTrue(len(results) > 0)
        for r in results[:3]:
            info = decode(r["uid"], _key=_TEST_KEY)
            self.assertTrue(info["hmac_ok"])
            self.assertEqual(info["app_id"], 1)


if __name__ == "__main__":
    unittest.main()
