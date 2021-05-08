from System.strategy.template import StrategyTemplate
from System.strategy.engine import StrategyEngine
from System.trader.object import TickData, OrderData
import pandas as pd


class BuyLowSellHighStrategy(StrategyTemplate):

    # down_buy = 0.02
    # up_sell = 0.5
    # 为了测试，让信号更容易产生
    down_buy = 0.0005
    up_sell = 0.001
    tick_count = 0
    price_bench = 0
    # 是否允许首次购买
    first_buy = True
    side = ""

    trade = pd.DataFrame(columns=["datetime", "client_orderid", 'price', "side"])

    def __init__(self,
                 strategy_engine: StrategyEngine,
                 strategy_name: str):
        super().__init__(strategy_engine, strategy_name, setting="")

        pass

    def on_init(self):
        print("策略初始化")
        # self.write_log("策略初始化")

    def on_start(self):
        print("策略启动")
        # self.write_log("策略启动")

    def on_stop(self):
        print("策略停止")
        # self.write_log("策略停止")

    def on_tick(self, tick: TickData):
        print("BuyLowSellHighStrategy处理tick数据")
        print("接到tick数据，开始计算信号")
        latest_price = float(tick.last_price)
        if self.tick_count == 0:
            # 取最新成交价为基准
            self.price_bench = latest_price
            # 取过去24h最高价为基准
            # self.price_bench = tick.high_price
        if self.trade.empty and self.first_buy:
            print(latest_price, float(self.price_bench)*(1-self.down_buy))
            if latest_price <= float(self.price_bench)*(1-self.down_buy):
                # 执行市价单买入
                print("首次买入")
                self.price_bench = float(latest_price)
                self.side = "buy"
                self.buy("BTC-USDT", price=0, volume=0.002*float(latest_price))
        else:
            # 如果发生过成交，那么取最新成交的价格为基准
            # self.price_bench = self.trade['price'].values[-1]
            # side = self.trade['side'].values[-1]
            # 如果最后一笔成交是买入，则现在应该考虑卖出信号
            if self.side == "buy":
                print(self.price_bench * (1 + self.up_sell), latest_price)
                if self.price_bench * (1 + self.up_sell) <= latest_price:
                    self.price_bench = float(latest_price)
                    self.side = "sell"
                    print("高卖")
                    self.sell("BTC-USDT", price=0, volume=0.002)
            # 如果最后一笔成交是卖出，则现在应该考虑买入信号
            elif self.side == "sell":
                print(latest_price, self.price_bench * (1 - self.down_buy))
                if latest_price <= self.price_bench * (1 - self.down_buy):
                    self.price_bench = float(latest_price)
                    self.side = "buy"
                    print("低买")
                    self.buy("BTC-USDT", price=0, volume=0.002 * float(latest_price))


        self.tick_count += 1


    # 一旦订单被成交，则加入trade之中
    def on_order(self, order: OrderData):
        print("BuyLowSellHighStrategy处理order数据")
        print(order.status)
        self.first_buy = False
        if order.status == "filled":
            print("成交的价格为："+str(order.fillPx))
            trade = pd.Series([order.datetime, order.client_orderid, order.price, order.direction], index=["datetime", "client_orderid", 'price', "side"])
            self.trade = self.trade.append(trade, ignore_index=True)

    def write_log(self, msg: str) -> None:
        self.strategy_engine.write_log(msg, self)
