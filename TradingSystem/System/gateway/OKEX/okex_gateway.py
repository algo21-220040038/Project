import websocket
import socket
import json
from datetime import datetime
from threading import Thread, Lock
import base64
import hmac
from pytz import utc as UTC_TZ
from typing import Any, Sequence, Dict, List, Optional, Callable
from System.event.engine import Event, EventEngine
from System.trader.object import TickData, BookData, \
    OrderData, TradeData, AccountData, \
    SubscribeRequest, OrderRequest, CancelRequest
from System.trader.constant import *
from System.trader.event import *
from .rest_api.trade_api import TradeAPI
from .rest_api.account_api import AccountAPI
from System.trader.constant import Exchange
import sys
import traceback
from time import sleep
import time
from copy import copy

WEBSOCKET_PUBLIC_HOST = 'wss://wspap.okex.com:8443/ws/v5/public?brokerId=9999'
WEBSOCKET_PRIVATE_HOST = 'wss://wspap.okex.com:8443/ws/v5/private?brokerId=9999'

# 产品与币种，这个可以用在订阅那里
# 可以用这两个来设置订阅哪些频道
instruments = set()
currencies = set()

# Okex对应一个网关，一个网关可以有多个接口，比如restful接口和websocket接口
class OkexGateway():

    default_setting = {
        "api_key": "7131f5ad-69e3-40d8-819e-a46ab51406fe",
        "secret_key": "C2BDF9B49FDA480590A5446A422254AF",
        "passphrase": "211411qwe",
        "代理地址": "127.0.0.1",
        "代理端口": 1080,
    }

    exchanges = [Exchange.OKEX]

    def __init__(self, event_engine, gateway_name):
        self.event_engine = event_engine
        self.gateway_name = gateway_name

        self.ws_public_api = OkexWebsocketApi(self, channel_type="public")
        self.ws_private_api = OkexWebsocketApi(self, channel_type="private")
        self.rest_api = OkexRestApi(self)

        self.orders = {}

    def connect(self, setting = default_setting):
        api_key = setting["api_key"]
        secret_key = setting["secret_key"]
        passphrase = setting["passphrase"]
        proxy_host = setting["代理地址"]
        proxy_port = setting["代理端口"]

        self.ws_public_api.connect(api_key, secret_key, passphrase, proxy_host, proxy_port)
        self.ws_private_api.connect(api_key, secret_key, passphrase, proxy_host, proxy_port)
        self.rest_api.connect(api_key, secret_key, passphrase, proxy_host, proxy_port)

    def subscribe(self, type, req: SubscribeRequest):
        channel = req.channel
        instId = req.instId
        instType = req.instType
        ccy = req.ccy
        uly = req.uly

        if type == "public":
            self.ws_public_api.subscribe(channel=channel, instId=instId, instType=instType, ccy=ccy, uly=uly)
        elif type == "private":
            self.ws_private_api.subscribe(channel=channel, instId=instId, instType=instType, ccy=ccy, uly=uly)

    def send_order(self, req: OrderRequest):
        self.rest_api.send_order(req)

    def cancel_order(self, req: CancelRequest):
        self.rest_api.cancel_order(req)

    def send_orders(self, reqs: Sequence[OrderRequest]) -> List[str]:
        sys_orderids = []

        for req in reqs:
            sys_orderid = self.send_order(req)
            sys_orderids.append(sys_orderid)

        return sys_orderids

    def cancel_orders(self, reqs: Sequence[CancelRequest]) -> None:
        for req in reqs:
            self.cancel_order(req)

    # 从本地的orders字典中提取目标order，这里orderid用的是自己设置的id
    def get_order(self, orderid: str):
        return self.orders.get(orderid, None)

    def query_account_balance(self, ccy):
        self.rest_api.query_account_balance(ccy)

    def query_account_pos_risk(self, instType=""):
        return self.rest_api.query_accont_pos_risk()

    def close(self):
        self.ws_public_api.stop()
        self.ws_private_api.stop()

    def on_event(self, type, data):
        event = Event(type, data)
        self.event_engine.put(event)
        print("把"+type+"事件放入事件驱动引擎")

    def on_tick(self, tick: TickData):
        self.on_event(EVENT_TICK, tick)

    def on_depth(self, book: BookData):
        self.on_event(EVENT_BOOK, book)

    def on_trade(self, trade:TradeData):
        self.on_event(EVENT_TRADE, trade)

    def on_order(self, order: OrderData):
        # 这里用本地自己设的订单号作为key
        self.orders[order.client_orderid] = order
        self.on_event(EVENT_ORDER, order)

    def on_account(self, account:AccountData):
        self.on_event(EVENT_ACCOUNT, account)

    def get_default_setting(self):
        return self.default_setting

