from numpy import append
import pandas as pd
import plotly.graph_objs as go
from plotly.subplots import make_subplots
from plotly.offline import plot
from binance import binance
from collections import Counter
from Indicators import Indicators
import time

class CheckProb:
    
    def __init__(self, symbol, filename:str, timeframe:str='4h', window:int=1000):
            self.symbol     = symbol
            self.timeframe  = timeframe
            self.exchange   = binance(filename)
            self.df         = self.exchange.GetSymbolKlines(symbol, timeframe, window)
            self.last_price = self.df['close'][len(self.df['close'])-1]

    def volatilizer(self, symbol, tf, limit):
        df  = self.exchange.GetSymbolKlines(symbol, tf, limit)
        ldf = len(df)
        chper = []
        for indx, item in df.iterrows():
            rng = item['high']-item['low']
            chper.append(rng/item['close'])
        return sum(chper)/ldf

    def volcandleanalizor(self, df, volrange:list=[5500, 30000]):
        lndf     = len(df)
        candlerange = []
        for pj in range(0, lndf):
            if (df['volume'][pj]>volrange[0] and df['volume'][pj]<volrange[1]):
                candlerange.append((df['low'][pj], df['high'][pj]))
        ranges = []
        for item in candlerange:
            ranges.append(item[1]-item[0])
        ave = sum(ranges)/len(ranges)
        print(ave)
        return

        return volthreshold, len(volthreshold)

    def askbidratio(self, df):
        lndf     = len(df)
        abratio  = []
        epvol    = 1
        vol      = df['volume']
        print('Volume min:{}, ave:{}, max:{}'.format(min(vol), vol.abs().mean(), max(vol)))
        rng  = df['close'] - df['open']
        print('Body range min:{}, ave:{}, max:{}'.format(min(rng), rng.abs().mean(), max(rng)))
        for pj in range(0, lndf):
            if vol[pj]<epvol:
                print('vol is zero')
                vol[pj] = epvol
                # abratio.append(None)
            abratio.append(rng[pj]/vol[pj])
        # df['abratio'] = abratio

        ave0 = sum(abratio)/len(abratio)
        ave1 = sum(map(abs, abratio))/len(abratio)
        print(ave0)
        print(ave1)
        print(min(abratio))
        print(max(abratio))
        return

    def paststream(self, stream, close):
        check = []
        # print(stream)
        for ind, item in stream.iterrows():
            # print(item)
            if item['close']>close:
                check.append('higher')
            elif item['close']<close:
                check.append('lower')
            else:
                check.append('equal')
        cnt = Counter(check)
        # print(cnt)
        percH = cnt['higher']/(len(stream))
        percL = cnt['lower']/(len(stream))
        return percH, percL

    def prob(self, symbol, timeframe, percil:float=0.01):
        df     = self.df
        length = len(df)
        open   = df['open']
        close  = df['close']
        high   = df['high']
        low    = df['low']
        tm     = df['time']

        color = []
        for pj in range(0, length):
            if open[pj]<close[pj]:
                color.append('green')
            else:
                color.append('red')
        penet    = []
        penetval = []
        for pj in range(length-1, 0, -1):
            # print(pj)
            cprev  = close[pj-1]
            tprev  = tm[pj-1]
            stream = self.exchange.GetSymbolSubData(symbol, timeframe, tprev, '1m')
            percH, percL = self.paststream(stream, cprev)
            mov   = percil*cprev
            if color[pj-1]=='green':
                lowet = low[pj]
                diff  = (cprev - lowet)
                if diff > mov:
                    penet.append(True)
                else:
                    penet.append(False)
            else:
                hist  = high[pj]
                diff  = (hist - cprev)
                if diff > mov:
                    penet.append(True)
                else:
                    penet.append(False)
            penetval.append(diff/cprev)
            print("data says {:.4f} higher and {:.4f} lower the close of {:5} candle with {:.4f} percent look back".format(percH, percL, color[pj-1], penetval[-1]))
        return color, penet, penetval

    def swingrabber(self, df):
        swingH = []
        swingL = []
        for pj in range(1, len(df)-1):
            if (df['low'][pj]==min([df['low'][pj-1], df['low'][pj], df['low'][pj+1]])):
                swingL.append(df['low'][pj])
            if (df['high'][pj]==max([df['high'][pj-1], df['high'][pj], df['high'][pj+1]])):
                swingH.append(df['high'][pj])
        return (swingH, swingL)
    
    def crossdetector(self, ichidiff):
        crosses = []
        ln      = len(ichidiff)
        for pj in range(1, ln):
            if (ichidiff[pj] >= 0) and (ichidiff[pj-1] < 0):
                crosses.append((pj, 'long'))
                continue
            if (ichidiff[pj] <= 0) and (ichidiff[pj-1] > 0):
                crosses.append((pj, 'short'))
                continue
        return crosses, len(crosses)

    def swingdetector(self, df):
        swings = []
        ln      = len(df)
        for pj in range(2, ln):
            if (df['low'].iloc[pj-1] == min((df['low'].iloc[pj], df['low'].iloc[pj-1], df['low'].iloc[pj-2]))):
                if (df['close'].iloc[pj-1] == min((df['close'].iloc[pj], df['close'].iloc[pj-1], df['close'].iloc[pj-2]))):
                    if (df['high'].iloc[pj] == max((df['high'].iloc[pj], df['high'].iloc[pj-1], df['high'].iloc[pj-2]))):
                        swings.append((pj, 'long'))
                        continue
            if (df['high'].iloc[pj-1] == max((df['high'].iloc[pj], df['high'].iloc[pj-1], df['high'].iloc[pj-2]))):
                if (df['close'].iloc[pj-1] == max((df['close'].iloc[pj], df['close'].iloc[pj-1], df['close'].iloc[pj-2]))):
                    if (df['low'].iloc[pj] == min((df['low'].iloc[pj], df['low'].iloc[pj-1], df['low'].iloc[pj-2]))):
                        swings.append((pj, 'short'))
                        continue
        return swings, len(swings)

    def crossrsi(self, ichidiff, rsi):
        def isinrange(x, rng:list):
            a = rng[0]
            b = rng[1]
            _isinrange = True if (x>a and x<b) else False
            return _isinrange

        crosses = []
        ln = len(ichidiff)
        for pj in range(1, ln):
            if (ichidiff[pj] > 0) and (ichidiff[pj-1] <= 0):
                if isinrange(rsi[pj], [52.5, 55]):
                    crosses.append((pj, 'long'))
                    continue
            if (ichidiff[pj] < 0) and (ichidiff[pj-1] >= 0):
                if isinrange(rsi[pj], [45, 47.5]):
                    crosses.append((pj, 'short'))
                continue
        return crosses, len(crosses)
    
    def volthreshold(self, df, t:float=[5500, 30000]):
        lndf  = len(df)
        volthreshold = []
        for pj in range(2, lndf):
            side = 'long' if df['close'][pj-1]<df['open'][pj-1] else 'short'
            if (df['volume'][pj-1]>t[0] and df['volume'][pj-1]<t[1]) and (df['volume'][pj-2]<t[0]):
                volthreshold.append((pj, side))
        return volthreshold, len(volthreshold)

    def voldouble(self, df):
        lndf         = len(df)
        volthreshold = []
        tail         = 9
        fac          = 3
        for pj in range(tail, lndf):
            side = 'long' if df['close'][pj-1]<df['open'][pj-1] else 'short'
            if (df['volume'][pj-1]>fac*max(list(df['volume'].iloc[-tail:]))):
                volthreshold.append((pj, side))
        return volthreshold, len(volthreshold)

    def pressdetector(self, df, tail:int=5, tpp:int=2, ep:float=0.05):
        lndf         = len(df)
        presses      = []
        for pj in range(tail, lndf):
            entryprice = df['close'][pj-1]
            minH = min(list(df['high'].iloc[pj-tail:pj]))
            maxC = max(list(df['close'].iloc[pj-tail:pj]))
            minC = min(list(df['close'].iloc[pj-tail:pj]))
            maxL = max(list(df['low'].iloc[pj-tail:pj]))
            maxO = max(list(df['open'].iloc[pj-tail:pj]))
            minO = min(list(df['open'].iloc[pj-tail:pj]))
            alfa = minH>maxC
            beta = maxL<minC
            zeta = maxO<=maxC
            gama = minO>=minC
            if alfa and (not beta):# and zeta:
                side = 'short'
                sl   = max(list(df['high'].iloc[pj-tail:pj])) + ep
                tp   = entryprice-tpp*(sl-entryprice)
                # # side = 'long'
                # tp   = max(list(df['high'].iloc[pj-tail:pj])) - ep
                # sl   = entryprice-tpp*(tp-entryprice)
                presses.append((pj, side, entryprice, sl, tp))
                
            elif beta and (not alfa):# and gama:
                side = 'long'
                sl   = min(list(df['low'].iloc[pj-tail:pj])) - ep
                tp   = entryprice+tpp*(entryprice-sl)
                # side = 'short'
                # tp   = min(list(df['low'].iloc[pj-tail:pj])) + ep
                # sl   = entryprice+tpp*(entryprice-tp)
                presses.append((pj, side, entryprice, sl, tp))
        return presses, len(presses)

    def isprofitable(self, df, canindx, posit, mxdraw:float=-5, mndraw:float=-0.8): # -5.63
        leverage     = 10
        lndf         = len(df)
        startprice   = df['close'][canindx]
        endprice     = startprice
        if posit == 'long':
            check = 'low'
            sgn   = 1
            # maxdrawprice = (mxdraw/(sgn*leverage*100))*startprice + startprice
            # sl = max([min([df['low'][canindx], df['low'][canindx-1]]), maxdrawprice])
            sl = min([df['low'][canindx], df['low'][canindx-1]])

        else:
            check = 'high'
            sgn   = -1
            # maxdrawprice = (mxdraw/(sgn*leverage*100))*startprice + startprice
            # sl = min([max([df['high'][canindx], df['high'][canindx-1]]), maxdrawprice])
            sl = max([df['high'][canindx], df['high'][canindx-1]])
        initialpnl = (sgn*(sl - startprice)/startprice) * leverage * 100
        if (initialpnl < mxdraw) or (initialpnl > mndraw):
            return 0, initialpnl
        # maxdrawprice = (mxdraw/(sgn*leverage*100))*startprice + startprice
        # if sgn*(sl - maxdrawprice) < 0:
        #     return 0

        for pj in range(canindx+1, lndf):
            if sgn*(df[check][pj] - sl) <= 0:
                endprice = sl
                break
            else:
                # if not sgn*(df[check][pj-1]- maxdrawprice) < 0:
                sl  = df[check][pj-1]
        pnl = (sgn*(endprice - startprice)/startprice) * leverage * 100
        return pnl, initialpnl

    def isprofitable_fixed(self, df, canindx, posit, tpp:float=0.021):
        leverage     = 10
        lndf         = len(df)
        entryprice   = df['open'][canindx]
        if posit == 'long':
            tp    = entryprice + tpp*entryprice/leverage
            sgn   = 1
            check = 'high'
        else:
            tp    = entryprice - tpp*entryprice/leverage
            sgn   = -1
            check = 'low'
        endprice  = df[check][canindx]
        if sgn*(tp-endprice) < 0:
            # print(tpp*100)
            return tpp*100, endprice
        else:
            endprice     = df['close'][canindx]
            pnl          = (sgn*(endprice - entryprice)/entryprice) * leverage * 100
            # print(pnl)
        return pnl, endprice


    def isprofitable_tp_sl(self, df, canindx, posit, sl, tp):
        leverage     = 10
        lndf         = len(df)
        entryprice   = df['close'][canindx]
        pnl          = 0
        endprice     = 0
        for pj in range(canindx+1, lndf):
            canH     = df['high'][pj]
            canL     = df['low'][pj]
            if posit == 'long':
                if canL<sl:
                    endprice     = sl
                    pnl          = ((endprice - entryprice)/entryprice) * leverage * 100
                    break
                elif canH>tp:
                    endprice     = tp
                    pnl          = ((endprice - entryprice)/entryprice) * leverage * 100
                    break
            else:
                if canH>sl:
                    endprice     = sl
                    pnl          = (-(endprice - entryprice)/entryprice) * leverage * 100
                    break
                elif canL<tp:
                    endprice     = tp
                    pnl          = (-(endprice - entryprice)/entryprice) * leverage * 100
                    break
        return pnl, endprice

    def totpnl(self, capital, vec):
        final = capital
        for item in vec:
            # final += capital*(item/100)
            final += final*(item/100)
        return final, (final-capital)/capital*100

    def winratio(self, pnl):
        lpnl   = len(pnl)
        traded = 0
        wins   = 0
        for item in pnl:
            if not item == 0:
                traded += 1
            if item > 0:
                wins += 1
        return lpnl, traded, wins, wins/traded

