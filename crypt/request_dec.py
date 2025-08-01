import json
import time

from lebase.crypt.lehash import dic2dec, get_sha
from lebase.ensures import ensure_num

# ----------------------------
# django request 转 ip 和时间戳验密
# ----------------------------


class RequestValidator:
    """请求验证器，用于防止时间戳重放攻击"""

    def __init__(self):
        self.last_pass_time = 0  # 假设低并发，则真正的用户每次验密时间必不同，防密钥重放攻击

    def get_last_pass_time(self):
        return self.last_pass_time

    def set_last_pass_time(self, time_value):
        self.last_pass_time = time_value


# 创建全局实例
request_validator = RequestValidator()


def _extract_request_data(request):
    """提取请求数据并设置编码"""
    request.encoding = "utf-8"
    req = json.loads(request.body)

    # 保存 ip 和 meta 信息
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")  # 判断是否使用代理
    if x_forwarded_for:
        req["ip"] = x_forwarded_for.split(",")[0]  # 使用代理获取真实的ip
        req["ip-agent"] = x_forwarded_for
    else:
        req["ip"] = request.META.get("REMOTE_ADDR")  # 未使用代理获取IP

    req["ua"] = request.META["HTTP_USER_AGENT"]
    return req


def _validate_timestamp(req):
    """验证时间戳"""
    rtime = req.get("r", 0)
    t = ensure_num(rtime)

    if t == 0:
        return "❌ time 0", t
    elif t < time.time() - 60:
        return "❌ time too old", t
    elif t > time.time() + 60:
        return "❌ time too future", t
    elif request_validator.get_last_pass_time() + 0.01 >= t:  # 重复使用时间戳
        return "❌ time reuse", t
    else:
        return "🟢 time pass", t


def _validate_username(req, colUser, rtime):
    """验证用户名"""
    p = ""
    passSHA = req.get("p", "")
    px = None

    for x in colUser.find({}):
        kou = "-".join(list(x["_id"] + str(rtime)))
        kouSHA = get_sha(kou)
        if passSHA == kouSHA:
            p = x["_id"]
            px = x
            break

    if not p:
        return "❌ 用户名不认识", p, px
    else:
        req["p"] = p
        return "🟢 name pass", p, px


def _validate_ip(req, px):
    """验证IP地址"""
    liIp = px.get("ip", [])
    isAllowIp = False

    if liIp == "*":
        isAllowIp = True
    elif req["ip"]:  # ip信息为空则不通过
        for goodIP in liIp:
            if "*" in goodIP:
                if req["ip"].startswith(goodIP.replace("*", "")):
                    isAllowIp = True
            elif req["ip"] == goodIP:
                isAllowIp = True

    if not isAllowIp:
        return "❌ ip不认识"
    else:
        return "🟢 ip pass"


def _decrypt_content(req, rtime):
    """解密内容"""
    if req.get("c", ""):
        req["c"] = dic2dec({"r": rtime, "c": req.get("c", "")}, req["p"])


def request2dec(request, colUser, colReq):
    """
    request：可读取前端传来的字典
        p：passSHA：客户传来的 口令+时间戳+加花- 的 sha256
        r：rtime：客户传来的毫秒时间戳
        c：待解密的内容
        ip：前端请求的 ip
    colUser：所有认可的用户名和权限信息存储在哪
    返回：字典
        m：总是字符串，错误统一以❌开头加要显示给客户的信息
            time xxx：时间戳错误信息
            x：用户名错误
            ip 不认识：ip 错误信息
            6：成功，通过
    上传：传入的req加返回的m都上传到 colReq
        p：匹配的用户名（没匹配则存SHA）
        c：解密的内容
        r：重复一遍 rtime（方便直接存入库）
        ip：重复一遍 ip（方便直接存入库）
    colReq：每次请求的数据入库
        缺点：如果用户输入错误密码（库里不认识的密码）那后端也不知道他输的是啥…
    """
    # 提取请求数据
    req = _extract_request_data(request)

    # 验证时间戳
    time_msg, t = _validate_timestamp(req)

    # 如果没有时间戳，则用户名和内容的解码都无法进行！
    if time_msg.startswith("❌ time 0"):
        req["m"] = time_msg
        colReq.insert_one(req)
        # print('request2dec:', x, req)
        return {"m": time_msg}

    # 验证用户名
    name_msg, p, px = _validate_username(req, colUser, req.get("r", 0))
    m = name_msg + " " + time_msg

    # 只要认识用户名就应该将消息解密存储
    if "name pass" in name_msg:
        # 解密内容
        _decrypt_content(req, req.get("r", 0))

        # 验证IP
        ip_msg = _validate_ip(req, px)
        m = ip_msg + " " + m

    # 在通过以上所有校验后
    req["m"] = m
    req["_id"] = time.time()
    colReq.insert_one(req)

    if "❌" in req["m"]:
        # print('request2dec ❌:', x, req)
        return {"m": m}
    else:
        request_validator.set_last_pass_time(t)
        print("LAST_PASS_TIME:", request_validator.get_last_pass_time())
        # print('request2dec PASSED:', x, req)
        return req
