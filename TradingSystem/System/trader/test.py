from System.gateway.OKEX.okex_gateway import OkexGateway
from System.event.engine import EventEngine
from System.trader.object import OrderRequest, SubscribeRequest
from System.trader.constant import *
from System.trader.engine import MainEngine
from System.strategy.engine import StrategyEngine
from System.strategy.strategies.test_strategy import TestStrategy
from System.strategy.strategies.buylowsellhigh import BuyLowSellHighStrategy

# OKEX网关启动示例
event_engine_test = EventEngine()
gateway_test = OkexGateway(event_engine_test,"OKEX")
gateway_test.connect()
main_engine_test = MainEngine(event_engine_test)
main_engine_test.add_gateway(gateway_test)
strategy_engine_test = StrategyEngine(main_engine_test, event_engine_test)
# strategy_test = TestStrategy(strategy_engine_test, "Test")
# strategy_engine_test.add_strategy(strategy_test, "Test")
strategy_test = BuyLowSellHighStrategy(strategy_engine_test, "BuyLowSellHigh")
strategy_engine_test.add_strategy(strategy_test, "BuyLowSellHigh")
strategy_engine_test.register_event()

# 委托示例，买用USDT计价，卖用BTC计价
# 58126是当时看的最新卖1
# req = OrderRequest(exchange=Exchange.OKEX, instId="BTC-USDT", tdMode="cash", direction="buy", type="market", volume=0.005 * 58126)
# req = OrderRequest(exchange=Exchange.OKEX, instId="BTC-USDT", tdMode="cash", direction="sell", type="market", volume=0.001)
# gateway_test.send_order(req)

# 订阅示例
# 公有频道订阅
# req = SubscribeRequest(channel="", instId="", )
# gateway_test.subscribe("public", req)
# 私有频道订阅
# gateway_test.subscribe("private", req)

# 手动查询账户持仓风险
# response = gateway_test.query_account_pos_risk()
# print(response)