class OkexWebsocketApi():
    def __init__(self, gateway, channel_type):
        self.gateway = gateway
        self.gateway_name = gateway.gateway_name

        self.channel_type = channel_type

        # 用来锁定线程的
        self._ws_lock = Lock()
        # 用来放创建好的连接
        self._ws = None

        # 主进程，从建立好的websocket不断接收消息
        self._worker_thread = None
        # 保持连接的进程
        self._ping_thread = None
        # 相当于从外部控制的开关
        self._active = False

        self.api_key = ""
        self.secret_key = ""
        self.passphrase = ""

        self.proxy_host = None
        self.proxy_port = None
        self.ping_interval = None

        # 用来标记成交了的订单
        self.trade_count = 0

        self.callbacks = {}

    # OKEx文档上说30s无消息则断开，所以ping_interval为20
    def init(self, url, proxy_host, proxy_port, ping_interval=20):
        self.url = url

        # 代理设置
        if proxy_host and proxy_port:
            self.proxy_host = proxy_host
            self.proxy_port = proxy_port

        self.ping_interval = ping_interval

        # 身份信息设置
        # self.api_key = "7131f5ad-69e3-40d8-819e-a46ab51406fe"
        # self.secret_key = "C2BDF9B49FDA480590A5446A422254AF"
        # self.passphrase = "211411qwe"

        # 用来存放在接受OKEX返回的数据以后，使用的回调函数
        self.callbacks = {}
        # 存放已订阅的产品品种
        self.subscribed = []

    # 控制启动的函数
    def connect(self, api_key, secret_key, passphrase, proxy_host, proxy_port):
        self.api_key = api_key
        self.secret_key = secret_key
        self.passphrase = passphrase

        if self.channel_type == "public":
            url = WEBSOCKET_PUBLIC_HOST
        elif self.channel_type == "private":
            url = WEBSOCKET_PRIVATE_HOST
        self.init(url = url, proxy_host = proxy_host, proxy_port = proxy_port)

        self.start()

    def on_connected(self):
        print("Websocket 连接成功")
        if self.channel_type == "public":
            # 默认订阅行情和五档深度频道，别的可以通过subscribe加
            self.subscribe(channel="tickers", instId="BTC-USDT")
            # self.subscribe(channel="books5", instId="BTC-USDT")
            # self.subscribe(channel="candle1m")
        elif self.channel_type == "private":
            self.login()

    def _ensure_connection(self):
        # 这个东西可以防止已经连接上以后的再次连接，至于中间连接出了问题，会报出异常
        is_connected = False
        # 用with实现，锁定线程，并在结束后释放
        with self._ws_lock:
            if self._ws is None:
                # 这里也可能连接不上，但是在外层异常处理中处理了连接不上的情况
                self._ws = websocket.create_connection(self.url, http_proxy_host=self.proxy_host, http_proxy_port=self.proxy_port)
                is_connected=True
        if is_connected:
            self.on_connected()

    def on_disconnected(self):
        print("Websocket 连接断开")

    def _disconnect(self):
        is_disconnected = False
        with self._ws_lock:
            ws = self._ws
            self._ws = None
            is_disconnected = True
        if is_disconnected:
            ws.close()
            self.on_disconnected()

    def on_login(self, data):
        if data["code"] == '0':
            print("Websocket 登录成功")
            # 默认订阅BTC和USDT的账户频道，后面可以加
            self.subscribe(channel="account", ccy="BTC")
            self.subscribe(channel="account", ccy="USDT")
            # 订阅委托频道
            self.subscribe(channel="orders", instType="SPOT")

        else:
            print("Websocket 登录失败")

    # 这里是接收到信息以后如何处理，v5和v3不一样
    def on_recv(self, response):
        if "event" in response:
            # json转换为字典
            response = json.loads(response)
            event = response["event"]
            if event == "subscribe":
                print("订阅成功")
                return
            elif event == "error":
                msg = response["message"]
                print("请求异常")
            elif event == "login":
                self.on_login(response)
        elif "data" in response:
            # json转换为字典
            response = json.loads(response)
            channel = response["arg"]["channel"]
            data = response["data"][0]
            callback = self.callbacks.get(channel, None)

            if callback:
                callback(data)

    # 核心运行函数
    def _run(self):
        try:
            # 如果外部调用stop把_active变成False，整个程序就停了
            while self._active:
                self._ensure_connection()
                try:
                    ws = self._ws
                    if ws:
                        print("等待接收消息")
                        response = ws.recv()
                        print(response)

                        if not response:
                            self._disconnect()
                            continue

                        # try:
                        #     response_json = self.unpack_response(response)
                        # except ValueError as e:
                        #     print("websocket unable to parse data: " + response)
                        #     raise e

                        self.on_recv(response)
                    # 这里同时处理了ensure_connection的异常
                except(
                        websocket.WebSocketConnectionClosedException,
                        websocket.WebSocketBadStatusException,
                        socket.error):
                    self._disconnect()
                # 这里处理on_recv部分的异常
                # 输出错误信息，不做细化处理
                except:
                    et, ev, tb = sys.exc_info()
                    print(et,ev)
                    traceback.print_tb(tb)
                    self._disconnect()

        except:
            et, ev, tb = sys.exc_info()
            print(et, ev)
            traceback.print_tb(tb)
            self._disconnect()

    def _ping(self):
        ws = self._ws
        if ws:
            print("发送ping")
            ws.send("ping", websocket.ABNF.OPCODE_PING)
            # 这里不加ping的callback处理为了效率更高
            # response = ws.recv()
            # try:
            #     response_json = self.unpack_response(response)
            # except ValueError as e:
            #     print("websocket unable to parse data: " + response)
            #     raise e
            # self.on_ping()

    def _run_ping(self):
        while self._active:
            try:
                self._ping()
            except:
                et, ev, tb = sys.exc_info()
                print(et, ev, tb)
                sleep(1)

            # 等带ping_interval秒
            for i in range(self.ping_interval):
                if not self._active:
                    break
                sleep(1)


    # 整个websocket启动的函数
    def start(self):
        self._active = True
        self._worker_thread = Thread(target=self._run)
        self._worker_thread.start()

        self._ping_thread = Thread(target=self._run_ping)
        self._ping_thread.start()

    # 通过控制_active，结束进程中的大循环
    def stop(self):
        self._active = False
        self._disconnect()

    def send_request(self, request:dict):
        request_json = json.dumps(request)
        ws = self._ws
        if ws:
            print("发送消息")
            ws.send(request_json)

    # OKEX的ticker频道只有一档行情，那深度数据就让on_depth专门负责就好
    def on_ticker(self, data):
        tick = TickData(instId=data["instId"], exchange=Exchange.OKEX, datetime=datetime.now(UTC_TZ), gateway_name=self.gateway_name)
        tick.last_price = data["last"]
        tick.last_volume = data["lastSz"]
        tick.open_price = data["open24h"]
        tick.high_price = data["high24h"]
        tick.low_price = data["low24h"]
        tick.volume = data["vol24h"]

        self.gateway.on_tick(copy(tick))

    def on_depth(self, data):
        book = BookData(instId=data["instId"], exchange=Exchange.OKEX, datetime=datetime.now(UTC_TZ), gateway_name=self.gateway_name)
        asks = data["asks"]
        bids = data["bids"]

        for n in range(5):
            price, volume, liquidated_orders_num, orders_num = bids[n]
            book.__setattr__("bid_price_%s" % (n+1), float(price))
            book.__setattr__("bid_volume_%s" % (n + 1), float(volume))

        for n in range(min(5, len(asks))):
            price, volume, liquidated_orders_num, orders_num = asks[n]
            book.__setattr__("ask_price_%s" % (n + 1), float(price))
            book.__setattr__("ask_volume_%s" % (n + 1), float(volume))

        self.gateway.on_depth(copy(book))

    # 这里是只接受单个币种或者产品的account信息，也可以改成一次接受多个
    def on_account(self, data):
        details = data["details"][0]
        account = AccountData(
            currency=details["ccy"],
            cash_balance=details["cashBal"],
            avail_balance=details["availBal"],
            frozen_balance=details["frozenBal"],
            server_time=details["uTime"],
            datetime=datetime.now(UTC_TZ),
            gateway_name = self.gateway_name
        )
        self.gateway.on_account(copy(account))

    # 注意，order里面是累计成交的量
    def on_order(self, data):
        order = OrderData(
            instId = data["instId"],
            exchange = Exchange.OKEX,
            server_orderid = data["ordId"],
            client_orderid=data["clOrdId"],
            direction=data["side"],
            price=data["px"],
            volume=float(data["sz"]),
            traded=float(data["accFillSz"]),
            datetime=datetime.now(UTC_TZ),
            status=data["state"],
            fillPx=data["fillPx"],
            gateway_name=self.gateway_name
        )
        self.gateway.on_order(copy(order))

        # 最新成交数量
        trade_volume = data.get("fillsz")
        # 如果没有成交，不生成trade_volume
        if not trade_volume or float(trade_volume) == 0:
            return

        self.trade_count += 1
        tradeid = f"{self.trade_count}"

        # trade记录每个委托的成交（每个委托可能有多次成交）
        trade = TradeData(
            instId=order.instId,
            exchange=order.exchange,
            server_orderid=order.server_orderid,
            client_orderid=order.client_orderid,
            tradeid=tradeid,
            direction=order.direction,
            price=float(data["fillPx"]),
            volume=float(trade_volume),
            datetime=datetime.now(UTC_TZ),
            gateway_name=self.gateway_name
        )
        self.gateway.on_trade(trade)


    # 这个要放在on_connected那里，订阅频道应该是在连接上以后，所以subscribe应该放在连接上后的回调函数中
    def subscribe(self, channel, instId="", instType="", uly = "", ccy=""):
        # self.subscribed.append(instId)
        args = {}
        args["channel"] = channel
        if instId:
            args["instId"] = instId
        if instType:
            args["instType"] = instType
        if uly:
            args["uly"] = uly
        if ccy:
            args["ccy"] = ccy

        # 订阅了什么频道，就在callbacks字典中加入什么频道的回调函数
        if channel == "tickers":
            self.callbacks[channel] = self.on_ticker
        if "books" in channel :
            self.callbacks[channel] = self.on_depth
        if channel == "account":
            self.callbacks[channel] = self.on_account
        if channel == "orders":
            self.callbacks[channel] = self.on_order
        # if "candle" in channel:
        #     self.callbacks[channel] = self.on_candle

        req  = {
            "op": "subscribe",
            "args":[args]
        }

        self.send_request(req)

    # 先将timestamp 、 method 、requestPath 、 body进行字符串拼接
    def pre_hash(self, timestamp, method, request_path):
        return str(timestamp) + str.upper(method) + request_path

    # 使用HMAC SHA256哈希函数获得哈希值，再使用Base-64编码
    def sign(self, message, secret_key):
        # 第一个参数是密钥，第二个参数是待加密的字符串，这两个参数都要是二进制形式，第三个参数是加密算法
        mac = hmac.new(bytes(secret_key, encoding='utf8'), bytes(message, encoding='utf-8'), digestmod='sha256')
        # digest返回mac的ascii格式
        d = mac.digest()
        # Base64就是一种基于64个可打印字符（包括a - z、A - Z、0 - 9、 / 、+）来表示二进制数据的方法
        return base64.b64encode(d)

    # 登陆
    def login(self):
        timestamp = str(int(time.time()))

        signature = self.sign(self.pre_hash(timestamp, 'GET', '/users/self/verify'), self.secret_key)

        req = {
            "op": "login",
            "args": [{
                "apiKey":self.api_key,
                "passphrase":self.passphrase,
                "timestamp":timestamp,
                "sign":signature.decode("utf-8")
            }]
        }
        self.send_request(req)
        self.callbacks['login'] = self.on_login

