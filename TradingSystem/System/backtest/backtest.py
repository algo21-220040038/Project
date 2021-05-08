# coding:utf-8 
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
import sqlite3
import datetime
import time

# configuration
fee_rate = 0.0003
slippage = 5.0
capital = 10000000
stop_profit_rate = 3
stop_loss_rate =  0.5

class BackTestModel:
    def __init__(self, data):
        self.data = data
        self.time = self.data['time']
        self.remain_money = capital
        self.total_money = pd.Series([self.remain_money],[self.time[0]])
        self.trade = pd.DataFrame(columns=["time", "num", 'price'])
        self.hold_number = 0
        self.cost = 0

    def buy(self, time, num):  # Buy BTC.
        price = self.data[self.data['time']==time]['close'].values[0]
        trade = pd.Series([time, num, price], index=["time","num", 'price'])
        if  self.remain_money - ( price*num  + num*slippage + num * fee_rate ) >=0:
            self.trade = self.trade.append(trade, ignore_index=True)
            self.remain_money -= (price * num + num * slippage + num * price * fee_rate)
            self.hold_number += num
            print("Time %s, buy %d BTC" % (time, num))
            if abs(self.hold_number) >= 1e-4:
                self.cost = price
        else:
            print("The principal is not sufficient.")

    def sell(self, time, num):# Sell BTC.
        price = self.data[self.data['time'] == time]['close'].values[0]
        trade = pd.Series([time, -num, price], index=["time","num", 'price'])
        self.trade = self.trade.append(trade, ignore_index=True)
        self.hold_number -= num
        self.remain_money += price * num - num*slippage - num * fee_rate * price
        print("Time %s, sell %d BTC" % (time, num))
        if abs(self.hold_number) >= 1e-4:
            self.cost = price

    # Close all positions.
    def close(self, time):
        if self.hold_number < 0:
            self.buy(time, self.hold_number)
        elif self.hold_number > 0:
            self.sell(time, self.hold_number)

    # If the return of a position exceeds the rate we set,
    # then we will stop profit and close the position.
    def stop_profit(self, time):
        price = self.data[self.data['time'] == time]['close'].values[0]
        if self.hold_number > 0:
            if price >= self.cost*(1+stop_profit_rate):
                self.close(time)
                print("Stop profit: all positions have been closed.")
        elif self.hold_number <0:
            if price <= self.cost*(1-stop_profit_rate):
                self.close(time)
                print("Stop profit: all positions have been closed.")

    # If the loss of a position exceeds the rate we set,
    # then we will stop loss and close the position.
    def stop_loss(self, time):
        price = self.data[self.data['time'] == time]['close'].values[0]
        if self.hold_number > 0:
            if price <= self.cost*(1-stop_loss_rate):
                self.close(time)
                print("Stop loss: all positions have been closed.")
        elif self.hold_number < 0:
            if price >= self.cost*(1+stop_loss_rate):
                self.close(time)
                print("Stop loss: all positions have been closed.")

    # Test whether we should stop profit or stop loss, and recalculate the total assets we have at present every day.
    def update(self, time):
        if abs(self.hold_number) >= 1e-4:
            self.stop_loss(time)
        if abs(self.hold_number) >= 1e-4:
            self.stop_profit(time)
        value = self.data[self.data['time'] == time]['close'].values[0] * self.hold_number
        self.total_money = self.total_money.append(pd.Series([value+self.remain_money],[time]))

    def cacul_performance(self):
        """
        Calculate annualized return, Sharpe ratio, maximal drawdown, return volatility and sortino ratio
        :return: annualized return, Sharpe ratio, maximal drawdown, return volatility and sortino ratio
        """
        for i in range(len(self.total_money)):
            if abs(self.total_money[i]-capital) >= 1:
                self.begin_index = i-1
                break
            self.begin_index = 0

        t1 = self.data.iloc[self.begin_index,0]
        t2 = self.data.iloc[-1,0]
        self.DAY_MAX = (t2-t1).days
        rtn = self.total_money[-1] / capital - 1

