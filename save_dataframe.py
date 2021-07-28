from numpy import append
import pandas as pd
import plotly.graph_objs as go
from plotly.subplots import make_subplots
from plotly.offline import plot
from binance import binance
from collections import Counter
from Indicators import Indicators
from Strategies import Strategies
import time


if __name__ == "__main__":
    print("><"*50)
    print("main")
    filename = '/home/pj/Documents/Assets/Binance/api/keys.txt'
    symbol   = 'BTCUSDT' # 'BTCUSDT', 'ETHUSDT', 'DOTUSDT', 'DOGEUSDT'
    #################################################################################################################
    exchange        = binance(filename)
    tf              = '5m'      # '1m', '5m', '1h', '2h', '4h', '1d'
    window          = 100000
    df              = exchange.GetSymbolKlines(symbol, tf, window)
    filename        = '{}_OHLC_{}_{}@{}.pkl'.format(symbol, tf, window, time.time_ns())
    df.to_pickle(filename)