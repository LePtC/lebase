import json
import time
from lebase.safes import ensure_num
from lebase.crypt.lehash import get_sha, dic2dec


# ----------------------------
# django request 转 ip 和时间戳验密
# ----------------------------

LAST_PASS_TIME = 0  # 假设低并发，则真正的用户每次验密时间必不同，防密钥重放攻击


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
    global LAST_PASS_TIME

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

    # ----------------------------
    # 先看时间戳
    # ----------------------------
    rtime = req.get("r", 0)

    t = ensure_num(rtime)
    if t == 0:
        m = "❌ time 0"
    elif t < time.time() - 60:
        m = "❌ time too old"
    elif t > time.time() + 60:
        m = "❌ time too future"
    elif LAST_PASS_TIME + 0.01 >= t:  # 重复使用时间戳
        m = "❌ time reuse"
    else:
        m = "🟢 time pass"

    # 如果没有时间戳，则用户名和内容的解码都无法进行！
    if m.startswith("❌ time 0"):
        req["m"] = m
        x = colReq.insert_one(req)
        # print('request2dec:', x, req)
        return {"m": m}

    # ----------------------------
    # 用户名校验
    # ----------------------------
    p = ""
    passSHA = req.get("p", "")
    for x in colUser.find({}):
        kou = "-".join(list(x["_id"] + str(rtime)))
        kouSHA = get_sha(kou)
        if passSHA == kouSHA:
            p = x["_id"]
            px = x
            break

    if not p:
        m = "❌ 用户名不认识 " + m
    else:
        m = "🟢 name pass " + m
        req["p"] = p

    # ----------------------------
    # 只要认识用户名就应该将消息解密存储
    # ----------------------------
    if "name pass" in m:

        if req.get("c", ""):
            req["c"] = dic2dec({"r": rtime, "c": req.get("c", "")}, req["p"])

        # ----------------------------
        # ip 校验
        # ----------------------------
        liIp = px.get("ip", [])
        isAllowIp = False
        if liIp == "*":
            isAllowIp = True
        if req["ip"]:  # ip信息为空则不通过
            for goodIP in liIp:
                if "*" in goodIP:
                    if req["ip"].startswith(goodIP.replace("*", "")):
                        isAllowIp = True
                else:
                    if req["ip"] == goodIP:
                        isAllowIp = True

        if not isAllowIp:
            m = "❌ ip不认识 " + m
        else:
            m = "🟢 ip pass " + m

    # ----------------------------
    # 在通过以上所有校验后
    # ----------------------------
    req["m"] = m
    req["_id"] = time.time()
    x = colReq.insert_one(req)
    if "❌" in req["m"]:
        # print('request2dec ❌:', x, req)
        return {"m": m}
    else:
        LAST_PASS_TIME = t
        print("LAST_PASS_TIME:", LAST_PASS_TIME)
        # print('request2dec PASSED:', x, req)
        return req
