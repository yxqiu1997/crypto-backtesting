import requests
import backtrader as bt
import pandas as pd
import json
import datetime as dt


def get_binance_bars(symbol, interval, start_time, end_time):
    url = "https://api.binance.com/api/v3/klines"
    start_time = str(int(start_time.timestamp() * 1000))
    end_time = str(int(end_time.timestamp() * 1000))
    limit = '1000'

    req_params = {'symbol': symbol, 'interval': interval, 'startTime': start_time, 'endTime': end_time, 'limit': limit}
    df = pd.DataFrame(json.loads(requests.get(url, params=req_params).text))
    if len(df.index) == 0:
        return None
    df = df.iloc[:, 0:6]
    df.columns = ['datetime', 'open', 'high', 'low', 'close', 'volume']

    df.open = df.open.astype('float')
    df.high = df.high.astype('float')
    df.low = df.low.astype('float')
    df.close = df.close.astype('float')
    df.volume = df.volume.astype('float')

    df.index = [dt.datetime.fromtimestamp(x / 1000.0) for x in df.datetime]

    return df


def get_data():
    df_list = []
    last_datetime = dt.datetime(2020, 1, 1)
    while True:
        new_df = get_binance_bars('BTCUSDT', '1d', last_datetime, dt.datetime.now())
        if new_df is None:
            break
        df_list.append(new_df)
        last_datetime = max(new_df.index) + dt.timedelta(0, 1)
    df = pd.concat(df_list)
    return df


class UltimateOscillatorStrategy(bt.Strategy):
    params = (
        ('period_1', 7),
        ('period_2', 14),
        ('period_3', 28)
    )

    def log(self, txt, dt=None):
        dt = dt or self.datas[0].datetime.date(0)
        print('%s, %s' % (dt.isoformat(), txt))

    def __init__(self):
        self.ULTOSC = bt.talib.ULTOSC(self.data.high, self.data.low, self.data.close,
                                      timeperiod1=self.params.period_1,
                                      timeperiod2=self.params.period_2,
                                      timeperiod3=self.params.period_3)

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            return
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(
                    'BUY EXECUTED, Price: {:.2f}, Cost: {:.2f}, Comm: {:.2f}'.format(
                        order.executed.price,
                        order.executed.value,
                        order.executed.comm
                    )
                )
                self.buyprice = order.executed.price
                self.buycomm = order.executed.comm
            else:
                self.log(
                    'SELL EXECUTED, Price: {:.2f}, Cost: {:.2f}, Comm: {:.2f}'.format(
                        order.executed.price,
                        order.executed.value,
                        order.executed.comm
                    )
                )
                self.bar_executed = len(self)

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('Order Canceled/Margin/Rejected')

        self.order = None

    def notify_trade(self, trade):
        if not trade.isclosed:
            return
        self.log('OPERATION PROFIT, GROSS %.2f, NET %.2f' %
            (trade.pnl, trade.pnlcomm)
        )

    def next(self):
        if not self.position:
            if self.ULTOSC < 30:
                self.buy()
        elif self.ULTOSC > 70:
            self.close()


if __name__ == '__main__':
    df = get_data()
    data = bt.feeds.PandasData(dataname=df)
    cerebro = bt.Cerebro()

    # Add a execution
    cerebro.addstrategy(UltimateOscillatorStrategy)

    # Add Data
    cerebro.adddata(data)

    # Set cash
    cerebro.broker.setcash(1000000.0)
    cerebro.broker.setcommission(commission=0.001)
    cerebro.addsizer(bt.sizers.PercentSizer, percents=10)

    # Run over everything
    print("start portfolio value {}".format(cerebro.broker.getvalue()))
    cerebro.run()
    print("end portfolio value {}".format(cerebro.broker.getvalue()))

    # Plot
    cerebro.plot(style='candle')
