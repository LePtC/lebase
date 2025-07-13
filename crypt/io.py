
import base64
import os

# 使用 cryptography 库进行加解密
from cryptography.fernet import Fernet
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from lelog.logs import log  # 假定已提供 log.info 与 log.warn 函数
from levar.var import lev

########################################
# 1. 配置文件格式与密码加解密工具函数
########################################


def derive_key(masterPassword, salt):
    """
    根据主密码和 salt 派生密钥，返回 32 字节的 Fernet 密钥
    """
    kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=100000, backend=default_backend())
    key = base64.urlsafe_b64encode(kdf.derive(masterPassword.encode()))
    return key


def encrypt_password(masterPassword, plainPassword):
    """
    加密密码工具函数
    参数：
        masterPassword: 主密码，用于派生加密密钥
        plainPassword: 明文密码
    返回值：加密后的密码字符串，同时打印加密结果
    格式为：base64(salt) + ":" + 密文
    """
    salt = os.urandom(16)  # 生成随机 salt
    key = derive_key(masterPassword, salt)
    fernet = Fernet(key)
    encrypted = fernet.encrypt(plainPassword.encode())
    encryptedStr = base64.urlsafe_b64encode(salt).decode() + ":" + encrypted.decode()
    log.info("加密后的密码: " + encryptedStr)
    return encryptedStr


def decrypt_password(masterPassword, encryptedStr):
    """
    解密密码工具函数
    参数：
        masterPassword: 主密码
        encryptedStr: 加密后的密码字符串
    返回值：解密后的明文密码；若解密失败则返回 None，并打印 warn 信息
    """
    try:
        saltB64, encryptedData = encryptedStr.split(":")
        salt = base64.urlsafe_b64decode(saltB64)
        key = derive_key(masterPassword, salt)
        fernet = Fernet(key)
        decrypted = fernet.decrypt(encryptedData.encode())
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
