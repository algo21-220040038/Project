import logging
from logging import Logger
import smtplib
import os
from abc import ABC
from datetime import datetime
from email.message import EmailMessage
from queue import Empty, Queue
from threading import Thread
from typing import Any, Sequence, Type, Dict, List, Optional

from System.event.engine import Event, EventEngine
from .app import BaseApp
from System.gateway.OKEX.okex_gateway import OkexGateway
from .object import *
from .event import *
from .setting import SETTINGS
from .utility import get_folder_path, TRADER_DIR


class MainEngine:

    def __init__(self, event_engine: EventEngine = None):
        if event_engine:
            self.event_engine: EventEngine = event_engine
        else:
            self.event_engine = EventEngine()
        self.event_engine.start()

        self.gateways = {}
        self.engines: Dict[str, BaseEngine] = {}
        self.apps: Dict[str, BaseApp] = {}
        self.exchanges: List[Exchange] = []

        self.init_engines()     # Initialize function engines

    # 添加引擎
    def add_engine(self, engine_class: Any) -> "BaseEngine":
        engine = engine_class(self, self.event_engine)
        self.engines[engine.engine_name] = engine
        return engine

    # 添加网关
    def add_gateway(self, gateway):
        # gateway = gateway_class(self.event_engine)
        self.gateways[gateway.gateway_name] = gateway

        for exchange in gateway.exchanges:
            if exchange not in self.exchanges:
                self.exchanges.append(exchange)

        return gateway

    # 添加应用
    def add_app(self, app_class):
        app = app_class()
        self.apps[app.app_name] = app

        engine = self.add_engine(app.engine_class)
        return engine

    # 初始化引擎，添加几个默认引擎
    def init_engines(self):
        # 添加日志引擎
        self.add_engine(LogEngine)
        # 添加订单管理引擎
        self.add_engine(OmsEngine)

    # 写日志
    def write_log(self, msg: str, source: str = "") -> None:
        log = LogData(msg=msg, gateway_name=source)
        event = Event("eLog", log)
        self.event_engine.put(event)

    # 获取特定网关
    def get_gateway(self, gateway_name: str):
        gateway = self.gateways.get(gateway_name, None)
        if not gateway:
            self.write_log(f"找不到底层接口：{gateway_name}")
        return gateway

    # 获取特定引擎
    def get_engine(self, engine_name: str):
        engine = self.engines.get(engine_name, None)
        if not engine:
            self.write_log(f"找不到引擎：{engine_name}")
        return engine

    # 获取默认设置（秘钥、代理信息等）
    def get_default_setting(self, gateway_name: str) -> Optional[Dict[str, Any]]:
        gateway = self.get_gateway(gateway_name)
        if gateway:
            return gateway.get_default_setting()
        return None

    # 获取所有网关名称
    def get_all_gateway_names(self) -> List[str]:
        return list(self.gateways.keys())

    # 获取所有应用
    def get_all_apps(self) -> List[BaseApp]:
        return list(self.apps.values())

    # 获取所有交易所
    def get_all_exchanges(self) -> List[Exchange]:
        return self.exchanges

    # 用特定的网关进行连接
    def connect(self, setting: dict, gateway_name: str) -> None:
        gateway = self.get_gateway(gateway_name)
        if gateway:
            gateway.connect(setting)

    # 用特定的网关去订阅某个频道，这里特定了是ticker频道
    def subscribe(self, req: SubscribeRequest, gateway_name: str) -> None:
        """
        Subscribe tick data update of a specific gateway.
        """
        gateway = self.get_gateway(gateway_name)
        if gateway:
            gateway.subscribe(req)

    # 就是在主引擎层面去调用网关的下单函数，即再次封装
    def send_order(self, req: OrderRequest, gateway_name: str="OKEX") -> str:
        """
        Send new order request to a specific gateway.
        """
        print("委托到达MainEngine")
        gateway = self.get_gateway(gateway_name)
        if gateway:
            return gateway.send_order(req)
        else:
            return ""

    def cancel_order(self, req: CancelRequest, gateway_name: str) -> None:
        gateway = self.get_gateway(gateway_name)
        if gateway:
            gateway.cancel_order(req)

    def send_orders(self, reqs: Sequence[OrderRequest], gateway_name: str) -> List[str]:
        gateway = self.get_gateway(gateway_name)
        if gateway:
            return gateway.send_orders(reqs)
        else:
            return ["" for req in reqs]

    def cancel_orders(self, reqs: Sequence[CancelRequest], gateway_name: str) -> None:
        gateway = self.get_gateway(gateway_name)
        if gateway:
            gateway.cancel_orders(reqs)

    def close(self) -> None:
        self.event_engine.stop()

        for engine in self.engines.values():
            engine.close()

        for gateway in self.gateways.values():
            gateway.close()

# 所有的Engine都有一个MainEngine，event_engine这样能保证用的都是同一个event_engine
class BaseEngine(ABC):

    def __init__(
        self,
        main_engine: MainEngine,
        event_engine: EventEngine,
        engine_name: str,
    ):
        self.main_engine = main_engine
        self.event_engine = event_engine
        self.engine_name = engine_name

    def close(self):
        pass


