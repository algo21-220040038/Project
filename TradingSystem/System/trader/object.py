from dataclasses import dataclass
from datetime import datetime
from .constant import *
from logging import INFO

ACTIVE_STATUSES = ["live", "partially_filled"]

@dataclass
class BaseData():
    gateway_name: str

@dataclass
class TickData(BaseData):
    instId: str
    exchange: Exchange
    datetime: datetime

    name: str = ""
    volume: float = 0
    open_interest: float = 0
    last_price: float = 0
    last_volume: float = 0
    limit_up: float = 0
    limit_down: float = 0

    open_price: float = 0
    high_price: float = 0
    low_price: float = 0
    pre_close: float = 0

    def __post_init__(self):
        """"""
        self.sys_symbol = f"{self.instId}.{self.exchange.value}"

@dataclass
class BookData(BaseData):
    instId: str
    exchange: Exchange
    datetime: datetime

    bid_price_1: float = 0
    bid_price_2: float = 0
    bid_price_3: float = 0
    bid_price_4: float = 0
    bid_price_5: float = 0

    ask_price_1: float = 0
    ask_price_2: float = 0
    ask_price_3: float = 0
    ask_price_4: float = 0
    ask_price_5: float = 0

    bid_volume_1: float = 0
    bid_volume_2: float = 0
    bid_volume_3: float = 0
    bid_volume_4: float = 0
    bid_volume_5: float = 0

    ask_volume_1: float = 0
    ask_volume_2: float = 0
    ask_volume_3: float = 0
    ask_volume_4: float = 0
    ask_volume_5: float = 0

    def __post_init__(self):
        """"""
        self.sys_symbol = f"{self.instId}.{self.exchange.value}"

@dataclass
class BarData(BaseData):
    """
    Candlestick bar data of a certain trading period.
    """

    symbol: str
    exchange: Exchange
    datetime: datetime

    interval: Interval = None
    volume: float = 0
    open_interest: float = 0
    open_price: float = 0
    high_price: float = 0
    low_price: float = 0
    close_price: float = 0

    def __post_init__(self):
        """"""
        self.vt_symbol = f"{self.symbol}.{self.exchange.value}"

@dataclass
class OrderData(BaseData):

    instId: str
    exchange: Exchange
    server_orderid: str
    client_orderid: str

    type: str = None
    direction: str = None
    # offset = None
    price: float = 0
    volume: float = 0
    traded: float = 0
    # 用来标记委托的阶段
    status:str = None
    datetime: datetime = None
    reference: str = ""

    # 最新成交价格
    fillPx:float = 0

    def __post_init__(self):

        self.sys_symbol = f"{self.instId}.{self.exchange.value}"
        self.sys_orderid = f"{self.gateway_name}.{self.server_orderid}"

    def is_active(self) -> bool:

        if self.status in ACTIVE_STATUSES:
            return True
        else:
            return False

@dataclass
class TradeData(BaseData):
    instId: str
    exchange: Exchange
    server_orderid: str
    client_orderid: str
    tradeid: str
    direction:str = None

    price: float = 0
    volume: float = 0
    datetime: datetime = None

    def __post_init__(self):
        """"""
        self.sys_symbol = f"{self.instId}.{self.exchange.value}"
        self.sys_orderid = f"{self.gateway_name}.{self.server_orderid}"
        self.sys_tradeid = f"{self.gateway_name}.{self.tradeid}"

@dataclass
class PositionData(BaseData):
    instId: str
    exchange: Exchange
    direction: str

    volume: float = 0
    frozen: float = 0
    price: float = 0
    pnl: float = 0
    yd_volume: float = 0

    def __post_init__(self):
        """"""
        self.sys_symbol = f"{self.instId}.{self.exchange.value}"
        self.sys_positionid = f"{self.sys_symbol}.{self.direction}"


@dataclass
class AccountData(BaseData):
    currency: str
    # 币种余额
    cash_balance: float = 0
    # 可用余额
    avail_balance: float = 0
    # 币种占用余额
    frozen_balance: float = 0
    server_time: str = None
    datetime: datetime = None

    def __post_init__(self):

        self.sys_accountid = f"{self.gateway_name}.{self.currency}"

@dataclass
class LogData(BaseData):
    """
    Log data is used for recording log messages on GUI or in log files.
    """

    msg: str
    level: int = INFO

    def __post_init__(self):
        """"""
        self.time = datetime.now()

@dataclass
class SubscribeRequest(BaseData):
    exchange: Exchange

    channel:str
    instId: str
    instType:str = ""
    uly:str = ""
    ccy:str = ""

    def __post_init__(self):
        """"""
        self.sys_symbol = f"{self.instId}.{self.exchange.value}"

@dataclass
class OrderRequest:
    instId: str
    direction:str
    type:str
    volume: float

    exchange: Exchange = Exchange.OKEX

    tdMode:str = "cash"
    price: float = 0
    ccy:str = None
    clOrdId:str = None
    tag:str = None
    posSide:str = None
    reduceOnly:bool = None

    def __post_init__(self):
        """"""
        self.sys_symbol = f"{self.instId}.{self.exchange.value}"

@dataclass
class CancelRequest:
    orderid: str
    instId: str
    exchange: Exchange

    def __post_init__(self):
        """"""
        self.sys_symbol = f"{self.instId}.{self.exchange.value}"