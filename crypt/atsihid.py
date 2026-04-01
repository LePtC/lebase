# -*- coding: utf-8 -*-
"""
ATSIHID — 128-bit sortable, verifiable, obfuscated unique ID

Layout (128 bits, big-endian):

    App_16 | Time_48 | Seq_16 | Obfuscated_48
                                  └─ (IP_32 | HMAC_16) XOR obs

    obs = HMAC-SHA256(key, Time_48)[:6]          — 48-bit obfuscation mask
    HMAC_16 = HMAC-SHA256(key, App|Time|Seq|IP)[:2]  — 16-bit signature

Epoch: 2026-04-01 00:00:00 UTC  (ms)
"""

from __future__ import annotations

import hashlib
import hmac
import os
import secrets
import struct
import sys
import threading
import time
from typing import Optional

# ── Constants ────────────────────────────────────────────────────────

# 2026-04-01 00:00:00 UTC in seconds since Unix epoch
_EPOCH_S = 1_774_982_400
_EPOCH_MS = _EPOCH_S * 1000

_TIME48_MAX = (1 << 48) - 1
_SEQ16_MAX = (1 << 16) - 1

# Bitcoin base58 alphabet
_B58_ALPHABET = b"123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
_B58_MAP = {c: i for i, c in enumerate(_B58_ALPHABET)}

# ── Internal helpers ─────────────────────────────────────────────────


def _load_key() -> bytes:
    """从环境变量 LEFAC_256 读取 256-bit key。"""
    raw = os.environ.get("LEFAC_256")
    if not raw:
        raise RuntimeError("环境变量 LEFAC_256 未设置，请先运行 setup/init_lefac_256.py")
    return bytes.fromhex(raw)


def _load_ip() -> int:
    """从落盘文件读取公网 IPv4，返回 32-bit 整数。"""
    if sys.platform == "win32":
        ip_path = os.path.join(os.environ.get("LOCALAPPDATA", ""), "lefac", "ip_public.txt")
    else:
        ip_path = os.path.expanduser("~/.local/etc/lefac/ip_public.txt")
    try:
        with open(ip_path, "r", encoding="utf-8") as f:
            ip_str = f.read().strip()
    except FileNotFoundError:
        raise RuntimeError(f"公网 IP 文件不存在: {ip_path}，请先运行 setup/init_public_ip")
    parts = ip_str.split(".")
    if len(parts) != 4:
        raise ValueError(f"无效的 IPv4 地址: {ip_str}")
    return (int(parts[0]) << 24) | (int(parts[1]) << 16) | (int(parts[2]) << 8) | int(parts[3])


def _hmac_sha256(key: bytes, data: bytes) -> bytes:
    return hmac.new(key, data, hashlib.sha256).digest()


def _now_ms() -> int:
    return int(time.time() * 1000) - _EPOCH_MS


# ── Sequence counter ────────────────────────────────────────────────


class _SeqCounter:
    """线程安全的 16-bit 单调递增计数器。"""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._val = 0

    def next(self) -> int:
        with self._lock:
            v = self._val
            self._val = (self._val + 1) & _SEQ16_MAX
            return v


_seq_counter = _SeqCounter()

# ── Core: generate / decode ──────────────────────────────────────────


def generate(app_id: int, *, sequential: bool = False,
             _key: Optional[bytes] = None,
             _ip: Optional[int] = None,
             _time_ms: Optional[int] = None) -> bytes:
    """
    生成一个 128-bit (16 bytes) ATSIHID。

    Args:
        app_id:     16-bit 应用标识 (0 ~ 65535)
        sequential: True 使用单调递增序列号，False 随机生成 (默认)
        _key/_ip/_time_ms: 测试用覆盖参数

    Returns:
        16 bytes, big-endian
    """
    if not (0 <= app_id <= _SEQ16_MAX):
        raise ValueError(f"app_id 超出范围 [0, 65535]: {app_id}")

    key = _key if _key is not None else _load_key()
    ip32 = _ip if _ip is not None else _load_ip()
    t48 = _time_ms if _time_ms is not None else _now_ms()

    if t48 < 0 or t48 > _TIME48_MAX:
        raise OverflowError(f"时间戳超出 48-bit 范围: {t48}")

    seq16 = _seq_counter.next() if sequential else secrets.randbelow(1 << 16)

    # ── 基础信息 (112 bits = 14 bytes) ──
    base_info = struct.pack(">HQ", app_id, t48)[: 2 + 6]  # App_16 + Time_48 (取低6字节)
    # 更精确的做法：手动拼
    base_info = (
        app_id.to_bytes(2, "big")
        + t48.to_bytes(6, "big")
        + seq16.to_bytes(2, "big")
        + ip32.to_bytes(4, "big")
    )  # 14 bytes

    # ── HMAC_16: 签名 ──
    hmac_16 = _hmac_sha256(key, base_info)[:2]  # 前 2 bytes = 16 bits

    # ── obs: 混淆掩码 ──
    obs = _hmac_sha256(key, t48.to_bytes(6, "big"))[:6]  # 前 6 bytes = 48 bits

    # ── 混淆: (IP_32 | HMAC_16) XOR obs ──
    plain_tail = ip32.to_bytes(4, "big") + hmac_16  # 6 bytes
    obfuscated = bytes(a ^ b for a, b in zip(plain_tail, obs))

    # ── 最终 128-bit ID ──
    return (
        app_id.to_bytes(2, "big")
        + t48.to_bytes(6, "big")
        + seq16.to_bytes(2, "big")
        + obfuscated
    )


