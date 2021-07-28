from PlotData import *
# from Database import *
from Indicators import Indicators
from Strategies import Strategies

class TradingModel:

    def __init__(self, symbol, filename:str, timeframe:str='4h', window:int=1000):
        self.PlotData = PlotData(symbol, filename, timeframe, window)
        #model.database = 

if __name__ == "__main__":
    print("main")
    filename = '/home/pj/Documents/Assets/Binance/api/keys.txt'
    symbol = 'BTCUSDT'; perc = 0.007; cnt = 10
    # symbol = 'ETHUSDT'; perc = 0.01; cnt = 15
    # symbol = 'DOTUSDT'; perc = 0.01; cnt = 3
    # symbol   = 'DOTUSDT' #'BTCUSDT', 'ETHUSDT', 'DOTUSDT'
    tf1      = '5m'
    tf2      = '1h'
    window1  = 1000
    window2  = 100
    STRATEGY_PARAMS               = {}
    STRATEGY_PARAMS['t']          = 9
    STRATEGY_PARAMS['k']          = 26
    STRATEGY_PARAMS['s']          = 52
    STRATEGY_PARAMS['d']          = 26
    STRATEGY_PARAMS['n_ema']      = 21
    STRATEGY_PARAMS['ftf']        = '1h'
    STRATEGY_PARAMS['rsibullish'] = (65, 100)
    STRATEGY_PARAMS['rsibearish'] = (0, 35)
    STRATEGY_PARAMS['name']       = 'ichicross_v2'   #('ichicross_v2', 'Swing', 'Vol')
    model1   = TradingModel(symbol, filename, tf1, window1)
    Indicators.AddIndicator(model1.PlotData.df, "ema", STRATEGY_PARAMS);  model1.PlotData.indicators[0]['isactive'] = True
    Indicators.AddIndicator(model1.PlotData.df, "tenkansen", STRATEGY_PARAMS);  model1.PlotData.indicators[7]['isactive'] = True
    Indicators.AddIndicator(model1.PlotData.df, "kijunsen", STRATEGY_PARAMS);  model1.PlotData.indicators[8]['isactive'] = True

    # print(model2.PlotData.df['rsi'])
    # signal = Strategies.RunStrategy(model.PlotData.df, strategy_name="bollband")
    # model1.PlotData.df['swing'] = model2.PlotData.df['swing']
    print(model1.PlotData.df['ema'][window1-1])
    print(model1.PlotData.df)
    model1.PlotData.plot(plot_title='test', rh=[0.50, 0.50])
    # print(signal)

