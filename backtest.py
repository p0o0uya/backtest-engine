from numpy import NAN, append, inf
import pandas as pd
import numpy as np
from PlotData import PlotData
from binance import binance
from collections import Counter
from Indicators import Indicators
from Strategies import Strategies
import time

class backtest:
    INTERVAL_DETAIL = {}
    INTERVAL_DETAIL['1m']   = {'insec': 60,      'tf_reference': 60000000000}
    INTERVAL_DETAIL['3m']   = {'insec': 180,     'tf_reference': 180000000000}
    INTERVAL_DETAIL['5m']   = {'insec': 300,     'tf_reference': 300000000000}
    INTERVAL_DETAIL['15m']  = {'insec': 900,     'tf_reference': 900000000000}
    INTERVAL_DETAIL['30m']  = {'insec': 1800,    'tf_reference': 1800000000000}
    INTERVAL_DETAIL['1h']   = {'insec': 3600,    'tf_reference': 3600000000000}
    INTERVAL_DETAIL['2h']   = {'insec': 7200,    'tf_reference': 7200000000000}
    INTERVAL_DETAIL['4h']   = {'insec': 14400,   'tf_reference': 14400000000000}
    INTERVAL_DETAIL['6h']   = {'insec': 21600,   'tf_reference': 21600000000000}
    INTERVAL_DETAIL['8h']   = {'insec': 28800,   'tf_reference': 28800000000000}
    INTERVAL_DETAIL['12h']  = {'insec': 43200,   'tf_reference': 43200000000000}
    INTERVAL_DETAIL['1d']   = {'insec': 86400,   'tf_reference': 86400000000000}
    INTERVAL_DETAIL['3d']   = {'insec': 259200,  'tf_reference': 259200000000000}
    INTERVAL_DETAIL['1w']   = {'insec': 604800,  'tf_reference': 604800000000000}
    INTERVAL_DETAIL['1M']   = {'insec': 2592000, 'tf_reference': 259200000000000}
    def __init__(self, symbol, filename:str, window:int=1000, strategy_name:str='', strategy_params:dict={}, tpsl_name:str='', tpsl_params:dict={}, indicatorsList:list=[]):
            self.symbol          = symbol
            self.window          = window
            self.timeframe       = strategy_params['main']['tf']
            self.indicatorsList  = indicatorsList
            self.strategy_params = strategy_params
            self.strategy_name   = strategy_name
            self.tpsl_params     = tpsl_params
            self.tpsl_name       = tpsl_name
            self.lastfather      = 0
            self.exchange        = binance(filename)
            self.df              = self.exchange.GetSymbolKlines(symbol, self.timeframe, window)
            # self.df              = pd.read_pickle('BTCUSDT_OHLC_5m_100000@1623927488694886865.pkl')
            for indicator in indicatorsList:
                Indicators.AddIndicator(self.df, indicator, strategy_params['main'])
            self.fdf = pd.DataFrame()
            if 'ftf' in strategy_params:
                self.fdf         = self.exchange.GetSymbolKlines(symbol, strategy_params['ftf']['tf'], window)
                # self.fdf         = pd.read_pickle('BTCUSDT_OHLC_1h_100000@1623927393290492341.pkl')
                for indicator in indicatorsList:
                    Indicators.AddIndicator(self.fdf, indicator, strategy_params['ftf'])
            self.last_price      = self.df['close'][len(self.df)-1]

    def findfather(self, time, fdf):
        if fdf.empty:
            return None
        for pj in range(self.lastfather, len(fdf)):
            if fdf['time'].iloc[pj]>time:
                self.lastfather = pj
                return fdf[0:pj]
        return fdf

def float2fixed(flt, prec):
    # print(flt)
    # print(prec)
    if np.isnan(flt):
        return flt
    return int(flt * prec)/prec

