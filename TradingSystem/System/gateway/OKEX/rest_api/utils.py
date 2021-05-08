# 整个utils就是构造http的请求头的工具类
# 请求头示例：
# Content-Type: application/json
# OK-ACCESS-KEY: 37c541a1-*--***-10fe7a038418
# OK-ACCESS-SIGN: leaVRETrtaoEQ3yI9qEtI1CZ82ikZ4xSG5Kj8gnl3uw=
# OK-ACCESS-PASSPHRASE: 1****6
# OK-ACCESS-TIMESTAMP: 2020-03-28T12:21:41.274Z
# x-simulated-trading: 1

import hmac
import base64
import datetime
import time
from . import consts as c


# 得到需要形式的 OK-ACCESS-SIGN
def get_timestamp():
    # utc是世界时间
    now = datetime.datetime.utcnow()
    # 要求的时间只需要保留小数点后三位
    t = now.isoformat("T", "milliseconds")
    return t + "Z"


# OK-ACCESS-SIGN使用HMAC SHA256哈希函数获得哈希值，再使用Base-64编码
def sign(message, secret_key):
    # 第一个参数是密钥，第二个参数是待加密的字符串，这两个参数都要是二进制形式，第三个参数是加密算法
    mac = hmac.new(bytes(secret_key, encoding='utf8'), bytes(message, encoding='utf-8'), digestmod='sha256')
    # digest返回mac的ascii格式
    d = mac.digest()
    # Base64就是一种基于64个可打印字符（包括a - z、A - Z、0 - 9、 / 、+）来表示二进制数据的方法
    return base64.b64encode(d)


# 由于OK-ACCESS-SIGN的请求头是对timestamp + method + requestPath + body字符串（+表示字符串连接）进行处理的，所以prehash就是
# 将其链接并变成字符串
def pre_hash(timestamp, method, request_path, body):
    return str(timestamp) + str.upper(method) + request_path + body


# 所有header中需要的东西都得到之后，把这些东西放入http的请求头之中
def get_header(api_key, sign, timestamp, passphrase):
    header = dict()
    header[c.CONTENT_TYPE] = c.APPLICATION_JSON
    header[c.OK_ACCESS_KEY] = api_key
    header[c.OK_ACCESS_SIGN] = sign
    header[c.OK_ACCESS_TIMESTAMP] = str(timestamp)
    header[c.OK_ACCESS_PASSPHRASE] = passphrase

    return header


# 把输入的参数变成url的形式，以得到requestPath
def parse_params_to_str(params):
    result = "?"
    for key, value in params.items():
        result += (str(key) + "=" +str(value) + "&")

    # 不要最后一个&
    return result[0:-1]

# 把时间字符串变成Unix timestamp 即多少毫秒
def str2UnixTimestamp(date_str):
    return int(time.mktime((datetime.datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%S.%fZ")).timetuple()) * 1000)