import requests
import json
from . import consts as c, utils

class Client(object):

    def __init__(self, api_key, api_secret_key, passphrase, proxies = "", test=True):
        self.API_KEY = api_key
        self.API_SECRET_KEY = api_secret_key
        self.PASSPHRASE = passphrase

        self.proxies = proxies

        # test用来表明是否为模拟盘，这里就是模拟盘所以默认为True
        self.test = test

    def _request(self, method, request_path, params):
        is_head = False
        if request_path == c.MARKET_HIST_KLINE:
            is_head = True
        if method == c.GET:
            # 得到OK-ACCESS-SIGN中的requestPath, 这个requestPath包含具体的参数信息
            # 具体的参数信息就是用parse_params_to_str变成url的形式
            request_path = request_path + utils.parse_params_to_str(params)
        # 就是root加上具体再加上参数，得到目标url
        url = c.API_URL + request_path

        # 获取请求头中的OK-ACCESS-TIMESTAMP
        timestamp = utils.get_timestamp()

        # 获取请求头OK-ACCESS-SIGN中需要的body,再用method,request_path和body组成OK-ACCESS-SIGN
        body = json.dumps(params) if method == c.POST else ""
        sign = utils.sign(utils.pre_hash(timestamp, method, request_path, str(body)), self.API_SECRET_KEY)

        # 构造请求头
        header = utils.get_header(self.API_KEY, sign, timestamp, self.PASSPHRASE)

        # 如果是模拟盘，那么在header中加上x-simulated-trading:1
        if self.test:
            header['x-simulated-trading'] = '1'

        if is_head:
            header = None

        # 发送request，得到response
        response = None
        if method == c.GET:
            print(url)
            print(header)
            response = requests.get(url, headers=header, proxies=self.proxies, verify=False)
            # response = requests.get(url)
        elif method == c.POST:
            response = requests.post(url, data=body, headers=header, proxies=self.proxies, verify=False)
        elif method == c.DELETE:
            response = requests.delete(url, headers=header, proxies=self.proxies, verify=False)

        return response.json()


    # 如果请求不需要参数，则只需要基本的获取方法以及目标url
    def _request_without_params(self, method, request_path):
        return self._request(method, request_path, {})


    def _request_with_params(self, method, request_path, params):
        return self._request(method, request_path, params)


    # 专门用来获取系统时间戳的函数，和两个_request函数可以说是并列的
    def _get_timestamp(self):
        url = c.API_URL + c.SERVER_TIMESTAMP_URL
        response = requests.get(url)
        if response.status_code == 200:
           return response.json()['iso']
        else:
           return ""