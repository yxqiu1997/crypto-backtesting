import datetime

import backtrader as bt
import pandas as pd


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

    def next(self):
        if not self.position:
            if self.ULTOSC < 30:
                self.buy()
        elif self.ULTOSC > 70:
            self.close()


if __name__ == '__main__':
    # Create a cerebro entity
    cerebro = bt.Cerebro()

    # Add data
    dataframe = pd.read_csv('../data/^GSPC.csv')
    dataframe['Date'] = pd.to_datetime(dataframe['Date'])
    dataframe.set_index('Date', inplace=True)

    # data = bt.feeds.PandasData(dataname=dataframe,
    #                            fromdate=datetime.datetime(2011, 1, 1),
    #                            todate=datetime.datetime(2023, 9, 3),
    #                            timeframe=bt.TimeFrame.Days)
    data = bt.feeds.PandasData(dataname=dataframe,
                               fromdate=datetime.datetime(2011, 1, 1),
                               todate=datetime.datetime(2023, 9, 3),
                               timeframe=bt.TimeFrame.Minutes,
                               compression=60)
    cerebro.adddata(data)

    # Add a execution
    cerebro.addstrategy(UltimateOscillatorStrategy)

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
