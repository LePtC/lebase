import base64
import os

# 使用 cryptography 库进行加解密（PBKDF2-SHA256 + AES-256-GCM）
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from lelog.logs import log  # 假定已提供 log.info 与 log.warn 函数
from levar.var import lev

########################################
# 1. 配置文件格式与密码加解密工具函数
########################################

_PBKDF2_ITERATIONS = 600000


def derive_key(masterPassword, salt):
    """
    根据主密码和 salt 派生 32 字节密钥（PBKDF2-HMAC-SHA256，600k 次迭代）
    """
    kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=_PBKDF2_ITERATIONS)
    return kdf.derive(masterPassword.encode())


def encrypt_password(masterPassword, plainPassword):
    """
    加密密码工具函数（AES-256-GCM）
    参数：
        masterPassword: 主密码，用于派生加密密钥
        plainPassword: 明文密码
    返回值：加密后的密码字符串
    格式为：base64(salt) + ":" + base64(iv) + ":" + base64(ciphertext+tag)
    """
    salt = os.urandom(16)
    iv = os.urandom(12)  # GCM 推荐 96-bit IV
    key = derive_key(masterPassword, salt)
    aesgcm = AESGCM(key)
    ciphertext = aesgcm.encrypt(iv, plainPassword.encode(), None)  # 含 16 字节 auth tag
    encryptedStr = (
        base64.urlsafe_b64encode(salt).decode()
        + ":"
        + base64.urlsafe_b64encode(iv).decode()
        + ":"
        + base64.urlsafe_b64encode(ciphertext).decode()
    )
    log.info("加密后的密码: " + encryptedStr)
    return encryptedStr


def decrypt_password(masterPassword, encryptedStr):
    """
    解密密码工具函数（AES-256-GCM）
    参数：
        masterPassword: 主密码
        encryptedStr: 加密后的密码字符串（salt:iv:ciphertext 三段 base64）
    返回值：解密后的明文密码；若解密失败则返回 None，并打印 warn 信息
    """
    try:
        saltB64, ivB64, ciphertextB64 = encryptedStr.split(":")
        salt = base64.urlsafe_b64decode(saltB64)
        iv = base64.urlsafe_b64decode(ivB64)
        ciphertext = base64.urlsafe_b64decode(ciphertextB64)
        key = derive_key(masterPassword, salt)
        aesgcm = AESGCM(key)
        decrypted = aesgcm.decrypt(iv, ciphertext, None)
        return decrypted.decode()
    except Exception as e:
        log.warning("解密密码失败: " + str(e))
        return None


# 配置文件存放建议：
# 在 Windows Server 上，可以将配置文件存放于 C:\ProgramData\YourAppName\mongo_config.json，
# 并设置严格的文件权限，只允许特定的应用程序和管理员访问，从而确保连接信息安全。


if __name__ == "__main__":

    # 示例1：使用主密码加密明文密码
    masterPwd = lev.pwd  # 主密码（实际使用时请妥善保存与管理）
    plainPwd = input("请输入要加密的原文：")
    encryptedPwd = encrypt_password(masterPwd, plainPwd)
    print("加密后的密码为:", encryptedPwd)
    input("按任意键继续...")
