from System.trader.object import *
from System.strategy.template import StrategyTemplate
from time import time


class TestStrategy(StrategyTemplate):
    """"""
    author = "用Python的交易员"

    test_trigger = 3

    tick_count = 0
    test_all_done = False

    parameters = ["test_trigger"]
    variables = ["tick_count", "test_all_done"]

    def __init__(self, strategy_engine, strategy_name, setting=""):
        """"""
        super().__init__(strategy_engine, strategy_name, setting="")

        self.test_funcs = [
            self.test_market_order,
            # self.test_limit_order,
            # self.test_cancel_all,
            # self.test_stop_order
        ]
        self.last_tick = None

    def on_init(self):
        # self.write_log("策略初始化")
        print("策略初始化")

    def on_start(self):
        # self.write_log("策略启动")
        print("策略启动")

    def on_stop(self):
        # self.write_log("策略停止")
        print("策略停止")

    def on_tick(self, tick: TickData):
        if self.test_all_done:
            return

        self.last_tick = tick

        self.tick_count += 1
        print("接收的tick数据个数："+str(self.tick_count))
        if self.tick_count >= self.test_trigger:
            self.tick_count = 0

            if self.test_funcs:
                test_func = self.test_funcs.pop(0)
                print(test_func)
                start = time()
                test_func()
                time_cost = (time() - start) * 1000
                # self.write_log("耗时%s毫秒" % (time_cost))
            else:
                # self.write_log("测试已全部完成")
                self.test_all_done = True


    def test_market_order(self):
        """"""
        self.buy("BTC-USDT", price=0, volume=60)
        # self.write_log("执行市价单测试")

    def test_limit_order(self):
        """"""
        print(0.001*float(self.last_tick.last_price))
        self.buy("BTC-USDT", price=self.last_tick.last_price, volume=60)
        # self.write_log("执行限价单测试")

    def test_stop_order(self):
        """"""
        self.buy(self.last_tick.ask_price_1, 1, True)
        # self.write_log("执行停止单测试")

    def test_cancel_all(self):
        """"""
        self.cancel_all()
        # self.write_log("执行全部撤单测试")