#        annual_rtn = np.power(rtn + 1, 365.0 / self.DAY_MAX) - 1  # 复利
        annual_rtn = rtn * 365 / self.DAY_MAX  # 单利
#        print(self.total_money)
        annual_lst = pd.Series(self.total_money).pct_change().dropna()
        annual_vol = np.array(annual_lst).std()*np.sqrt(24*365)

        rf = 0.04
        semi_down_list = [annual_lst[k] for k in range(self.DAY_MAX - 1) if annual_lst[k] < rf]
        semi_down_vol = np.array(semi_down_list).std()*np.sqrt(24*365)
        sharpe_ratio = (annual_rtn - rf) / annual_vol
        sortino_ratio = (annual_rtn - rf) / semi_down_vol

        max_drawdown_ratio = 0
        for e, i in enumerate(self.total_money):
            for f, j in enumerate(self.total_money):
                if f > e and float(j - i) / i < max_drawdown_ratio:
                    max_drawdown_ratio = float(j - i) / i

        # Plot
        print('Return: %.2f%%' % (rtn * 100.0))
        print('Annualized Return: %.2f%%' % (annual_rtn * 100.0))
        print('Maximal Drawdown: %.2f%%' % (max_drawdown_ratio * 100.0))
        print('Annualized Vol: %.2f%%' % (100.0 * annual_vol))
        print('Sharpe Ratio: %.4f' % sharpe_ratio)
        print('Sortino Ratio: %.4f' % sortino_ratio)

        plt.figure(figsize=(8, 5))
        plt.plot(self.total_money)
        plt.xticks([self.total_money.index[i] for i in range(0, len(self.total_money), 300)], rotation = 20)
        plt.xlabel('Date')
        plt.ylabel('Money')
        plt.title('Money Curve')
        plt.grid(True)
        plt.show()

    def run(self):
        for t in self.time[1:]:
            if t.minute ==0:
                self.update(t)
            if t.hour == 0 and t.minute == 0:
                self.strategy(t)
                print(t)
        self.cacul_performance()

    def strategy(self, time):
        pass

class Strategy(BackTestModel):
    def __init__(self, data):
        super(Strategy, self).__init__(data)
        self.down_buy = 0.02
        self.up_sell = 0.5

    def strategy(self, time):
        price = self.data[self.data['time'] == time]['close'].values[0]
        if self.trade.empty:
            if price <= self.data['close'][0]*(1-self.down_buy):
                self.buy(time, 0.99*self.remain_money/price)
            return None
        if self.hold_number != 0:
            buy_price = self.trade['price'].values[-1]
            if buy_price*(1+self.up_sell) <= price:
                self.sell(time, self.hold_number)
            return None
        if self.hold_number == 0:
            sell_price = self.trade['price'].values[-1]
            if price <= sell_price * (1 - self.down_buy):
                self.buy(time, 0.99 * self.remain_money / price)

def timestamp_datetime(value):
    value = time.localtime(value/1000)
    return datetime.datetime(value.tm_year, value.tm_mon, value.tm_mday,
                             value.tm_hour, value.tm_min)

if __name__ == '__main__':
    # 连接本地数据库
    conn = sqlite3.connect('./Kline/BT_Coin.db')
    c = conn.cursor()
    response = c.execute('select * from BTC_USDT')

    data = response.fetchall()

    data = pd.DataFrame(data)
    data.iloc[:, 0] = [timestamp_datetime(t) for t in data.iloc[:, 0]]

    data.columns = ['time', 'open', 'high', 'low', 'close', 'volumn', 'turnover']
    data.sort_values(by='time', inplace=True)

    data = data.reset_index()
    data = data.drop('index', axis=1)

    S = Strategy(data)
    S.run()
