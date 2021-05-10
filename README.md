# Trading system report

Our trading system resembles vn.py, an open-source trading system. It is composed of three major parts, namely, gateway, event engine and strategy. Gateway is responsible for commuting with crypto-currency exchange, it receives and send messages to the exchange automatically. Event engine is used to detect whether a trading signal is generated and then take corresponding action. Strategy is where all these action take place.

The general architecture is presented in the picture below:

![avatar](https://github.com/algo21-220040039/Project/raw/main/system%20architecture)



## **Gateway**

We first introduce the gateway, we use two different API to communicate with crypto-currency exchange - REST API and WebSocket API. 

**REST**

REST is short for Representational State Transfer, an architectural style. Rest API is based on HTTP; it sends request to the server and then receives feedback. Okex v5 API is implemented in /gateway/OKEX/rest_api

The base class is the client class, it implements the methods needed to query the server with either get, post or delete requests. Two more classes inherit the base class. The trade api can fulfill tasks such as placing orders, cancelling orders and querying historical orders. The account api can request the current position, balance, bills and so on of the account the api is connected to.

![avatar](https://github.com/algo21-220040039/Project/raw/main/rest%20api%20illustration)

**WebSocket**

WebSocket is a protocol based on HTML5, it establishes bi-directional communication of information between the server and end users. WebSocket allows the user to subscribe real-time data from the server. So we primarily use this API to get up-to-date market information from the exchange.

Once connected, we can choose to subscribe to different channels. There are two different types of channels - public and private. Public channels do not require logging in and feed current market information to subscribers. Private channels requires logging in and can be used for placing orders and other account specific tasks. 

Implementation of WebSocket API can be found in /gateway/ OKEX/ okex_gateway.py.  Inside the python file, we create a class called OkexWebsocketApi.  

```python
class OkexWebsocketApi():
    def __init__(self, gateway, channel_type):
        self.gateway = gateway
        self.gateway_name = gateway.gateway_name
        self.channel_type = channel_type
        self._ws_lock = Lock()
        self._ws = None
        self._worker_thread = None
        self._ping_thread = None
        self._active = False
        self.api_key = ""
        self.secret_key = ""
        self.passphrase = ""
        self.proxy_host = None
        self.proxy_port = None
        self.ping_interval = None
        self.trade_count = 0
        self.callbacks = {}

    def init(self, url, proxy_host, proxy_port, ping_interval=20):
    def connect(self, api_key, secret_key, passphrase, proxy_host, proxy_port):
    def on_connected(self):
    def _ensure_connection(self): 
    def on_disconnected(self):
    def _disconnect(self):
    def on_login(self, data):
    def on_recv(self, response):
    def _run(self):
    def _ping(self):
    def _run_ping(self):
    def start(self):
    def stop(self):
    def send_request(self, request:dict):
    def subscribe(self, channel, instId="", instType="", uly = "", ccy=""):
     ......
```

The variables are all self-explanatory. The only thing worth attention is that we define a ping interval. Because the server cuts connection if no new message is sent within 30 second. A ping method is implemented to send message to the server at this ping interval. Due to this, we use multi-threading to receive subscriptions and sending pings at the same time. Callbacks is used to store the information received from the server. 

The init method sets several parameters such as proxy, ping intervals etc.

Connect method tries to connect to the server and start receiving feeds. On_connected than subscribes to the default channel. _ensure_connection method is used to prevent multiple connections.

On_recv method converts the json objects we receive to standard python objects for storage. 

_run method will continuously try to receive information from the server and at the same time handle connection errors. 

As is described above, _run_ping method will send ping message to the server at given ping interval.

Once this WebSocket api is started, four threads are carried out simultaneously. We have the two threads to handle information from public and private channels, and two other ping threads to ensure the connection.

The subscribe method can subscribe to designated channels. More methods elaborating on the subscription to different channels are also implemented but not enumerated here.

## **Event Engine**

The event engine sort of detecting whether an 'event' (a trading signal etc.) appears and then assigning the corresponding methods() to deal with it. It should at least accomplish the following tasks:

1. register and cancel which events the engine should pay attention to 
2. link different methods to handle the aforementioned events
3. continuously watching the information inflow to tell whether an event has occurred

We implement this event engine in /event/engine.py. Below is the structure of this class:

```python
class EventEngine():
    def __init__(self, interval = 1):
        self._interval = interval
        self._queue = Queue()
        self._active = False
        self._thread = Thread(target = self._run)
        self._timer = Thread(target = self._run_timer)
        self._handlers = defaultdict(list)
        self._general_handlers = []

    def _run(self):
    def _process(self, event) -> None:
    def _run_timer(self) -> None:
    def start(self) -> None:      
    def stop(self) -> None:
    def put(self, event: Event) -> None:
    def register(self, type: str, handler) -> None:     
    def unregister(self, type: str, handler) -> None:
    def register_general(self, handler) -> None:      
    def unregister_general(self, handler) -> None:
```

We have, in this class, a number of private variables. Their meaning is quite straightforward : _active serves as a switch to turn on the engine, _handlers is a dictionary storing which methods to use for a event. The most important one is the _queue variable where we store all the events intercepted. Queue works in a First In First Out manner, so it is suitable for handling events. 

The function _run, by its name, defines how the engine works, it continuously tries to read from the queue and calls the _process function to assign the event(if any) to handler for future process.

The _start and _end function starts and stops the engine respectively.

The rest register/unregister functions can (un)register different handlers to different events. The word general means the handler can be called by all events.



## **Strategy**

We define a template class for all strategies. 

```python
class StrategyTemplate(ABC):
    def __init__(self, strategy_engine, strategy_name, setting):
        self.strategy_engine = strategy_engine
        self.strategy_name = strategy_name
        self.inited: bool = True
        self.trading: bool = True
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

    def sell(self,
             instId: str,
             price: float,
             volume: float
    ):
   
    def send_order(self,
                   instId: str,
                   direction:str,
                   price: float,
                   volume: float,
                   type: str = "market"
    ):

```

As is shown in the above abbreviated class code, this template contains several private variables, the first two shows what strategy engines(later introduced) and its name this class is added to. The two boolean variables shows the status of the strategy and the last two variables keep track of orders. The virtual functions indicate the action to take upon different scenarios. They are virtual in that they can be override by subclasses. The last three functions are clear in their intentions: they implement the buying and selling actions.

With various strategies classes , we define a strategy engine class to manage all these strategies:

One strategy engine keeps a list of the strategies it manages, it also log the trades happened in execution these strategies. As is shown later, the strategy shares the same event engine as the main engine. It registers what needs paying attention to to the event engine and tell the event engine what handlers to use for different event 

```python
class StrategyEngine(BaseEngine):

    def __init__(self, main_engine: MainEngine, event_engine: EventEngine):
        super().__init__(main_engine, event_engine, APP_NAME)
        self.strategies = []
        self.sys_tradeids: Set[str] = set()

    def register_event(self):
    def process_tick_event(self, event: Event):
    def call_strategy_func(
        self, strategy: StrategyTemplate, func: Callable, params: Any = None
    ):
    def add_strategy(self, strategy: StrategyTemplate, strategy_name: str, setting: dict = None):
    def send_server_order(
            self,
            strategy: StrategyTemplate,
            instId: str,
            direction: str,
            price: float,
            volume: float,
            type: str
    ):
    def send_limit_order(
            self,
            strategy: StrategyTemplate,
            exchange: str,
            instId: str,
            direction: str,
            price: float,
            volume: float
    ):
    def _init_strategy(self, strategy_name: str):
    def start_strategy(self, strategy_name:str):
    def stop_strategy(self, strategy_name: str):
    def write_log(self, msg: str, strategy: StrategyTemplate = None):
```

## How the system works

Having introduced the gateway, event engine and strategy engine, we are now ready to present how our trading system works. Below is a sample test of running our trading system:

```python
event_engine_test = EventEngine()
gateway_test = OkexGateway(event_engine_test,"OKEX")
gateway_test.connect()
main_engine_test = MainEngine(event_engine_test)
main_engine_test.add_gateway(gateway_test)
strategy_engine_test = StrategyEngine(main_engine_test, event_engine_test)
strategy_test = TestStrategy(strategy_engine_test, "Test")
strategy_engine_test.add_strategy(strategy_test, "Test")
strategy_engine_test.register_event()
```

We start by creating the gateway and event engine entities, then we add these to a new class we call main engine. The main engine is an integrated class where functionalities like communication, event handling, logging and order management are all included. The strategy engine is created by passing event engine and main engine to it. In this way we can make sure strategy and main engine use the same event engine. In the end, we can add different strategies and register events and handlers for the event engine. 

## Back testing on a simple strategy

We tried out a simple speculation strategy on the historical data acquired from the Okex Rest API. 

The rule of this strategy is fairly naive, we have the price of last traded crypto-currency as the base price(if there is no trade history, the first price recorded is the base price). We then, buy the currency with 99% of whole wealth (the rest 1% is kept to pay for fees etc.) whenever the price falls 2% under the base price and sell all of our holdings whenever the price has risen 50% above the base price. 

The detailed implementation can be found in /backtest/backtest.py

Here are the performance metrics :

| metric                | value   |
| --------------------- | ------- |
| total return          | 245.87% |
| annualized return     | 155.53% |
| maximal drawdown      | -60.20% |
| annualized volatility | 63.21%  |
| Sharpe ratio          | 2.3974  |
| Sortino ratio         | 3.3427  |