class LogEngine(BaseEngine):

    def __init__(self, main_engine: MainEngine, event_engine: EventEngine):
        super(LogEngine, self).__init__(main_engine, event_engine, "log")

        if not SETTINGS["log.active"]:
            return

        self.level: int = SETTINGS["log.level"]

        self.logger: Logger = logging.getLogger("VN Trader")
        self.logger.setLevel(self.level)

        self.formatter = logging.Formatter(
            "%(asctime)s  %(levelname)s: %(message)s"
        )

        self.add_null_handler()

        if SETTINGS["log.console"]:
            self.add_console_handler()

        if SETTINGS["log.file"]:
            self.add_file_handler()

        self.register_event()

    def add_null_handler(self) -> None:
        null_handler = logging.NullHandler()
        self.logger.addHandler(null_handler)

    def add_console_handler(self) -> None:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(self.level)
        console_handler.setFormatter(self.formatter)
        self.logger.addHandler(console_handler)

    def add_file_handler(self) -> None:
        today_date = datetime.now().strftime("%Y%m%d")
        filename = f"vt_{today_date}.log"
        log_path = get_folder_path("log")
        file_path = log_path.joinpath(filename)

        file_handler = logging.FileHandler(
            file_path, mode="a", encoding="utf8"
        )
        file_handler.setLevel(self.level)
        file_handler.setFormatter(self.formatter)
        self.logger.addHandler(file_handler)

    def register_event(self) -> None:
        self.event_engine.register("eLog", self.process_log_event)

    def process_log_event(self, event: Event) -> None:
        log = event.data
        self.logger.log(log.level, log.msg)


class OmsEngine(BaseEngine):

    def __init__(self, main_engine: MainEngine, event_engine: EventEngine):

        super(OmsEngine, self).__init__(main_engine, event_engine, "oms")

        self.ticks: Dict[str, TickData] = {}
        self.orders: Dict[str, OrderData] = {}
        self.trades: Dict[str, TradeData] = {}
        # self.positions: Dict[str, PositionData] = {}
        self.accounts: Dict[str, AccountData] = {}
        # self.contracts: Dict[str, ContractData] = {}

        self.active_orders: Dict[str, OrderData] = {}

        self.add_function()
        self.register_event()

    def add_function(self) -> None:

        self.main_engine.get_tick = self.get_tick
        self.main_engine.get_order = self.get_order
        self.main_engine.get_trade = self.get_trade
        # self.main_engine.get_position = self.get_position
        self.main_engine.get_account = self.get_account
        # self.main_engine.get_contract = self.get_contract
        self.main_engine.get_all_ticks = self.get_all_ticks
        self.main_engine.get_all_orders = self.get_all_orders
        self.main_engine.get_all_trades = self.get_all_trades
        # self.main_engine.get_all_positions = self.get_all_positions
        self.main_engine.get_all_accounts = self.get_all_accounts
        # self.main_engine.get_all_contracts = self.get_all_contracts
        self.main_engine.get_all_active_orders = self.get_all_active_orders

    # 让事件引擎增加这些事件的处理方法
    def register_event(self) -> None:
        print("OMSengine"+"注册事件处理器")
        self.event_engine.register(EVENT_TICK, self.process_tick_event)
        self.event_engine.register(EVENT_ORDER, self.process_order_event)
        self.event_engine.register(EVENT_TRADE, self.process_trade_event)
        self.event_engine.register(EVENT_ACCOUNT, self.process_account_event)
        # self.event_engine.register(EVENT_POSITION, self.process_position_event)
        # self.event_engine.register(EVENT_CONTRACT, self.process_contract_event)

    # 只存最新的tick数据
    def process_tick_event(self, event: Event) -> None:
        print("OMSengine"+"处理tick数据")
        tick = event.data
        self.ticks[tick.sys_symbol] = tick

    # order全部存下来(vt_orderid是唯一的，基于server_orderid)
    def process_order_event(self, event: Event) -> None:

        order = event.data
        self.orders[order.sys_orderid] = order

        # 这里可以随时检测order有没有完全成交或者撤单，以删减active_orders
        if order.is_active():
            self.active_orders[order.sys_orderid] = order
        elif order.sys_orderid in self.active_orders:
            self.active_orders.pop(order.sys_orderid)

    # trade也是记录每一次
    def process_trade_event(self, event: Event) -> None:

        trade = event.data
        self.trades[trade.sys_tradeid] = trade

    # 账户信息只记录最新的
    def process_account_event(self, event: Event) -> None:

        account = event.data
        self.accounts[account.sys_accountid] = account

    # 获取最新tick数据
    def get_tick(self, sys_symbol: str) -> Optional[TickData]:
        return self.ticks.get(sys_symbol, None)

    # 获取每个order的最新情况
    def get_order(self, sys_orderid: str) -> Optional[OrderData]:
        return self.orders.get(sys_orderid, None)

    # 通过tradeid获取trade数据，这里没有最新的概念，因为每个trade都会被保存
    def get_trade(self, sys_tradeid: str) -> Optional[TradeData]:
        return self.trades.get(sys_tradeid, None)

    # 获取最新account数据
    def get_account(self, sys_accountid: str) -> Optional[AccountData]:
        return self.accounts.get(sys_accountid, None)

    # 获取全部交易所的最新订单，目前实现的交易所只有OKEX
    def get_all_ticks(self) -> List[TickData]:
        return list(self.ticks.values())

    # 获取全部订单
    def get_all_orders(self) -> List[OrderData]:
        return list(self.orders.values())

    def get_all_trades(self) -> List[TradeData]:
        return list(self.trades.values())

    def get_all_accounts(self) -> List[AccountData]:
        return list(self.accounts.values())

    # 获取某个交易所active的委托
    def get_all_active_orders(self, sys_symbol: str = "") -> List[OrderData]:
        if not sys_symbol:
            return list(self.active_orders.values())
        else:
            active_orders = [
                order
                for order in self.active_orders.values()
                if order.sys_symbol == sys_symbol
            ]
            return active_orders