# -*- coding: utf-8 -*-
"""
ATSIHID — 128-bit sortable, verifiable, obfuscated unique ID

Layout (128 bits, big-endian):

    App_16 | Time_48 | Seq_16 | Obfuscated_48
                                  └─ (IAM_32 | HMAC_16) XOR obs

    IAM_32:  高 2 位固定 0，低 30 位为 IAM 标识符的 5 个 base64 字符编码。
             若高 2 位非零，说明该字段存储的是传统 IPv4 地址而非 IAM。
    obs = HMAC-SHA256(key, Time_48)[:6]               — 48-bit obfuscation mask
    HMAC_16 = HMAC-SHA256(key, App|Time|Seq|IAM)[:2]  — 16-bit signature

Epoch: 2026-04-01 00:00:00 UTC  (ms)

Text encoding: custom base64 with ASCII-sorted alphabet
    $0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz_
    Fixed 22-char output, left-padded with '$'. String sort == byte sort.
"""

from __future__ import annotations

import hashlib
import hmac
import os
import re
import secrets
import sys
import threading
import time
import uuid as _uuid_mod
from typing import Optional

# ── Constants ────────────────────────────────────────────────────────

# 2026-04-01 00:00:00 UTC in seconds since Unix epoch
_EPOCH_S = 1_774_982_400
_EPOCH_MS = _EPOCH_S * 1000

_TIME48_MAX = (1 << 48) - 1
_SEQ16_MAX = (1 << 16) - 1

# Custom base64 alphabet — ASCII-sorted so string comparison == byte comparison
_B64_ALPHABET = "$0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz_"
_B64_MAP = {c: i for i, c in enumerate(_B64_ALPHABET)}
_B64_LEN = 22  # ceil(128 / 6) = 22 chars for 128-bit ID

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


# ── IAM helpers ──────────────────────────────────────────────────

_IAM_RESERVED = {"LO", "UNK", "VM"}
_IAM_PATTERN = re.compile(r"^[A-Z][A-Z0-9]*$")
_IAM_CHARS = 5  # IAM 在 ID 中占 5 个 base64 字符 = 30 bits


def validate_iam(s: str) -> bool:
    """校验 IAM 标识符是否合法。

    规则：纯大写字母+数字，必须以大写字母开头，不能为保留词 (LO/UNK/VM)。
    """
    if not s or s in _IAM_RESERVED:
        return False
    return bool(_IAM_PATTERN.match(s))


def _get_mac_32() -> int:
    """获取本机 MAC 地址的低 32 bits。"""
    return _uuid_mod.getnode() & 0xFFFFFFFF


def _mac32_to_iam(mac32: int) -> str:
    """将 32-bit MAC 值编码为 6 个自定义 base64 字符（可直接写入 IAM.txt）。"""
    chars: list[str] = []
    n = mac32
    for _ in range(6):
        chars.append(_B64_ALPHABET[n & 0x3F])
        n >>= 6
    return "".join(reversed(chars))


def iam_to_32bit(iam: str) -> int:
    """IAM 字符串 → 32-bit 整数（高 2 位固定 0，低 30 位为 5 个 base64 字符）。

    不足 5 字符左侧补 '$'(值 0)，超过 5 字符截断前 5 个。
    """
    padded = iam[:_IAM_CHARS].rjust(_IAM_CHARS, "$")
    n = 0
    for ch in padded:
        if ch not in _B64_MAP:
            raise ValueError(f"IAM 包含非法 base64 字符: {ch!r}")
        n = n * 64 + _B64_MAP[ch]
    return n  # 最大 30 bits，高 2 位自然为 0


def decode_iam_32(val: int) -> str:
    """32-bit 整数 → IAM 字符串（去掉左侧 '$' 补位）。"""
    val &= 0x3FFFFFFF  # 取低 30 bits
    chars: list[str] = []
    for _ in range(_IAM_CHARS):
        chars.append(_B64_ALPHABET[val & 0x3F])
        val >>= 6
    return "".join(reversed(chars)).lstrip("$")


def _iam_path() -> str:
    """IAM.txt 的平台路径。"""
    if sys.platform == "win32":
        return os.path.join(os.environ.get("LOCALAPPDATA", ""), "lefac", "IAM.txt")
    return os.path.expanduser("~/.local/etc/lefac/IAM.txt")


