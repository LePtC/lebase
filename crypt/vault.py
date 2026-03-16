import base64
import json
import os
import uuid
from datetime import datetime, timezone

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from lelog.logs import log

_CANARY_PLAIN = "vault-canary-v1"
_KDF_ALGO = "PBKDF2-SHA256"
_KDF_ITERATIONS = 600000
_KEY_LEN = 32


def _b64e(b: bytes) -> str:
    return base64.urlsafe_b64encode(b).decode()


def _b64d(s: str) -> bytes:
    return base64.urlsafe_b64decode(s)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def derive_vault_key(masterPassword: str, saltB64: str, iterations: int = _KDF_ITERATIONS) -> bytes:
    """从主密码和 base64url 编码的 salt 派生 32 字节 AES-256 密钥（PBKDF2-SHA256，仅执行一次）"""
    kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=_KEY_LEN, salt=_b64d(saltB64), iterations=iterations)
    return kdf.derive(masterPassword.encode())


def _encrypt_blob(vaultKey: bytes, plaintext: str) -> str:
    """AES-256-GCM 加密字符串，返回 ivB64:ctB64"""
    iv = os.urandom(12)
    ct = AESGCM(vaultKey).encrypt(iv, plaintext.encode(), None)
    return _b64e(iv) + ":" + _b64e(ct)


def _decrypt_blob(vaultKey: bytes, blob: str) -> str:
    """解密 ivB64:ctB64 格式密文，返回明文字符串"""
    ivB64, ctB64 = blob.split(":", 1)
    return AESGCM(vaultKey).decrypt(_b64d(ivB64), _b64d(ctB64), None).decode()


def encrypt_entry(vaultKey: bytes, entryDict: dict) -> str:
    """将 entry dict 序列化并加密，返回 blob 字符串（ivB64:ctB64）"""
    return _encrypt_blob(vaultKey, json.dumps(entryDict, ensure_ascii=False))


def decrypt_entry(vaultKey: bytes, blob: str) -> dict:
    """解密 blob，返回 entry dict"""
    return json.loads(_decrypt_blob(vaultKey, blob))


def _load_raw(filePath: str) -> dict:
    with open(filePath, "r", encoding="utf-8") as f:
        return json.load(f)


def _save_raw(filePath: str, vault: dict):
    dirPath = os.path.dirname(os.path.abspath(filePath))
    os.makedirs(dirPath, exist_ok=True)
    with open(filePath, "w", encoding="utf-8") as f:
        json.dump(vault, f, ensure_ascii=False, indent=2)


def _derive_key_from_vault(vault: dict, masterPassword: str) -> bytes:
    kdf = vault["kdf"]
    return derive_vault_key(masterPassword, kdf["salt"], kdf["iterations"])


def _verify_key(vaultKey: bytes, vault: dict) -> bool:
    try:
        return _decrypt_blob(vaultKey, vault["canary"]) == _CANARY_PLAIN
    except Exception:
        return False


def create_vault(filePath: str, masterPassword: str):
    """创建新密码本文件。若文件已存在则抛出 FileExistsError。"""
    if os.path.exists(filePath):
        raise FileExistsError(f"密码本已存在: {filePath}")
    saltB64 = _b64e(os.urandom(16))
    vaultKey = derive_vault_key(masterPassword, saltB64)
    vault = {
        "version": 1,
        "kdf": {"algo": _KDF_ALGO, "iterations": _KDF_ITERATIONS, "salt": saltB64},
        "canary": _encrypt_blob(vaultKey, _CANARY_PLAIN),
        "entries": [],
    }
    _save_raw(filePath, vault)
    log.info("密码本已创建: {path}", path=filePath)


def open_vault(filePath: str, masterPassword: str) -> list:
    """
    打开密码本，验证主密码，返回所有解密后的 entry dict 列表。
    每条 dict 含额外字段 _id / _created_at / _updated_at。
    主密码错误时抛出 ValueError。
    """
    vault = _load_raw(filePath)
    vaultKey = _derive_key_from_vault(vault, masterPassword)
    if not _verify_key(vaultKey, vault):
        raise ValueError("主密码错误或密码本已损坏")
    result = []
    for e in vault["entries"]:
        try:
            data = decrypt_entry(vaultKey, e["data"])
            data["_id"] = e["id"]
            data["_created_at"] = e["created_at"]
            data["_updated_at"] = e["updated_at"]
            result.append(data)
        except Exception as ex:
            log.warning("条目 {id} 解密失败，已跳过: {e}", id=e["id"], e=ex)
    return result


