import importlib
import os
import traceback
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Set, Tuple, Type, Any, Callable
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor
from tzlocal import get_localzone

from System.event.engine import Event, EventEngine
from System.trader.engine import BaseEngine, MainEngine
from System.trader.object import (
    OrderRequest,
    SubscribeRequest,
    LogData,
    TickData,
    OrderData,
    TradeData,
    PositionData,
    BarData,
)
from System.trader.event import *
from System.trader.constant import (
    Direction,
    OrderType,
    Interval,
    Exchange,
    Offset
)
from System.trader.utility import load_json, save_json, extract_vt_symbol, round_to

from .base import APP_NAME
from .template import StrategyTemplate

class StrategyEngine(BaseEngine):

    def __init__(self, main_engine: MainEngine, event_engine: EventEngine):
        super().__init__(main_engine, event_engine, APP_NAME)

        # self.classes: Dict[str, Type[StrategyTemplate]] = {}
        # self.strategies: Dict[str, StrategyTemplate] = {}
        self.strategies = []

        self.sys_tradeids: Set[str] = set()

    def register_event(self):
        print("strategyEngine"+"注册事件处理器")
        self.event_engine.register(EVENT_TICK, self.process_tick_event)
        self.event_engine.register(EVENT_ORDER, self.process_order_event)
        # self.event_engine.register(EVENT_TRADE, self.process_trade_event)
        # self.event_engine.register(EVENT_POSITION, self.process_position_event)

    def process_tick_event(self, event: Event):
        print("策略引擎处理tick数据")
        tick: TickData = event.data

        strategies = self.strategies
        if not strategies:
            return

        for strategy in strategies:
            if strategy.inited:
                self.call_strategy_func(strategy, strategy.on_tick, tick)

    def process_order_event(self, event: Event):
        order: OrderData = event.data

        strategies = self.strategies
        if not strategies:
            return

        for strategy in strategies:

            if strategy.inited:
                self.call_strategy_func(strategy, strategy.on_order, order)

    def call_strategy_func(
        self, strategy: StrategyTemplate, func: Callable, params: Any = None
    ):
        try:
            if params:
                func(params)
            else:
                func()
        except Exception:
            strategy.trading = False
            strategy.inited = False

            msg = f"触发异常已停止\n{traceback.format_exc()}"
            # self.write_log(msg, strategy)
            print(msg)

    def add_strategy(self, strategy: StrategyTemplate, strategy_name: str, setting: dict = None):
        # if strategy_name in self.strategies:
        #     self.write_log(f"创建策略失败，存在重名{strategy_name}")
        #     return
        print(strategy_name+"策略添加成功")

        # strategy_class = self.classes.get(class_name, None)
        # if not strategy_class:
        #     self.write_log(f"创建策略失败，找不到策略类{class_name}")
        #     return

        # strategy = strategy_class(self, strategy_name, setting)
        self.strategies.append(strategy)

    def send_server_order(
            self,
            strategy: StrategyTemplate,
            instId: str,
            direction: str,
            price: float,
            volume: float,
            type: str
    ):
        req = OrderRequest(
            instId=instId,
            tdMode="cash",
            direction=direction,
            price=price,
            volume=volume,
            type=type
        )
        print("委托到达StrategyEngine")
        self.main_engine.send_order(req)

    def send_limit_order(
            self,
            strategy: StrategyTemplate,
            exchange: str,
            instId: str,
            direction: str,
            price: float,
            volume: float
    ):
        return self.send_server_order(strategy, exchange, instId, direction, price, volume, type="limit")

    def _init_strategy(self, strategy_name: str):
        strategy = self.strategies[strategy_name]

        if strategy.inited:
            self.write_log(f"{strategy_name}已经完成初始化，禁止重复操作")
            return

        self.write_log(f"{strategy_name}开始执行初始化")

        # 调用策略自身的init回调函数
        self.call_strategy_func(strategy, strategy.on_init)

        strategy.inited = True
        self.write_log(f"{strategy_name}初始化完成")

    def start_strategy(self, strategy_name:str):
        strategy = self.strategies[strategy_name]
        if not strategy.inited:
            self.write_log(f"策略{strategy.strategy_name}启动失败，请先初始化")
            return

        if strategy.trading:
            self.write_log(f"{strategy_name}已经启动，请勿重复操作")
            return

        # 调用策略自身的start回调函数
        self.call_strategy_func(strategy, strategy.on_start)
        strategy.trading = True

    def stop_strategy(self, strategy_name: str):
        strategy = self.strategies[strategy_name]
        if not strategy.trading:
            return

        # 调用策略自身的stop回调函数
        self.call_strategy_func(strategy, strategy.on_stop)

        strategy.trading = False

    def write_log(self, msg: str, strategy: StrategyTemplate = None):
        """
        Create portfolio engine log event.
        """
        if strategy:
            msg = f"{strategy.strategy_name}: {msg}"

        log = LogData(msg=msg, gateway_name=APP_NAME)
        event = Event(type=EVENT_LOG, data=log)
        self.event_engine.put(event)