if __name__ == "__main__":
    print("><"*50)
    print("main")
    filename = '/home/pj/Documents/Assets/Binance/api/keys.txt'
    symbol   = 'BTCUSDT' # 'BTCUSDT', 'ETHUSDT', 'DOTUSDT', 'DOGEUSDT'
    tf       = '5m'      # '1m', '5m', '1h', '2h', '4h', '1d'
    window   = 100000
    model    = CheckProb(symbol, filename, tf, window)
    Indicators.AddIndicator(model.df, indicator_name="tenkiju")
    Indicators.AddIndicator(model.df, indicator_name="rsi")
    # print(model.df['volume'].max())
    # print(model.df['volume'].min())
    print("><"*50)
    # crosses1, lnc1 = model.crossdetector(model.df['tenkiju'])
    # crosses2, lnc2 = model.crossrsi(model.df['tenkiju'], model.df['rsi'])
    # swings1,  lns1 = model.swingdetector(model.df)
    # volthre1, lnv1 = model.volthreshold(model.df, t=[5500, 28000])
    # volthre2, lnv2 = model.voldouble(model.df)
    # presses1, lnp1 = model.pressdetector(model.df, tail=9, tpp=2.5, ep=100)
    # model.volcandleanalizor(model.df, volrange=[5500, 30000])
    model.askbidratio(model.df)
    # print(lnc1)
    # print(lnc2)
    # print(lns1)
    # print(lnv1)
#    print(lnp1)
    # PNL   = []
    # sides = []
    # for item in presses1:
    #     # pnl, initialpnl = model.isprofitable(model.df, item[0], item[1])
    #     # pnl, initialpnl = model.isprofitable_fixed(model.df, item[0], item[1], tpp=0.024)
    #     pnl, initialpnl = model.isprofitable_tp_sl(model.df, item[0], item[1], sl=item[3], tp=item[4])

    #     if pnl:
    #         PNL.append(pnl)
    #         sides.append(item[1])
    #     if pnl>-200 and pnl!=0:
    #         print(pnl)
    #         print(initialpnl)
    #         print(item)
    #         print('*'*50)

    # winratio = model.winratio(PNL)
    # print('final, percentage, winning ratio are:')
    # print(model.totpnl(100, PNL)[0])
    # print(model.totpnl(100, PNL)[1])
    # print(winratio)
    # print(Counter(sides))

    # print('this backtest lasts for {} days'.format(window*5/60/24))