def append_entry(filePath: str, masterPassword: str, entryDict: dict) -> str:
    """追加一条新记录，返回新记录的 id（UUID 字符串）"""
    vault = _load_raw(filePath)
    vaultKey = _derive_key_from_vault(vault, masterPassword)
    if not _verify_key(vaultKey, vault):
        raise ValueError("主密码错误或密码本已损坏")
    entryId = str(uuid.uuid4())
    now = _now_iso()
    vault["entries"].append({
        "id": entryId,
        "created_at": now,
        "updated_at": now,
        "data": encrypt_entry(vaultKey, entryDict),
    })
    _save_raw(filePath, vault)
    log.info("密码本追加条目 {id}", id=entryId)
    return entryId


def update_entry(filePath: str, masterPassword: str, entryId: str, entryDict: dict) -> bool:
    """更新指定 id 的条目，返回是否找到并更新"""
    vault = _load_raw(filePath)
    vaultKey = _derive_key_from_vault(vault, masterPassword)
    if not _verify_key(vaultKey, vault):
        raise ValueError("主密码错误或密码本已损坏")
    for e in vault["entries"]:
        if e["id"] == entryId:
            e["updated_at"] = _now_iso()
            e["data"] = encrypt_entry(vaultKey, entryDict)
            _save_raw(filePath, vault)
            log.info("密码本更新条目 {id}", id=entryId)
            return True
    return False


def delete_entry(filePath: str, masterPassword: str, entryId: str) -> bool:
    """删除指定 id 的条目，返回是否找到并删除"""
    vault = _load_raw(filePath)
    vaultKey = _derive_key_from_vault(vault, masterPassword)
    if not _verify_key(vaultKey, vault):
        raise ValueError("主密码错误或密码本已损坏")
    before = len(vault["entries"])
    vault["entries"] = [e for e in vault["entries"] if e["id"] != entryId]
    if len(vault["entries"]) == before:
        return False
    _save_raw(filePath, vault)
    log.info("密码本删除条目 {id}", id=entryId)
    return True


def export_vault(
    srcPath: str,
    srcMaster: str,
    destPath: str,
    destMaster: str,
    entryIds: list | None = None,
):
    """
    换密码导出：用 srcMaster 解密 srcPath，用 destMaster 重加密，保存到 destPath。
    entryIds 为 None 时导出全部；否则仅导出指定 id 的条目。
    """
    vault = _load_raw(srcPath)
    srcKey = _derive_key_from_vault(vault, srcMaster)
    if not _verify_key(srcKey, vault):
        raise ValueError("源密码本主密码错误或已损坏")

    newSaltB64 = _b64e(os.urandom(16))
    destKey = derive_vault_key(destMaster, newSaltB64, vault["kdf"]["iterations"])

    idSet = set(entryIds) if entryIds is not None else None
    newEntries = []
    for e in vault["entries"]:
        if idSet is not None and e["id"] not in idSet:
            continue
        try:
            data = decrypt_entry(srcKey, e["data"])
            newEntries.append({
                "id": e["id"],
                "created_at": e["created_at"],
                "updated_at": e["updated_at"],
                "data": encrypt_entry(destKey, data),
            })
        except Exception as ex:
            log.warning("导出时条目 {id} 解密失败，已跳过: {e}", id=e["id"], e=ex)

    destVault = {
        "version": 1,
        "kdf": {"algo": _KDF_ALGO, "iterations": vault["kdf"]["iterations"], "salt": newSaltB64},
        "canary": _encrypt_blob(destKey, _CANARY_PLAIN),
        "entries": newEntries,
    }
    _save_raw(destPath, destVault)
    log.info("密码本导出完成: {src} → {dest}，共 {n} 条", src=srcPath, dest=destPath, n=len(newEntries))