def _is_iam_usable(s: str) -> bool:
    """判断 IAM.txt 中的值是否可用（合法的手动 IAM 或 MAC 回退值均可）。"""
    if not s or s == "UNK":
        return False
    # 手动设置的合法 IAM
    if validate_iam(s):
        return True
    # MAC 回退产生的值：所有字符都在 base64 字母表中即可
    return all(ch in _B64_MAP for ch in s)


def _load_iam() -> int:
    """读取 IAM.txt 并返回 32-bit 编码值。

    若 IAM 缺失、为 UNK 或不可用，则用 MAC 后 32 位生成 IAM 并覆写 IAM.txt。
    """
    path = _iam_path()
    iam = ""
    try:
        with open(path, "r", encoding="utf-8") as f:
            iam = f.read().strip()
    except FileNotFoundError:
        pass

    if not _is_iam_usable(iam):
        # MAC 回退
        mac32 = _get_mac_32()
        iam = _mac32_to_iam(mac32)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(iam)

    return iam_to_32bit(iam)


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
             _iam32: Optional[int] = None,
             _time_ms: Optional[int] = None) -> bytes:
    """
    生成一个 128-bit (16 bytes) ATSIHID。

    Args:
        app_id:     16-bit 应用标识 (0 ~ 65535)
        sequential: True 使用单调递增序列号，False 随机生成 (默认)
        _key/_iam32/_time_ms: 测试用覆盖参数

    Returns:
        16 bytes, big-endian
    """
    if not (0 <= app_id <= _SEQ16_MAX):
        raise ValueError(f"app_id 超出范围 [0, 65535]: {app_id}")

    key = _key if _key is not None else _load_key()
    ip32 = _iam32 if _iam32 is not None else _load_iam()
    t48 = _time_ms if _time_ms is not None else _now_ms()

    if t48 < 0 or t48 > _TIME48_MAX:
        raise OverflowError(f"时间戳超出 48-bit 范围: {t48}")

    seq16 = _seq_counter.next() if sequential else secrets.randbelow(1 << 16)

    # ── 基础信息 (112 bits = 14 bytes) ──
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

    32-bit 字段高 2 位为 0 时视为 IAM 编码（低 30 bits = 5 个 base64 字符），
    否则视为传统 IPv4 地址。两种解读均返回，由调用方按需使用。

    Returns:
        {
            "app_id":     int,
            "time_ms":    int,      # 相对于 ATSIHID 纪元的毫秒数
            "time_unix":  float,    # Unix timestamp (秒)
            "seq":        int,
            "field32":    int,      # 原始 32-bit 值
            "is_iam":     bool,     # 高 2 位为 0 → True（可能是 IAM）
            "iam":        str,      # IAM 解读（去掉左侧 $ 补位）
            "ip":         str,      # IP 解读 "x.x.x.x"
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
    field32 = int.from_bytes(plain_tail[0:4], "big")
    hmac_got = plain_tail[4:6]

    # 重建 base_info 验签
    base_info = (
        app_id.to_bytes(2, "big")
        + t48.to_bytes(6, "big")
        + seq16.to_bytes(2, "big")
        + field32.to_bytes(4, "big")
    )
    hmac_expected = _hmac_sha256(key, base_info)[:2]

    # 高 2 位为 0 → 可能是 IAM
    is_iam = (field32 >> 30) == 0
    iam_str = decode_iam_32(field32) if is_iam else ""
    ip_str = f"{(field32 >> 24) & 0xFF}.{(field32 >> 16) & 0xFF}.{(field32 >> 8) & 0xFF}.{field32 & 0xFF}"

    return {
        "app_id": app_id,
        "time_ms": t48,
        "time_unix": (_EPOCH_MS + t48) / 1000.0,
        "seq": seq16,
        "field32": field32,
        "is_iam": is_iam,
        "iam": iam_str,
        "ip": ip_str,
        "hmac_ok": hmac.compare_digest(hmac_got, hmac_expected),
    }


# ── Base64 (custom alphabet) ─────────────────────────────────────────


def to_base64(uid: bytes) -> str:
    """128-bit ATSIHID → 22-char base64 字符串 (自定义 ASCII 有序字母表)。

    固定 22 字符，左补 '$'(值 0)，字符串字典序 == 字节大端序。
    """
    if len(uid) != 16:
        raise ValueError(f"ATSIHID 必须是 16 bytes，收到 {len(uid)}")

    n = int.from_bytes(uid, "big")
    chars: list[str] = []
    for _ in range(_B64_LEN):
        n, r = divmod(n, 64)
        chars.append(_B64_ALPHABET[r])
    return "".join(reversed(chars))


def from_base64(s: str) -> bytes:
    """22-char base64 字符串 → 128-bit ATSIHID (16 bytes)。"""
    if len(s) != _B64_LEN:
        raise ValueError(f"base64 字符串必须是 {_B64_LEN} 字符，收到 {len(s)}")

    n = 0
    for ch in s:
        if ch not in _B64_MAP:
            raise ValueError(f"非法 base64 字符: {ch!r}")
        n = n * 64 + _B64_MAP[ch]

    return n.to_bytes(16, "big")


# ── Sorting ──────────────────────────────────────────────────────────


def sort_key(uid: bytes) -> bytes:
    """排序键 — 直接按字节序 (big-endian) 比较即可。"""
    return uid


def sort(uids: list[bytes], *, reverse: bool = False) -> list[bytes]:
    """对 ATSIHID 列表排序 (按 App → Time → Seq 自然有序)。"""
    return sorted(uids, key=sort_key, reverse=reverse)


# ── Vanity search ───────────────────────────────────────────────────


def _build_substring_table(needle: str, case_sensitive: bool) -> list[list[str]]:
    """预计算 needle 的所有子串，按长度分组 (index 0 = length 1)。"""
    if not case_sensitive:
        needle = needle.lower()
    table: list[list[str]] = []
    for length in range(1, len(needle) + 1):
        subs = []
        for start in range(len(needle) - length + 1):
            subs.append(needle[start:start + length])
        table.append(subs)
    return table


def _fuzzy_score_fast(haystack: str, sub_table: list[list[str]], min_score: int) -> int:
    """返回 needle 在 haystack 中最长连续匹配子串的长度。

    只检查长度 > min_score 的子串（低于 min_score 的不值得入围）。
    """
    for length_idx in range(len(sub_table) - 1, min_score - 1, -1):
        for sub in sub_table[length_idx]:
            if sub in haystack:
                return length_idx + 1  # length = index + 1
    return 0


def _int_to_base64(n: int) -> str:
    """将 128-bit 整数转为 22-char base64 字符串 (内联优化版)。"""
    alph = _B64_ALPHABET
    chars = []
    for _ in range(_B64_LEN):
        chars.append(alph[n & 0x3F])
        n >>= 6
    return "".join(reversed(chars))


def vanity(
    app_id: int,
    target: str,
    *,
    seconds: float = 1.0,
    case_sensitive: bool = True,
    time_origin_ms: Optional[int] = None,
    max_wall_seconds: Optional[float] = None,
    top_n: int = 20,
    _key: Optional[bytes] = None,
    _iam32: Optional[int] = None,
) -> list[dict]:
    """在允许的时间范围内暴力搜索包含指定子串的 ATSIHID。

    在固定 app_id 和时间起点的基础上，遍历 (秒+毫秒+seq) 的全部自由度，
    寻找 base64 编码中包含 target 子串的 ID。

    Args:
        app_id:         16-bit 应用标识
        target:         目标子串
        seconds:        允许搜索的秒数（从 time_origin_ms 开始）
        case_sensitive: 是否严格区分大小写
        time_origin_ms: 搜索起始时间 (相对于 ATSIHID 纪元的毫秒数)，
                        缺省取当前时间
        max_wall_seconds: 最大墙钟搜索时间 (秒)，超时后返回已有最优结果。
                          None 表示不限制 (仅受 seconds 搜索空间限制)
        top_n:          未精确命中时返回的模糊候选数量 (默认 20)
        _key/_iam32:    测试用覆盖参数

    Returns:
        命中列表，每项为 {"uid": bytes, "base64": str, "score": int}。
        score == len(target) 表示精确命中。
        按 score 降序、base64 升序排列。
    """
    if not (0 <= app_id <= _SEQ16_MAX):
        raise ValueError(f"app_id 超出范围 [0, 65535]: {app_id}")
    if not target:
        raise ValueError("target 不能为空")

    key = _key if _key is not None else _load_key()
    ip32 = _iam32 if _iam32 is not None else _load_iam()
    t_start = time_origin_ms if time_origin_ms is not None else _now_ms()

    total_ms = int(seconds * 1000)
    target_len = len(target)
    match_target = target if case_sensitive else target.lower()

    exact_matches: list[dict] = []
    # 模糊候选：保留 top_n 个最高分，(score, base64, uid_int)
    fuzzy: list[tuple[int, str, int]] = []
    fuzzy_min_score = 0

    # 预计算子串表 (用于快速模糊匹配)
    sub_table = _build_substring_table(target, case_sensitive)

    # 预计算常量
    app_hi = app_id << 112  # app_id 在 128-bit 中的位置
    ip_bytes = ip32.to_bytes(4, "big")
    wall_deadline = (time.monotonic() + max_wall_seconds) if max_wall_seconds else None

    _hmac = _hmac_sha256
    _to_b64 = _int_to_base64
    _mono = time.monotonic

    timed_out = False
    for ms_offset in range(total_ms):
        if timed_out:
            break
        t48 = t_start + ms_offset
        if t48 < 0 or t48 > _TIME48_MAX:
            continue

        time_bytes = t48.to_bytes(6, "big")
        obs = _hmac(key, time_bytes)[:6]
        obs_ip = bytes(a ^ b for a, b in zip(ip_bytes, obs[:4]))
        obs_ip_int = int.from_bytes(obs_ip, "big")
        obs_tail_0 = obs[4]
        obs_tail_1 = obs[5]

        # uid 高 80 bits 中，app + time 部分是常量
        prefix = app_hi | (t48 << 64)
        # masked_ip 在 uid 的 bit[16..48] 区间
        masked_ip_shifted = obs_ip_int << 16

        app_time_bytes = app_id.to_bytes(2, "big") + time_bytes

        for seq16 in range(1 << 16):
            # 每 4096 次检查一次墙钟时间
            if wall_deadline and (seq16 & 0xFFF) == 0 and _mono() >= wall_deadline:
                timed_out = True
                break

            hmac_16 = _hmac(key, app_time_bytes + seq16.to_bytes(2, "big") + ip_bytes)[:2]
            xored_hmac = (hmac_16[0] ^ obs_tail_0) << 8 | (hmac_16[1] ^ obs_tail_1)

            uid_int = prefix | (seq16 << 48) | masked_ip_shifted | xored_hmac
            b64 = _to_b64(uid_int)

            haystack = b64 if case_sensitive else b64.lower()
            if match_target in haystack:
                uid = uid_int.to_bytes(16, "big")
                exact_matches.append({
                    "uid": uid, "base64": b64, "score": target_len,
                })
                if len(exact_matches) >= top_n:
                    return exact_matches
            elif len(fuzzy) < top_n or fuzzy_min_score < target_len:
                score = _fuzzy_score_fast(haystack, sub_table, fuzzy_min_score)
                if score > 0 and (len(fuzzy) < top_n or score > fuzzy_min_score):
                    if len(fuzzy) < top_n:
                        fuzzy.append((score, b64, uid_int))
                        if len(fuzzy) == top_n:
                            fuzzy.sort(key=lambda x: (-x[0], x[1]))
                            fuzzy_min_score = fuzzy[-1][0]
                    else:
                        fuzzy[-1] = (score, b64, uid_int)
                        fuzzy.sort(key=lambda x: (-x[0], x[1]))
                        fuzzy_min_score = fuzzy[-1][0]

    if exact_matches:
        return exact_matches

    fuzzy.sort(key=lambda x: (-x[0], x[1]))
    return [
        {"uid": uid_int.to_bytes(16, "big"), "base64": b64, "score": score}
        for score, b64, uid_int in fuzzy
    ]


# ── CLI demo ─────────────────────────────────────────────────────────

if __name__ == "__main__":
    uid = generate(app_id=1)
    b64 = to_base64(uid)
    info = decode(uid)
    print(f"ID (hex):    {uid.hex()}")
    print(f"ID (base64): {b64}")
    print(f"IAM:         {info['iam']}")
    print(f"Decoded:     {info}")

    # round-trip
    assert from_base64(b64) == uid
    assert info["hmac_ok"]
    print("Round-trip OK")
