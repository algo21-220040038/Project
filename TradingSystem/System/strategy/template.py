from abc import ABC
from copy import copy
from typing import Dict, Set, List, TYPE_CHECKING
from collections import defaultdict

from System.trader.constant import Interval
from System.trader.object import BarData, TickData, OrderData, TradeData
from System.trader.utility import virtual

class StrategyTemplate(ABC):

    def __init__(self, strategy_engine, strategy_name, setting):
        self.strategy_engine = strategy_engine
        self.strategy_name = strategy_name

        # 是否初始化与是否启动
        self.inited: bool = True
        self.trading: bool = True

        # 委托
        self.orders: Dict[str, OrderData] = {}
        self.active_orderids: Set[str] = set()


    @virtual
    def on_init(self) -> None:
        pass

    @virtual
    def on_start(self) -> None:
        pass

    @virtual
    def on_stop(self) -> None:
        pass

    @virtual
    def on_tick(self, tick: TickData) -> None:
        pass

    def buy(self,
            instId: str,
            price: float,
            volume: float
    ):
        return self.send_order(instId=instId, direction="buy", price=price, volume=volume)

    def sell(self,
             instId: str,
             price: float,
             volume: float
    ):
        return self.send_order(instId=instId, direction="sell", price=price, volume=volume)

    def send_order(self,
                   instId: str,
                   direction:str,
                   price: float,
                   volume: float,
                   type: str = "market"
    ):
        if self.trading:
            self.strategy_engine.send_server_order(self,
                                                   instId=instId,
                                                   direction=direction,
                                                   price=price,
                                                   volume=volume,
                                                   type=type
                                                   )
        else:
            pass
