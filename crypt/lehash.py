# -*- coding: utf-8 -*-
"""
由于MD5模块在python3中被移除， 在python3中使用hashlib模块进行md5操作

250203 js2py 报错不适配 py3.12 待MR
https://github.com/PiotrDabkowski/Js2Py/pull/327/files
"""

import base64
import hashlib
import json
import time

import js2py  # 与 javascript 编码解码互通
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

en = js2py.eval_js("function en(c) {return encodeURIComponent(c)}")
de = js2py.eval_js("function de(b) {return decodeURIComponent(b)}")

BLOCK_SIZE = 16


def pad(s):
    return s + (BLOCK_SIZE - len(s) % BLOCK_SIZE) * chr(BLOCK_SIZE - len(s) % BLOCK_SIZE)


def unpad(s):
    return s[: -ord(s[len(s) - 1 :])]


# https://stackoverflow.com/questions/43199123/encrypting-with-aes-256-and-pkcs7-padding
# def pkcs5padding(data):
#     return pkcs7padding(data, 8)


# 生成MD5
def get_md5(txt):
    # 创建md5对象
    hl = hashlib.md5()  # noqa: S324

    # Tips
    # 此处必须声明encode
    # 否则报错为：hl.update(txt)    Unicode-objects must be encoded before hashing
    hl.update(txt.encode(encoding="utf-8"))

    print("MD5加密前为 ：" + txt)
    print("MD5加密后为 ：" + hl.hexdigest())


def get_sha(txt):
    return hashlib.sha256(txt.encode("utf-8")).hexdigest()


# 配合前端 AES 加密解密
KOU_LIN = "赞赞赞"


def get_rule_key(kou, t):
    s = get_sha("=".join(list(kou + str(t)))) + "23679BDEFkLMoprsXz1458ACGhJNQTyUVWdaf0gblentcuxSimj"
    return s[:32]


# https://stackoverflow.com/questions/25261647/python-aes-encryption-without-extra-module
def encrypt(raw, key):
    # cipher = Cipher(algorithms.AES(key.encode("utf-8")), modes.ECB())
    cipher = Cipher(algorithms.AES(key.encode("utf-8")), modes.CBC((key[:16]).encode("utf-8")))

    txt = base64.b64encode(en(raw).encode("utf-8")).decode("utf-8")
    # print('txt:',txt)
    encryptor = cipher.encryptor()
    ct = encryptor.update(pad(txt).encode("utf-8")) + encryptor.finalize()

    return base64.b64encode(ct)


def decrypt(ct, key):
    cipher = Cipher(algorithms.AES(key.encode("utf-8")), modes.CBC((key[:16]).encode("utf-8")))

    decryptor = cipher.decryptor()
    dt = decryptor.update(base64.b64decode(ct)) + decryptor.finalize()

    return de(base64.b64decode(unpad(dt)).decode("utf-8"))


# 最终封装，与 js 同款的一键把 dict 按狸子 DIY 协议加密打包
def dic2enc(dic, kouling):
    t = time.time()
    s = get_rule_key(kouling, t)
    return {"r": t, "c": encrypt(json.dumps(dic), s).decode("utf-8")}  # 后端无需把 p 给前端验密


def dic2dec(dic, kouling):
    t = dic["r"]
    s = get_rule_key(kouling, t)
    return json.loads(decrypt(dic["c"], s))


if __name__ == "__main__":

    # get_md5('1234567890ABCDEF1568134370')
    # print(en("fans2021123111-ALJ20211231223006.csv+pack3-fans2021123111-TK20211231110902.csv"))
    # print(de(en("fans2021123111-ALJ20211231223006.csv+pack3-fans2021123111-TK20211231110902.csv")))
    # print(en("💐🌸💮🏵️🌹🥀🌺🌻🌼🌷🌱🌲🌳🌴🌵🌾🌿☘️🍀🍁🍂🍃"))
    # print(de(en("💐🌸💮🏵️🌹🥀🌺🌻🌼🌷🌱🌲🌳🌴🌵🌾🌿☘️🍀🍁🍂🍃")))

    # kl = get_rule_key(KOU_LIN, '1642520275.003')
    # print(kl)
    # print((kl[:16]).encode("utf-8"))
    # ct = encrypt("a secret message 啊啊", "26f3ee35dffad70acfa78706c1fe3a89")
    # # ct = encrypt("fans2021123111-ALJ20211231223006.csv+pack3-fans2021123111-TK20211231110902.csv",kl)
    # print(ct)
    # print(decrypt(ct,kl))

    # string iv:'26f3ee35dffad70a', key:"26f3ee35dffad70acfa78706c1fe3a89"，test:'2'发现是按hex打印的
    # js iv:32366633656533356466666164373061，key: 3236663365653335646666616437306163666137383730366331666533613839，test:32

    # li = list(bytes('26f3ee35dffad70a', 'ascii'))
    # print(li)
    # x = 0
    # for i in range(len(li)):
    #     x += x*128 + li[i]
    # print(x)

    kl = get_rule_key("xxx", "1663313945.4672966")
    ct = "OLcE7AMhZL8p2dnKXDhJsZqyuLp9gDljrfiTojJtSfwXpW8q+5DCxwXW3ZhibJeyhENy1xNi0xbAzf6TeczrQFQfBKMh4HD8XMGG1ysjS0+2WlD3lCXIH5q9EpUKQsqXvCI/AOyjnr9Z/eLLCrVnGrm8/a7aByh+4yvDv7W82xGDW/+I6cq6M20y9PYNdKLU2NOKMf7KJek+m8NFpfNK+g=="
    print(decrypt(ct, kl))