def totalpnl(capital, positions, leverage:int=1, fixed:bool=True):
    maxdraw = 80
    final = capital
    draw  = [final]
    sides = []
    if fixed:
        for item in positions:
            if item['status'] in ('tp', 'sl'):
                final += capital*((item['pnl']*leverage)/100) - capital*leverage*(0.0004)*2# - item['entryPrice']*leverage*(0.0004)
                draw.append(final)
                sides.append(item['signal'])
    else:
        for item in positions:
            if item['status'] in ('tp', 'sl'):
                final += final*((item['pnl']*leverage)/100) - final*leverage*(0.0004)*2# - item['entryPrice']*leverage*(0.0004)
                draw.append(final)
                sides.append(item['signal'])

    if len(draw)>1:
        if draw[1]>draw[0]:
            decline = []
        else:
            decline = [dict(top=draw[0])]
        mxdraw = []
        for pj in range(1, len(draw)-1):
            if draw[pj]>draw[pj-1] and draw[pj]>draw[pj+1]:
                decline.append(dict(top=draw[pj]))
            if draw[pj]<draw[pj-1] and draw[pj]<draw[pj+1]:
                decline[-1]['bot']  = draw[pj]
                mxdraw.append((1 - decline[-1]['bot']/decline[-1]['top'])*100)
        if mxdraw==[]:
            mxxdraw = 0
        else:
            mxxdraw = max(mxdraw)

        # print(final)
        # print(capital)
        # print(mxxdraw)
    else:
        mxxdraw = np.nan
    cntsides = Counter(sides)
    if len(sides):
        cntsides = (float2fixed(cntsides['long']/len(sides), 100), float2fixed(cntsides['short']/len(sides), 100))
    else:
        cntsides = (0, 0)
    return capital, float2fixed(final, 100), float2fixed((final-capital)/capital*100, 100), float2fixed(mxxdraw, 100), draw, cntsides

def winratio(posvec):
    lpnl   = len(posvec)
    if lpnl==0:
        return 0, 0, 0
    wins   = 0
    for item in posvec:
        if item['status'] == 'tp':
            wins += 1
    return lpnl, wins, float2fixed(wins/lpnl*100, 100)

def main(model):
    print('Starting Main Loop')
    positions = []
    sells     = []
    buys      = []
    tps       = []
    sls       = []
    concs     = []
    flag      = 0
    if strategy_params.__contains__('x'):
        startindx = strategy_params['x']
    else:
        startindx = 2

    for pj in range(startindx, model.window):
        # print(pj)
        childdf  = model.df.iloc[0:pj+1].copy()
        if not model.fdf.empty:
            fdfcopy  = model.fdf.copy() 
        else:
            fdfcopy = pd.DataFrame()
        fatherdf = model.findfather(childdf['time'].iloc[-1], fdfcopy)
        if flag==0:

            ret = Strategies.strategy(childdf, model.strategy_name, model.strategy_params, fdf=fatherdf)

            if ret['signal']:
                positions.append({'signal': ret['signal'], 'indx': pj, 'time': childdf['date'].iloc[pj], 'entryPrice': ret['entryPrice'], 'sl': None, 'tp': None, 'status': 'open', 'closeindx': None})
                ret1 = Strategies.tpsl(childdf, positions[-1], model.tpsl_name, model.tpsl_params)
                sl   = ret1[0]
                tp   = ret1[1]
                positions[-1]['sl'] = sl
                positions[-1]['tp'] = tp
                if ret['signal']=='long':
                    buys.append([childdf['date'].iloc[pj], ret['entryPrice']])
                if ret['signal']=='short':
                    sells.append([childdf['date'].iloc[pj], ret['entryPrice']])
                tps.append([childdf['date'].iloc[pj], tp])
                sls.append([childdf['date'].iloc[pj], sl])
                flag = 1
            else:
                tps.append([model.df['date'].iloc[pj], NAN])
                sls.append([model.df['date'].iloc[pj], NAN])
        elif flag==1:
            sgn        = 1 if positions[-1]['signal']=='long' else -1
            hl         = (sgn*model.df['high'].iloc[pj], sgn*model.df['low'].iloc[pj])
            ret1       = Strategies.tpsl(childdf, positions[-1], model.tpsl_name, model.tpsl_params)
            sl         = ret1[0]
            tp         = ret1[1]
            positions[-1]['sl'] = sl
            positions[-1]['tp'] = tp
            tps.append([model.df['date'].iloc[pj], tp])
            sls.append([model.df['date'].iloc[pj], sl])
            entryPrice = positions[-1]['entryPrice']
            if sgn*(sgn*min(hl)-sl)<0:
                concs.append([model.df['date'].iloc[pj], sl])
                flag = 0
                pnl  = (-(sgn*(entryPrice-sl))/entryPrice)*100
                if pnl<0:
                    positions[-1]['status']    = 'sl'
                elif pnl>0:
                    positions[-1]['status']    = 'tp'
                    positions[-1]['tp']        = sl
                else:
                    positions[-1]['status']    = 'null'
                positions[-1]['closeindx'] = pj
                positions[-1]['pnl']       = pnl
                
            elif sgn*(sgn*max(hl)-tp)>0:
                concs.append([model.df['date'].iloc[pj], tp])
                flag = 0
                pnl  = ((abs(entryPrice-tp))/entryPrice)*100
                positions[-1]['status']    = 'tp'
                positions[-1]['closeindx'] = pj
                positions[-1]['pnl']       = pnl
            
        else:
            raise('Invalid flag!')
    return positions, buys, sells, concs, tps, sls