class OkexRestApi():
    def __init__(self, gateway):
        self.gateway = gateway
        self.gateway_name = gateway.gateway_name

        self.url_base = ""

        self.api_key = ""
        self.secret_key = ""
        self.passphrase = ""

        self.order_count = 0
        self.order_count_lock = Lock()

        self.trade_api = None
        self.accout_api = None

    def connect(self, api_key, secret_key, passphrase, proxy_host, proxy_port):
        self.api_key = api_key
        self.secret_key = secret_key
        self.passphrase = passphrase

        if proxy_host and proxy_port:
            proxy = f"http://{proxy_host}:{proxy_port}"
            self.proxies = {"http": proxy, "https": proxy}

        self.trade_api = TradeAPI(api_key, secret_key, passphrase, self.proxies)
        self.accout_api = AccountAPI(api_key, secret_key, passphrase, self.proxies)


    def _new_order_id(self):
        with self.order_count_lock:
            self.order_count += 1
            return self.order_count

    # 设置好req，就可以下单了
    def send_order(self, req: OrderRequest):
        print("委托到达okex_gateway")
        client_orderid = f"a{self._new_order_id()}"
        print(req)
        response = self.trade_api.set_order(instId = req.instId, tdMode = req.tdMode, side = req.direction,
                       ordType = req.type, sz = req.volume, clOrdId=client_orderid, px=req.price)
        if response["code"] == '0':
            print(client_orderid + "委托成功")
        else:
            print(client_orderid + "委托失败")
            print(response["data"][0]["sCode"])
            print(response["data"][0]["sMsg"])

    def cancel_order(self, req: CancelRequest):
        response = self.trade_api.cancel_order(instId = req.instId, ordId = req.orderid)
        if response["code"] == 0:
            print(req.orderid + "撤单成功")
        else:
            print(req.orderid + "撤单失败")
            print(response["data"]["sCode"])
            print(response["data"]["sMsg"])

    # 手动查询账户余额，并放入事件引擎队列之中
    def query_account_balance(self, ccy):
        response = self.accout_api.get_balance(ccy=ccy)
        data = response["data"]
        details = data["details"]
        account = AccountData(
            currency=details["ccy"],
            cash_balance=details["cashBal"],
            avail_balance=details["availBal"],
            frozen_balance=details["frozenBal"],
            server_time=details["uTime"],
            datetime=datetime.now(UTC_TZ)
        )
        self.gateway.on_account(copy(account))

    def query_accont_pos_risk(self, instType=""):
        return self.accout_api.get_position_risk(instType)
