# -*- coding: utf-8 -*-
# Peter hash

import hmac

# from datetime import datetime
from datetime import datetime, timedelta, timezone

KEY = 20210114  # 常量，项目启动的日期，整数
C = 299792458  # 常量，真空光速，整数


def get_pehash():
    # date = int(datetime.today().strftime('%Y%m%d')) # 变量，当前日期，八位 yyyyMMdd 格式，整数
    date = int(datetime.today().astimezone(timezone(timedelta(hours=+8))).strftime("%Y%m%d"))
    h = hmac.new(
        KEY.to_bytes(4, byteorder="big"), date.to_bytes(4, byteorder="big"), digestmod="SHA256"
    )  # HMAC 运算对象
    token = format(
        int(h.hexdigest(), 16) % C, "08X"
    )  # 结果识别为 16 进制整数，对光速求余，然后转换为八位大写 16 进制字符串，此为所需结果

    return token


if __name__ == "__main__":

    print(datetime.today())
    print(get_pehash())

    pass
