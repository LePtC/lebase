# -*- coding: utf-8 -*-
import os
import unittest

from crypt.atsihid import (
    generate, decode, to_base58, from_base58, sort,
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


class TestBase58(unittest.TestCase):
    def test_roundtrip(self):
        uid = generate(1, _key=_TEST_KEY, _ip=_TEST_IP, _time_ms=_TEST_TIME)
        b58 = to_base58(uid)
        self.assertIsInstance(b58, str)
        self.assertEqual(from_base58(b58), uid)

    def test_zero_id(self):
        uid = b"\x00" * 16
        b58 = to_base58(uid)
        self.assertEqual(from_base58(b58), uid)

    def test_max_id(self):
        uid = b"\xff" * 16
        b58 = to_base58(uid)
        self.assertEqual(from_base58(b58), uid)

    def test_invalid_char(self):
        with self.assertRaises(ValueError):
            from_base58("0OIl")  # these chars not in base58


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


if __name__ == "__main__":
    unittest.main()
