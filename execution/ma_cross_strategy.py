import requests
import backtrader as bt
import pandas as pd
import json
import datetime as dt
import matplotlib.pyplot as plt


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


class MaCrossStrategy(bt.Strategy):
    params = (
        ('fast_length', 5),
        ('slow_length', 25)
    )

    def __init__(self):
        ma_fast = bt.ind.SMA(period=self.params.fast_length)
        ma_slow = bt.ind.SMA(period=self.params.slow_length)
        self.crossover = bt.ind.CrossOver(ma_fast, ma_slow)

    def next(self):
        if not self.position:
            if self.crossover > 0:
                self.buy()
        elif self.crossover < 0:
            self.close()


if __name__ == '__main__':
    df = get_data()
    data = bt.feeds.PandasData(dataname=df)
    cerebro = bt.Cerebro()

    # Add a execution
    cerebro.addstrategy(MaCrossStrategy)

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
