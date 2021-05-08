from collections import defaultdict
from queue import Empty, Queue
from threading import Thread
from time import sleep
import sqlite3
import os
from typing import Any, Callable, List

EVENT_TIMER = "eTimer"
class Event:
    def __init__(self, type, data = None):
        self.type = type
        self.data = data

class EventEngine():
    def __init__(self, interval = 1):
        self._interval = interval
        self._queue = Queue()
        self._active = False
        self._thread = Thread(target = self._run)
        self._timer = Thread(target = self._run_timer)
        self._handlers = defaultdict(list)

        self._general_handlers = []
        self.register('eTick.', self.save_etick)
        self.register('eBook.', self.save_ebook)

    def _run(self):
        while self._active:
            print('run_active')
            try:
                event = self._queue.get(block=True, timeout=1)
                self._process(event)
            except Empty:
                pass

    def _process(self, event) -> None:
        # 给每种事件分配处理函数
        if event.type in self._handlers:
            print('process_event')
            [handler(event) for handler in self._handlers[event.type]]
            print(self._handlers[event.type])
        if self._general_handlers:
            [handler(event) for handler in self._general_handlers]

    # 相当于每隔一段时间就产生一个“空事件”
    def _run_timer(self) -> None:
        while self._active:
            sleep(self._interval)
            event = Event(EVENT_TIMER)
            self.put(event)

    def start(self) -> None:
        self._active = True
        self._thread.start()
        self._timer.start()

    def stop(self) -> None:
        self._active = False
        # join用来等待子线程结束再结束，反之未知错误
        self._timer.join()
        self._thread.join()

    def put(self, event: Event) -> None:
        self._queue.put(event)
        print(event.data)

    def register(self, type: str, handler) -> None:
        # 为某种类型的事件增加处理器，这里检查了一下原来有没有这个处理器，没有的话就新加上
        handler_list = self._handlers[type]
        if handler not in handler_list:
            handler_list.append(handler)

    def unregister(self, type: str, handler) -> None:
        handler_list = self._handlers[type]

        if handler in handler_list:
            handler_list.remove(handler)

        if not handler_list:
            self._handlers.pop(type)

    def register_general(self, handler) -> None:
        if handler not in self._general_handlers:
            self._general_handlers.append(handler)

    def unregister_general(self, handler) -> None:
        """
        Unregister an existing general handler function.
        """
        if handler in self._general_handlers:
            self._general_handlers.remove(handler)

    def save_ebook(self,event):
        if not os.path.exists('./data'):
                os.mkdir('./data')
        conn = sqlite3.connect('./data/Coin.db')
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS  book_BTC_USDT
                   (Time Datetime PRIMARY KEY     NOT NULL,
                    bid_price_1           INT     NOT NULL,
                    bid_price_2           INT     NOT NULL,
                    bid_price_3           INT     NOT NULL,
                    bid_price_4           INT     NOT NULL,
                    bid_price_5           INT     NOT NULL,
                    ask_price_1           INT     NOT NULL,
                    ask_price_2           INT     NOT NULL,
                    ask_price_3           INT     NOT NULL,
                    ask_price_4           INT     NOT NULL,
                    ask_price_5           INT     NOT NULL,
                    bid_volume_1           INT     NOT NULL,
                    bid_volume_2           INT     NOT NULL,
                    bid_volume_3           INT     NOT NULL,
                    bid_volume_4           INT     NOT NULL,
                    bid_volume_5           INT     NOT NULL,
                    ask_volume_1           INT     NOT NULL,
                    ask_volume_2           INT     NOT NULL,
                    ask_volume_3           INT     NOT NULL,
                    ask_volume_4           INT     NOT NULL,
                    ask_volume_5           INT     NOT NULL);''')
        c.execute(
            "insert into book_BTC_USDT (Time,bid_price_1,bid_price_2,bid_price_3,bid_price_4 ,bid_price_5,\
                                                ask_price_1,ask_price_2,ask_price_3,ask_price_4 ,ask_price_5,\
                                                bid_volume_1 ,bid_volume_2 ,bid_volume_3 ,bid_volume_4 ,bid_volume_5,\
                                                ask_volume_1 ,ask_volume_2 ,ask_volume_3 ,ask_volume_4 ,ask_volume_5) values (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            [event.data.datetime,event.data.bid_price_1,event.data.bid_price_2,event.data.bid_price_3,event.data.bid_price_4 ,event.data.bid_price_5,
                              event.data.ask_price_1,event.data.ask_price_2,event.data.ask_price_3,event.data.ask_price_4 ,event.data.ask_price_5,
                              event.data.bid_volume_1 ,event.data.bid_volume_2 ,event.data.bid_volume_3 ,event.data.bid_volume_4 ,event.data.bid_volume_5,
                              event.data.ask_volume_1 ,event.data.ask_volume_2 ,event.data.ask_volume_3 ,event.data.ask_volume_4 ,event.data.ask_volume_5])
        # c.execute('''insert into etick_BTC_USDT (Time,bid_price_1,bid_price_2,bid_price_3,bid_price_4 ,bid_price_5,
        #                                         ask_price_1,ask_price_2,ask_price_3,ask_price_4 ,ask_price_5,
        #                                         bid_volume_1 ,bid_volume_2 ,bid_volume_3 ,bid_volume_4 ,bid_volume_5,
        #                                         ask_volume_1 ,ask_volume_2 ,ask_volume_3 ,ask_volume_4 ,ask_volume_5)
        #               VALUES (event.data.datetime,event.data.bid_price_1,event.data.bid_price_2,event.data.bid_price_3,event.data.bid_price_4 ,event.data.bid_price_5,
        #                                       event.data.ask_price_1,event.data.ask_price_2,event.data.ask_price_3,event.data.ask_price_4 ,event.data.ask_price_5,
        #                                       event.data.bid_volume_1 ,event.data.bid_volume_2 ,event.data.bid_volume_3 ,event.data.bid_volume_4 ,event.data.bid_volume_5,
        #                                       event.data.ask_volume_1 ,event.data.ask_volume_2 ,event.data.ask_volume_3 ,event.data.ask_volume_4 ,event.data.ask_volume_5)''')
        conn.commit()
        conn.close()



    def save_etick(self,event):
        if not os.path.exists('./data'):
                os.mkdir('./data')
        conn = sqlite3.connect('./data/Coin.db')
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS  etick_BTC_USDT
                           (Time            Datetime PRIMARY KEY     NOT NULL,
                            volume           INT     NOT NULL,
                            open_interest           INT     NOT NULL,
                            last_price           INT     NOT NULL,
                            last_volume           INT     NOT NULL,
                            limit_up           INT     NOT NULL,
                            limit_down           INT     NOT NULL,
                            open_price           INT     NOT NULL,
                            high_price           INT     NOT NULL,
                            low_price           INT     NOT NULL,
                            pre_close           INT     NOT NULL);''')
        c.execute(
            "insert into etick_BTC_USDT (Time, volume , open_interest , last_price, last_volume, limit_up , limit_down, open_price , high_price ,low_price, pre_close) values (?,?,?,?,?,?,?,?,?,?,?)",
            [event.data.datetime, event.data.volume,event.data.open_interest, event.data.last_price, event.data.last_volume,
             event.data.limit_up, event.data.limit_down,
             event.data.open_price, event.data.high_price, event.data.low_price, event.data.pre_close])
        conn.commit()
        conn.close()