def decode(uid: bytes, *, _key: Optional[bytes] = None) -> dict:
    """
    解码 128-bit ATSIHID，返回各字段及签名校验结果。

    Returns:
        {
            "app_id":     int,
            "time_ms":    int,      # 相对于 ATSIHID 纪元的毫秒数
            "time_unix":  float,    # Unix timestamp (秒)
            "seq":        int,
            "ip":         str,      # "x.x.x.x"
            "ip_int":     int,
            "hmac_ok":    bool,     # 签名是否通过
        }
    """
    if len(uid) != 16:
        raise ValueError(f"ATSIHID 必须是 16 bytes，收到 {len(uid)}")

    key = _key if _key is not None else _load_key()

    app_id = int.from_bytes(uid[0:2], "big")
    t48 = int.from_bytes(uid[2:8], "big")
    seq16 = int.from_bytes(uid[8:10], "big")
    obfuscated = uid[10:16]  # 6 bytes

    # 还原: obs XOR
    obs = _hmac_sha256(key, t48.to_bytes(6, "big"))[:6]
    plain_tail = bytes(a ^ b for a, b in zip(obfuscated, obs))
    ip32 = int.from_bytes(plain_tail[0:4], "big")
    hmac_got = plain_tail[4:6]

    # 重建 base_info 验签
    base_info = (
        app_id.to_bytes(2, "big")
        + t48.to_bytes(6, "big")
        + seq16.to_bytes(2, "big")
        + ip32.to_bytes(4, "big")
    )
    hmac_expected = _hmac_sha256(key, base_info)[:2]

    ip_str = f"{(ip32 >> 24) & 0xFF}.{(ip32 >> 16) & 0xFF}.{(ip32 >> 8) & 0xFF}.{ip32 & 0xFF}"

    return {
        "app_id": app_id,
        "time_ms": t48,
        "time_unix": (_EPOCH_MS + t48) / 1000.0,
        "seq": seq16,
        "ip": ip_str,
        "ip_int": ip32,
        "hmac_ok": hmac.compare_digest(hmac_got, hmac_expected),
    }


# ── Base58 ───────────────────────────────────────────────────────────


def to_base58(uid: bytes) -> str:
    """128-bit ATSIHID → Base58 字符串 (Bitcoin alphabet)。"""
    if len(uid) != 16:
        raise ValueError(f"ATSIHID 必须是 16 bytes，收到 {len(uid)}")

    n = int.from_bytes(uid, "big")
    if n == 0:
        return _B58_ALPHABET[0:1].decode()

    chars: list[int] = []
    while n > 0:
        n, r = divmod(n, 58)
        chars.append(_B58_ALPHABET[r])
    # 前导零字节 → 前导 '1'
    for b in uid:
        if b == 0:
            chars.append(_B58_ALPHABET[0])
        else:
            break
    return bytes(reversed(chars)).decode()


def from_base58(s: str) -> bytes:
    """Base58 字符串 → 128-bit ATSIHID (16 bytes)。"""
    n = 0
    for ch in s.encode():
        if ch not in _B58_MAP:
            raise ValueError(f"非法 Base58 字符: {chr(ch)}")
        n = n * 58 + _B58_MAP[ch]

    # 前导 '1' → 前导零字节
    leading_zeros = 0
    for ch in s.encode():
        if ch == _B58_ALPHABET[0]:
            leading_zeros += 1
        else:
            break

    raw = n.to_bytes((n.bit_length() + 7) // 8, "big") if n > 0 else b""
    result = b"\x00" * leading_zeros + raw

    # 填充或截断到 16 bytes
    if len(result) > 16:
        raise ValueError(f"Base58 解码结果超过 16 bytes: {len(result)}")
    return result.rjust(16, b"\x00")


# ── Sorting ──────────────────────────────────────────────────────────


def sort_key(uid: bytes) -> bytes:
    """排序键 — 直接按字节序 (big-endian) 比较即可。"""
    return uid


def sort(uids: list[bytes], *, reverse: bool = False) -> list[bytes]:
    """对 ATSIHID 列表排序 (按 App → Time → Seq 自然有序)。"""
    return sorted(uids, key=sort_key, reverse=reverse)


# ── CLI demo ─────────────────────────────────────────────────────────

if __name__ == "__main__":
    uid = generate(app_id=1)
    b58 = to_base58(uid)
    info = decode(uid)
    print(f"ID (hex):    {uid.hex()}")
    print(f"ID (base58): {b58}")
    print(f"Decoded:     {info}")

    # round-trip
    assert from_base58(b58) == uid
    assert info["hmac_ok"]
    print("Round-trip OK")