if __name__ == "__main__":
    print("><"*50)
    print("main")
    filename = '/home/pj/Documents/Assets/Binance/api/keys.txt'
    symbol   = 'BTCUSDT' # 'BTCUSDT', 'ETHUSDT', 'DOTUSDT', 'DOGEUSDT'
    #################################################################################################################
    # tf       = '5m'      # '1m', '5m', '1h', '2h', '4h', '1d'
    # window   = 10000
    # # strategy_params = {'t': 9, 'k':26, 's':52, 'd':26, 'x': 3, 'ifreverse': False}
    # # strategy_params = {'t': 15, 'k':45, 's':90, 'd':45, 'x': 3, 'ifreverse': False}
    # # strategy_params = {'t': 20, 'k':60, 's':120, 'd':60, 'x': 3, 'ifreverse': False} #worst yet
    # strategy_params = {'t': 40, 'k':120, 's':240, 'd':120, 'x': 3, 'ifreverse': True} #best yet
    # # strategy_params = {'t': 80, 'k':240, 's':480, 'd':240, 'ifreverse': False}
    # # strategy_params = {'t': 160, 'k':480, 's':960, 'd':480, 'ifreverse': False}

    # strategy_name    = 'ichicross_v0'
    # tpsl_params      = {'slperc': 0.5, 'tpfactor':3}
    # # tpsl_name        = 'tpslfixed'
    # tpsl_name        = 'candletrailsl'
    # indicatorsList   = ['tenkiju', 'maximin']
    # indicatorstoplot = ['kijunsen', 'tenkansen']
    # model            = backtest(symbol, filename, tf, window, strategy_name, strategy_params, tpsl_name, tpsl_params, indicatorsList=indicatorsList)
    # pos, buys, sells, concs, tps, sls = main(model)
    # capital  = 100
    # leverage = 10
    # fixed    = False
    #################################################################################################################
    # tf       = '5m'      # '1m', '5m', '1h', '2h', '4h', '1d'
    # window   = 10000
    # # rsibullish = (0, 100); rsibearish = (0, 100)
    # # rsibullish = (50, 60); rsibearish = (40, 50)
    # ub = 10
    # lb = 0
    # rsibullish = (50+ub, 100-lb); rsibearish = (0+lb, 50-ub)
    # strategy_params  = {'t': 9, 'k':26, 's':52, 'd':26, 'n': 14, 'rsibullish': rsibullish, 'rsibearish': rsibearish, 'reverse': False}
    # strategy_name    = 'ichicross_v1'
    # tpsl_params      = {'slperc': 0.5, 'tpfactor':3}
    # tpsl_name        = 'tpslfixed'
    # indicatorsList   = ['tenkiju', 'rsi']
    # indicatorstoplot = ['tenkansen', 'kijunsen', 'rsi']

    # model           = backtest(symbol, filename, tf, window, strategy_name, strategy_params, tpsl_name, tpsl_params, indicatorsList=indicatorsList)
    # pos, buys, sells, concs, tps, sls = main(model)
    # capital         = 100
    # leverage        = 10
    ################################################################################################################
    # tf       = '1m'      # '1m', '5m', '1h', '2h', '4h', '1d'
    # ftf      = '1h'
    # window   = 5000  #107000#24*60*1
    # ifreverse        = False

    # strategy_params_maintf  = {'tf': tf, 't': 15, 'k':45, 's':90, 'd':45, 'x': 3}     
    # strategy_params_ftf     = {'tf': ftf, 'n': 10, 'rsibullish': (65, 100), 'rsibearish': (0, 35)} 
    # strategy_params         = {'main': strategy_params_maintf, 'ftf': strategy_params_ftf, 'ifreverse': ifreverse}    #best yet 


    # strategy_name    = 'ichicross_v2'
    # tpsl_params      = {'slperc': 1.5, 'tpfactor':1/3} #best yet
    # # tpsl_params      = {'slperc': 0.5, 'tpfactor':1.0}
    # # tpsl_name        = 'tpslfixed'
    # tpsl_name        = 'candletrailsl'
    # indicatorsList   = ['tenkansen', 'kijunsen', 'tenkiju', 'rsi', 'maximin']
    # indicatorstoplot = ['tenkansen', 'kijunsen', 'fdfrsi', 'rsi']
    # model            = backtest(symbol, filename, window, strategy_name, strategy_params, tpsl_name, tpsl_params, indicatorsList=indicatorsList)
    # pos, buys, sells, concs, tps, sls = main(model)
    # capital  = 100
    # leverage = 10
    # fixed    = True
    #################################################################################################################
    # tf       = '1m'      # '1m', '5m', '1h', '2h', '4h', '1d'
    # ftf      = '3m'
    # window   = 5000      #107000#24*60*1
    # ifreverse        = False
    # strategy_params_maintf  = {'tf': tf, 't': 5, 'k':22, 's':44, 'd':22, 'n': 8, 'x': 104, 'rsibullish': (50, 100), 'rsibearish': (0, 50)}     
    # strategy_params_ftf     = {'tf': ftf, 't': 3, 'k':15, 's':30, 'd':15, 'n': 7, 'x': 104, 'rsibullish': (54, 70), 'rsibearish': (30, 46)} 
    # strategy_params  = {'main': strategy_params_maintf, 'ftf': strategy_params_ftf, 'ifreverse': ifreverse}    #best yet 

    # strategy_name    = 'ichicross_v3'
    # # tpsl_params      = {'slperc': 0.5, 'tpfactor':1.0}
    # # tpsl_name        = 'tpslfixed'
    # # tpsl_params      = {'tpperc':0.5, 'offset': 0.0003} #best yet
    # # tpsl_name        = 'kijunsensl'
    # tpsl_params      = {'tpperc':0.3, 'offset': 0.0003} #best yet
    # tpsl_name        = 'kijunsensl_tpfixed'
    # # tpsl_params      = {}
    # # tpsl_name        = 'candletrailsl'
    # indicatorsList   = ['tenkansen', 'kijunsen', 'tenkiju', 'rsi', 'maximin']
    # indicatorstoplot = ['tenkansen', 'kijunsen', 'fdfrsi', 'rsi']
    # model            = backtest(symbol, filename, window, strategy_name, strategy_params, tpsl_name, tpsl_params, indicatorsList=indicatorsList)
    # pos, buys, sells, concs, tps, sls = main(model)
    # capital  = 100
    # leverage = 1
    # fixed    = True
    ################################################################################################################
    # tf       = '1m'      # '1m', '3m', '5m', '15m', '30m', '1h', '2h', '4h', '6h', '8h', 12h', '1d'
    # ftf      = '1h'
    # window   = 50000  #107000#24*60*1
    # bullish  = (65, 100); bearish = (0, 35)
    # minibullish = (0, 100); minibearish = (0, 100)
    # # minibullish = (60, 65); minibearish = (40, 45)
    # ifreverse       = False
    # strategy_params = {'t': 9, 'k':26, 's':52, 'd':26, 'n': 14, 'ftf': ftf, 'bullish': bullish, 'bearish': bearish, 'minibullish': minibullish, 'minibearish': minibearish, 'ifreverse': ifreverse}
    # strategy_name   = 'ichicross_v4'
    # tpsl_params     = {'slperc': 0.5, 'tpfactor':3} #best yet
    # # tpsl_params     = {'slperc': 0.5, 'tpfactor':3.5}
    # tpsl_name        = 'tpslfixed'
    # indicatorsList   = ['tenkansen', 'kijunsen', 'tenkiju', 'rsi']
    # indicatorstoplot = ['tenkansen', 'kijunsen', 'fdfrsi', 'rsi']
    # model            = backtest(symbol, filename, tf, window, strategy_name, strategy_params, tpsl_name, tpsl_params, indicatorsList=indicatorsList)
    # pos, buys, sells, concs, tps, sls = main(model)
    # capital  = 100
    # leverage = 3
    # fixed    = True
    #################################################################################################################
    # tf       = '1m'      # '1m', '5m', '1h', '2h', '4h', '1d'
    # ftf      = '1h'
    # window   = 20000  #107000#24*60*1
    # bullish = (65, 100); bearish = (0, 35)
    # strategy_params = {'t': 9, 'k':26, 's':52, 'd':26, 'n': 14, 'ftf': ftf, 'rsibullish': bullish, 'rsibearish': bearish}
    # strategy_name   = 'ichicross_v2'
    # tpsl_params     = {'slperc': 0.5, 'tpfactor':3} #best yet
    # # tpsl_params     = {'slperc': 0.5, 'tpfactor':3.5}
    # tpsl_name        = 'tpslfixed'
    # indicatorsList   = ['tenkansen', 'kijunsen', 'tenkiju', 'rsi']
    # indicatorstoplot = ['tenkansen', 'kijunsen', 'fdfrsi', 'rsi']
    # model            = backtest(symbol, filename, tf, window, strategy_name, strategy_params, tpsl_name, tpsl_params, indicatorsList=indicatorsList)
    # pos, buys, sells, concs, tps, sls = main(model)
    # capital  = 1000
    # leverage = 30
    # fixed    = False
    #################################################################################################################
    # tf                      = '5m'      # '1m', '5m', '1h', '2h', '4h', '1d'
    # window                  = 20000
    # strategy_params         = {'t': 52, 'threshold': [1.6, 10], 'rsibounds':[30, 70]}
    # strategy_name           = 'cancellation_v0'
    # tpsl_params             = {'slperc': 0.5, 'tpfactor':3} #best yet
    # tpsl_name               = 'tpslfixed'
    # tpsl_name               = 'tpslfromstrategy'
    # indicatorsList          = ['maximin', 'askbidratio', 'rsi', 'volume']
    # model                   = backtest(symbol, filename, tf, window, strategy_name, strategy_params, tpsl_name, tpsl_params, indicatorsList=indicatorsList)
    # pos, buys, sells, concs, tps, sls = main(model)
    # capital  = 100
    # leverage = 10
    #################################################################################################################
    # tf                      = '5m'      # '1m', '5m', '1h', '2h', '4h', '1d'
    # window                  = 10000
    # strategy_params         = {'t': 20, 'tipoutp': 0.3, 'slfactor':0.25}
    # strategy_name           = 'bollband_v0'
    # tpsl_params             = {'slperc': 0.5, 'tpfactor':8} #best yet
    # tpsl_name               = 'tpslfromstrategy'
    # indicatorsList          = ['ubb', 'lbb']
    # indicatorstoplot        = ['ubb', 'lbb']
    # model                   = backtest(symbol, filename, tf, window, strategy_name, strategy_params, tpsl_name, tpsl_params, indicatorsList=indicatorsList)
    # pos, buys, sells, concs, tps, sls = main(model)
    # capital  = 100
    # leverage = 10
    #################################################################################################################
    tf       = '15m'    # '1m', '5m', '1h', '2h', '4h', '1d'
    window   = 500      #107000#24*60*1
    ifreverse        = False
    strategy_params_maintf  = {'tf': tf, 'n1': 14, 'n2':42, 'diff': (-16, 16), 'x': 3}     
    strategy_params         = {'main': strategy_params_maintf, 'ifreverse': ifreverse}    #best yet 

    strategy_name    = 'rsidiff_v0'
    tpsl_params      = {'slperc': 0.5, 'tpfactor':3.0}
    tpsl_name        = 'tpslfixed'
    # tpsl_params      = {'tpperc':0.5, 'offset': 0.0003} #best yet
    # tpsl_name        = 'kijunsensl'
    # tpsl_params      = {'tpperc':0.3, 'offset': 0.0003} #best yet
    # tpsl_name        = 'kijunsensl_tpfixed'
    # tpsl_params      = {}
    # tpsl_name        = 'candletrailsl'
    indicatorsList   = ['rsidiff', 'maximin', 'stoch_rsi']
    # indicatorstoplot = ['rsidiff']
    indicatorstoplot = ['stoch_rsi']
    model            = backtest(symbol, filename, window, strategy_name, strategy_params, tpsl_name, tpsl_params, indicatorsList=indicatorsList)
    pos, buys, sells, concs, tps, sls = main(model)
    capital  = 100
    leverage = 1
    fixed    = True
    #################################################################################################################
    # for item in pos:
    #     print(item)
    print(pos)
    wr = winratio(pos)
    print(wr)
    pnl= totalpnl(capital, pos, leverage, fixed)
    print(pnl[:4])
    print(pnl[4])
    print(pnl[5])
    windowdaily = window*model.INTERVAL_DETAIL[tf]['insec']/60/60/24
    windowdaily = float2fixed(windowdaily, 100)
    freq        = float2fixed((wr[0]/windowdaily), 100)
    print('this backtest lasts for {} days and {} years'.format(windowdaily, float2fixed(windowdaily/365, 1000)))
    print('this strategy opens {} positions per day on average'.format(freq))

    #################################################################################################################
    indicators   = [dict(col_name="fast_ema",   color="indianred",                name="FAST EMA",             isactive=False),
                    dict(col_name="50_ema",     color="indianred",                name="50 EMA",               isactive=False),
                    dict(col_name="200_ema",    color="indianred",                name="200 EMA",              isactive=False),
                    dict(col_name="fast_sma",   color="rgba(102, 207, 255, 50)",  name="FAST SMA",             isactive=False),
                    dict(col_name="slow_sma",   color="rgba(255, 207, 102, 50)",  name="SLOW SMA",             isactive=False),
                    dict(col_name="lbb",        color="rgba(255, 102, 207, 50)",  name="Lower Bollinger Band", isactive=False),
                    dict(col_name="ubb",        color="rgba(255, 102, 207, 50)",  name="Upper Bollinger Band", isactive=False),
                    dict(col_name="tenkansen",  color="rgba(40, 40, 141, 100)",   name="tenkansen",            isactive=False),
                    dict(col_name="kijunsen",   color="rgba(140, 40, 40, 100)",   name="kijunsen",             isactive=False),
                    dict(col_name="senkou_a",   color="rgba(160, 240, 160, 100)", name="senkou_a",             isactive=False),
                    dict(col_name="senkou_b",   color="rgba(240, 160, 160, 50)",  name="senkou_b",             isactive=False),
                    dict(col_name="chikouspan", color="rgba(200, 130, 100, 100)", name="chikouspan",           isactive=False),
                    dict(col_name="swing",      color="rgba(220, 100, 200, 100)", name="swing",                isactive=False),
                    dict(col_name="rsi",        color="rgba(220, 100, 200, 100)", name="RSI",                  isactive=False),
                    dict(col_name="stoch_rsi",  color="rgba(220, 100, 200, 100)", name="STOCH RSI",            isactive=False),
                    dict(col_name="rsidiff",    color="rgba(220, 100, 200, 100)", name="RSI DIFFERENCE",       isactive=False),
                    dict(col_name="fdfrsi",     color="rgba(220, 100, 200, 100)", name="Father Timeframe RSI", isactive=False),
                    dict(col_name="volume",     color="rgba(220, 100, 200, 100)", name="volume",               isactive=False),
                    dict(col_name="tenkiju",    color="rgba(140, 40, 40, 100)",   name="tenkiju",              isactive=False),
                    dict(col_name="x_period_high", color="rgba(140, 40, 40, 100)", name="maximin",             isactive=False),
                    dict(col_name="x_period_low",  color="rgba(140, 40, 40, 100)", name="maximin",             isactive=False)]

    for item in indicators:
        if item['col_name'] in indicatorstoplot:
            item['isactive'] = True

    txtbox = {}
    txtbox['StrategyName']      = 'Strategy: {}'.format(strategy_name)
    txtbox['Duration']          = 'Duration: {} Days'.format(windowdaily)
    txtbox['Total']             = 'Total: {} Trades'.format(wr[0])
    txtbox['Won']               = 'Won: {} Trades'.format(wr[1])
    txtbox['WiningRatio']       = 'WinRatio: {} %'.format(wr[2])
    txtbox['Frequency']         = 'Frequency: {} per day'.format(freq)
    txtbox['Leverage']          = 'Leverage: {}'.format(leverage)
    txtbox['Balance']           = 'Balance: {} USDT'.format(pnl[0])
    txtbox['ConcludedBalance']  = 'Conc. Bal.: {} USDT'.format(pnl[1])
    txtbox['MaxDrawDown']       = 'mxdraw: {} %'.format(pnl[3])
    if 'ichi' in strategy_name:
        txtbox['tksd']              = 'tksd: {},{},{},{}'.format(strategy_params['main']['t'], strategy_params['main']['k'], strategy_params['main']['s'], strategy_params['main']['d'])
    if strategy_params.__contains__('ftf') and strategy_params['ftf'].__contains__('n'):
        txtbox['rsin']              = 'RSI (n): {}'.format(strategy_params['ftf']['n'])
    txtbox['tpsl']              = 'tpsl: {}'.format(tpsl_name)

    r2bnds = []
    if (strategy_params.__contains__('ftf') and strategy_params['ftf'].__contains__('rsibullish')):
        r2bnds.append(strategy_params['ftf']['rsibullish'][0])
        r2bnds.append(strategy_params['ftf']['rsibullish'][1])
    if (strategy_params.__contains__('ftf') and strategy_params['ftf'].__contains__('rsibearish')):
        r2bnds.append(strategy_params['ftf']['rsibearish'][0])
        r2bnds.append(strategy_params['ftf']['rsibearish'][1])
    if (strategy_params['main'].__contains__('rsibullish')):
        r2bnds.append(strategy_params['main']['rsibullish'][0])
        r2bnds.append(strategy_params['main']['rsibullish'][1])
    if (strategy_params['main'].__contains__('rsibearish')):
        r2bnds.append(strategy_params['main']['rsibearish'][0])
        r2bnds.append(strategy_params['main']['rsibearish'][1])
    if (strategy_params['main'].__contains__('diff')):
        r2bnds.append(strategy_params['main']['diff'][0])
        r2bnds.append(strategy_params['main']['diff'][1])
    else:
        r2bnds  = None

    if ('ftf' not in locals()):
        ftf  = None

    plotter = PlotData(model.df, model.symbol, indicators, fdf = model.fdf)
    plotter.plot(buy_signals = buys, sell_signals = sells, close_signals=concs, take_profits=tps, stop_losses=sls, row2bounds = r2bnds, rh=[80, 20], plot_title='{}_{}_{}_{}'.format(strategy_name, window, tf, ftf), text_box=txtbox)
    #print(model.df)
