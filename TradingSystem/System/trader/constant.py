from enum import Enum

class Exchange(Enum):

    OKEX = "OKEX"
    HUOBI = "HUOBI"

class Direction(Enum):

    LONG = "多"
    SHORT = "空"
    NET = "净"

class Status(Enum):

    SUBMITTING = "提交中"
    NOTTRADED = "未成交"
    PARTTRADED = "部分成交"
    ALLTRADED = "全部成交"
    CANCELLED = "已撤销"
    REJECTED = "拒单"

class Interval(Enum):

    MINUTE = "1m"
    HOUR = "1h"
    DAILY = "d"
    WEEKLY = "w"
    TICK = "tick"

class OrderType(Enum):

    LIMIT = "限价"
    MARKET = "市价"
    STOP = "STOP"
    FAK = "FAK"
    FOK = "FOK"
    RFQ = "询价"

class Offset(Enum):

    NONE = ""
    OPEN = "开"
    CLOSE = "平"
    CLOSETODAY = "平今"
    CLOSEYESTERDAY = "平昨"