from Indicators import Indicators, Swingrabber
import numpy as np

# But first, because we're not computing the indicators in TradingModel anymore,
# if they don't already exist within the df, we will be computing them here
def inrange(a, rng):
    if a>rng[0] and a<rng[1]:
        return True
    return False

def float2fixed(flt, prec):
    if np.isnan(flt):
        return flt
    return int(flt * prec)/prec
    
def emaCross(df, args:list=[]):
    ''' If Slow MA and fast ema cross, return True'''

    if not df.__contains__('50_ema') and not df.__contains__('200_ema'):
        Indicators.AddIndicator(df, indicator_name="ema", col_name="50_ema", args=50)
        Indicators.AddIndicator(df, indicator_name="ema", col_name="200_ema", args=200)
    for i in range(len(df)):
        if i > 0 and df['50_ema'][i-1] <= df['200_ema'][i-1] and df['50_ema'][i] > df['200_ema'][i]:
            return 'long'
    return None

def bollband_v0(df, tipoutp, slfactor):
    if not df.__contains__('lbb') or not df.__contains__('ubb'):
        raise Exception("indicator missing from the data frame")
    # tipoutp percentage of band width that the price allowed to break before signal is issued
    # slfactor coef of tipout as stop loss
    bwidth   = df['ubb'].iloc[-1]-df['lbb'].iloc[-1]
    tipout   = tipoutp*bwidth
    signal   = None
    sl       = None
    if df['close'].iloc[-1] > (df['ubb'].iloc[-1] + tipout):
        signal  =  "short"
        sl = df['close'].iloc[-1] + slfactor*tipout
    elif df['close'].iloc[-1] < (df['lbb'].iloc[-1] - tipout):
        signal  =  "long"
        sl = df['close'].iloc[-1] - slfactor*tipout
    
    ret = {}
    ret['date']        = df['date'].iloc[-1]
    ret['signal']      = signal
    ret['sl']          = sl
    ret['entryPrice']  = df['close'].iloc[-1]
    return ret

def ichicross_v0(df, reverse):
    ichidiff = list(df.iloc[-2:]['tenkiju'])
    signal = None
    # print(ichidiff)
    if (ichidiff[1] >= 0) and (ichidiff[0] < 0):
        if reverse:
            signal = 'short'
        else:
            signal = 'long'
    if (ichidiff[1] <= 0) and (ichidiff[0] > 0):
        if reverse:
            signal = 'long'
        else:
            signal = 'short'
    ret = {}
    ret['signal']      = signal
    ret['ichidiff']    = ichidiff
    ret['entryPrice']  = df['close'].iloc[-1]
    return ret

def ichicross_v1(df, rsibullish:tuple=(50, 100), rsibearish:tuple=(0, 50), reverse:bool=False):
    ichidiff = list(df.iloc[-2:]['tenkiju'])
    rsi      = df.iloc[-1]['rsi']
    signal = None
    if inrange(rsi, rsibullish) and (ichidiff[1] >= 0) and (ichidiff[0] < 0):
        if reverse:
            signal = 'short'
        else:
            signal = 'long'
    if inrange(rsi, rsibearish) and (ichidiff[1] <= 0) and (ichidiff[0] > 0):
        if reverse:
            signal = 'long'
        else:
            signal = 'short'
    ret = {}
    ret['signal']      = signal
    ret['ichidiff']    = ichidiff
    ret['entryPrice']  = df['close'].iloc[-1]
    return ret

def ichicross_v2(df, fdf, rsibullish:tuple=(50, 100), rsibearish:tuple=(0, 50), reverse:bool=False):
    # print(df)    
    ichidiff = list(df['tenkiju'].iloc[-2:])
    rsi      = fdf['rsi'].iloc[-1]
    signal   = None
    if inrange(rsi, rsibullish) and (ichidiff[1] >= 0) and (ichidiff[0] < 0):
        signal = 'short' if reverse else 'long'
    if inrange(rsi, rsibearish) and (ichidiff[1] <= 0) and (ichidiff[0] > 0):
        signal = 'long' if reverse else 'short'
    ret = {}
    ret['date']        = df['date'].iloc[-1]
    ret['signal']      = signal
    ichdiff_fixed      = []
    for item in ichidiff:
            ichdiff_fixed.append(float2fixed(item, 1000))
    ret['ichidiff']    = ichdiff_fixed
    ret['rsi']         = float2fixed(rsi, 100)
    ret['entryPrice']  = df['close'].iloc[-1]
    return ret

def ichicross_v4(df, fdf, bullish:tuple=(50, 100), bearish:tuple=(0, 50), minibullish:tuple=(50, 100), minibearish:tuple=(0, 50), reverse:bool=False):
    # print(df)    
    ichidiff = list(df['tenkiju'].iloc[-2:])
    rsi      = fdf['rsi'].iloc[-1]
    minirsi  = df['rsi'].iloc[-1]
    signal   = None
    if inrange(rsi, bullish) and (inrange(minirsi, minibullish)) and (ichidiff[1] >= 0) and (ichidiff[0] < 0):
        signal = 'short' if reverse else 'long'
    if inrange(rsi, bearish) and (inrange(minirsi, minibearish)) and (ichidiff[1] <= 0) and (ichidiff[0] > 0):
        signal = 'long' if reverse else 'short'
    ret = {}
    ret['signal']      = signal
    ret['ichidiff']    = ichidiff
    ret['rsi']         = rsi
    ret['minirsi']     = minirsi
    ret['entryPrice']  = df['close'].iloc[-1]
    return ret

def ichicross_v5(df, fdf, rsibullish:tuple=(50, 100), rsibearish:tuple=(0, 50), flag:int=0):
    n = 1
    # print(df)    
    ichidiff = list(df['tenkiju'].iloc[-2:])
    rsi      = fdf['rsi'].iloc[-1]
    signal   = None
    if inrange(rsi, rsibullish) and (ichidiff[1] >= 0) and (ichidiff[0] < 0) and (flag < n):
        signal = 'long'
    if inrange(rsi, rsibearish) and (ichidiff[1] <= 0) and (ichidiff[0] > 0) and (flag < n):
        signal = 'short'
    ret = {}
    ret['date']        = df['date'].iloc[-1]
    ret['signal']      = signal
    ichdiff_fixed      = []
    for item in ichidiff:
            ichdiff_fixed.append(float2fixed(item, 1000))
    ret['ichidiff']    = ichdiff_fixed
    ret['rsi']         = float2fixed(rsi, 100)
    ret['entryPrice']  = df['close'].iloc[-1]
    return ret

def ichicross_v3(df, fdf, rsibullish:tuple=(0, 100), rsibearish:tuple=(0, 100), ftfrsibullish:tuple=(0, 100), ftfrsibearish:tuple=(0, 100)):
    # print(df)    
    ichidiff         = list(df['tenkiju'].iloc[-2:])
    fdfichidiff      = fdf['tenkiju'].iloc[-1]
    signal = None
    rsi      = df['rsi'].iloc[-1]
    fdfrsi   = fdf['rsi'].iloc[-1]
    flag     = fdf['tenkansen'] > fdf['kijunsen']
    # if inrange(rsi, rsibullish) and (inrange(fdfrsi, ftfrsibullish)) and ((ichidiff[1] >= 0) and (ichidiff[0] < 0)) and (fdf['tenkansen'].iloc[-1] > fdf['kijunsen'].iloc[-1]):
    #     signal = 'long'
    # if inrange(rsi, rsibearish) and (inrange(fdfrsi, ftfrsibearish)) and ((ichidiff[1] <= 0) and (ichidiff[0] > 0)) and (fdf['tenkansen'].iloc[-1] < fdf['kijunsen'].iloc[-1]):
    #     signal = 'short'
    # if inrange(rsi, rsibullish) and (inrange(fdfrsi, ftfrsibullish)) and (df['tenkansen'].iloc[-1] > df['kijunsen'].iloc[-1]) and (fdf['tenkansen'].iloc[-1] > fdf['kijunsen'].iloc[-1]):
    #     signal = 'long'
    # if inrange(rsi, rsibearish) and (inrange(fdfrsi, ftfrsibearish)) and (df['tenkansen'].iloc[-1] < df['kijunsen'].iloc[-1]) and (fdf['tenkansen'].iloc[-1] < fdf['kijunsen'].iloc[-1]):
    #     signal = 'short'

    if inrange(rsi, rsibullish) and (inrange(fdfrsi, ftfrsibullish)) and (rsi<fdfrsi) and (df['tenkansen'].iloc[-1] > df['kijunsen'].iloc[-1]) and (fdf['tenkansen'].iloc[-1] > fdf['kijunsen'].iloc[-1]):
        signal = 'long'
    if inrange(rsi, rsibearish) and (inrange(fdfrsi, ftfrsibearish)) and (rsi>fdfrsi) and (df['tenkansen'].iloc[-1] < df['kijunsen'].iloc[-1]) and (fdf['tenkansen'].iloc[-1] < fdf['kijunsen'].iloc[-1]):
        signal = 'short'


    ret = {}
    ret['signal']      = signal
    ret['ichidiff']    = ichidiff
    ret['fdfrsi']      = fdfrsi
    ret['rsi']         = rsi    
    ret['entryPrice']  = df['close'].iloc[-1]
    return ret

def cancellation_v0(df, threshold, rsibounds):
    def inrange(a, rng):
        if a>rng[0] and a<rng[1]:
            return True
        return False
    signal = None
    price  = None
    sl     = None
    if df['rsi'].iloc[-3]<rsibounds[0] and df['rsi'].iloc[-2]>rsibounds[0]:
        if df['low'].iloc[-3]==df['t_period_low'].iloc[-2]:
            if df['abratio'].iloc[-3]<0 and df['abratio'].iloc[-2]>0:
                if df['close'].iloc[-2] > df['high'].iloc[-3]:
                    cancellation_ratio = df['abratio'].iloc[-2]/abs(df['abratio'].iloc[-3])
                    # print('long')
                    # print(cancellation_ratio)
                    if inrange(cancellation_ratio, threshold):
                        signal = 'long'
                        price  = df['close'].iloc[-2]
                        sl     = df['t_period_low'].iloc[-2]
    elif df['rsi'].iloc[-3]>rsibounds[1] and df['rsi'].iloc[-2]<rsibounds[1]:
        if df['high'].iloc[-3]==df['t_period_high'].iloc[-2]:
            if df['abratio'].iloc[-3]>0 and df['abratio'].iloc[-2]<0:
                if df['close'].iloc[-2] < df['low'].iloc[-3]:
                    cancellation_ratio = abs(df['abratio'].iloc[-2])/df['abratio'].iloc[-3]
                    # print('short')
                    # print(cancellation_ratio)
                    if inrange(cancellation_ratio, threshold):
                        signal = 'short'
                        price  = df['close'].iloc[-2]
                        sl     = df['t_period_high'].iloc[-2]
    
    ret = {}
    ret['signal']     = signal
    ret['entryPrice'] = price
    ret['sl']         = sl
    return ret

def ichimokubull(df, args:list=[]):
    ''' If price is above the Cloud formed by the Senkou Span A and B, 
    and it moves above Tenkansen (from below), that is a buy signal.'''

    if not df.__contains__('tenkansen') or not df.__contains__('kijunsen') or \
        not df.__contains__('senkou_a') or not df.__contains__('senkou_b'):
        Indicators.AddIndicator(df, indicator_name="ichimoku", col_name=None, args=None)
    i = 1
    if i - 1 > 0 and i < len(df):
        if df['senkou_a'][i] is not None and df['senkou_b'][i] is not None:
            if df['tenkansen'][i] is not None and df['tenkansen'][i-1] is not None:
                if df['close'][i-1] < df['tenkansen'][i-1] and \
                    df['close'][i] > df['tenkansen'][i] and \
                    df['close'][i] > df['senkou_a'][i] and \
                    df['close'][i] > df['senkou_b'][i]:
                    signal = 'long'
                    return signal
    return None

def rsidiff_v0(df, d):
    rsidiff2 = df['rsidiff'].iloc[-2]
    rsidiff1 = df['rsidiff'].iloc[-1]
    signal = None
    if (rsidiff2 > d[1]) and (df['high'].iloc[-1]<df['x_period_high'].iloc[-1]) and (rsidiff2>rsidiff1):
        signal = 'short'
    if (rsidiff2 < d[0]) and (df['low'].iloc[-1]>df['x_period_low'].iloc[-1]) and (rsidiff2<rsidiff1):
        signal = 'long'
    ret = {}
    ret['signal']      = signal
    ret['rsidiff']     = rsidiff2
    ret['entryPrice']  = df['close'].iloc[-1]
    return ret        

def tpslfixed(entryPrice, slperc, tpfactor, side):
    sgn    = 1 if side=='long' else -1
    tp     = entryPrice + sgn*tpfactor*(slperc/100)*entryPrice
    sl     = entryPrice - sgn*(slperc/100)*entryPrice
    return sl, tp


def tpslfromstrategy(entryPrice, sl, tpfactor, side):
    sgn    = 1 if side=='long' else -1
    slperc = 100*(entryPrice - sl)/sgn/entryPrice
    tp     = entryPrice + sgn*tpfactor*(slperc/100)*entryPrice
    return tp

def candletrailsl(df, side, lastsl):

    inftp  = float('inf')#1000000.0
    sgn    = 1 if side=='long' else -1
    if sgn > 0:
        newsl = df['x_period_low'].iloc[-1]
        if lastsl:
            if (newsl>lastsl) and (newsl<df['close'].iloc[-1]):
                return newsl, inftp
            else:
                return lastsl, inftp
        else:
            return newsl, inftp
    elif sgn < 0:
        newsl = df['x_period_high'].iloc[-1]
        if lastsl:
            if (newsl<lastsl) and (newsl>df['close'].iloc[-1]):
                return newsl, -inftp
            else:
                return lastsl, -inftp
        else:
            return newsl, -inftp

def kijunsensl(df, side, lastsl, offset):

    inftp  = float('inf')#1000000.0
    sgn    = 1 if side=='long' else -1
    if sgn > 0:
        newsl = df['kijunsen'].iloc[-1] - offset*df['kijunsen'].iloc[-1]
        if lastsl:
            if (newsl>lastsl) and (newsl<df['close'].iloc[-1]):
                return newsl, inftp
            else:
                return lastsl, inftp
        else:
            return newsl, inftp
    elif sgn < 0:
        newsl = df['kijunsen'].iloc[-1] + offset*df['kijunsen'].iloc[-1]
        if lastsl:
            if (newsl<lastsl) and (newsl>df['close'].iloc[-1]):
                return newsl, -inftp
            else:
                return lastsl, -inftp
        else:
            return newsl, -inftp

def kijunsensl_tpfixed(df, side, lastsl, tpperc, offset, entryPrice):

    sgn    = 1 if side=='long' else -1
    inftp  = entryPrice + sgn*(tpperc/100)*entryPrice
    if inftp<0:
        print(inftp)
    if sgn > 0:
        newsl = df['kijunsen'].iloc[-1] - offset*df['kijunsen'].iloc[-1]
        if lastsl:
            if (newsl>lastsl) and (newsl<df['close'].iloc[-1]):
                return newsl, inftp
            else:
                return lastsl, inftp
        else:
            return newsl, inftp
    elif sgn < 0:
        newsl = df['kijunsen'].iloc[-1] + offset*df['kijunsen'].iloc[-1]
        if lastsl:
            if (newsl<lastsl) and (newsl>df['close'].iloc[-1]):
                return newsl, inftp
            else:
                return lastsl, inftp
        else:
            return newsl, inftp



class Strategies:
    STRATEGIES_DICT = {}
    STRATEGIES_DICT["emaCross"]        = emaCross
    STRATEGIES_DICT["bollband"]        = bollband_v0
    STRATEGIES_DICT["ichimokubull"]    = ichimokubull
    STRATEGIES_DICT["ichicross_v0"]    = ichicross_v0
    STRATEGIES_DICT["ichicross_v1"]    = ichicross_v1
    STRATEGIES_DICT["ichicross_v2"]    = ichicross_v2
    STRATEGIES_DICT["ichicross_v3"]    = ichicross_v3
    STRATEGIES_DICT["cancellation_v0"] = cancellation_v0



    TPSL_DICT = {}
    TPSL_DICT['tpslfixed']          = tpslfixed
    TPSL_DICT['candletrailsl']      = candletrailsl

    @staticmethod
    def strategy(df, strategy_name, strategy_params:dict={}, fdf=None):

        try:
            if strategy_name == "ichicross_v0":
                reverse    = strategy_params['ifreverse']
                ret = ichicross_v0(df, reverse)
                return ret
            elif strategy_name == "ichicross_v1":
                rsibullish = strategy_params['rsibullish']
                rsibearish = strategy_params['rsibearish']
                reverse    = strategy_params['reverse']
                ret = ichicross_v1(df, rsibullish, rsibearish, reverse)
                return ret
            elif strategy_name == "ichicross_v2":
                rsibullish = strategy_params['ftf']['rsibullish']
                rsibearish = strategy_params['ftf']['rsibearish']
                ifreverse  = strategy_params['ifreverse']
                ret = ichicross_v2(df, fdf, rsibullish, rsibearish, ifreverse)
                return ret
            elif strategy_name == "ichicross_v3":
                bullish    = strategy_params['main']['rsibullish']
                bearish    = strategy_params['main']['rsibearish']
                ftfbullish = strategy_params['ftf']['rsibullish']
                ftfbearish = strategy_params['ftf']['rsibearish']
                ret = ichicross_v3(df, fdf, bullish, bearish, ftfbullish, ftfbearish)
                return ret
            elif strategy_name == "ichicross_v4":
                bullish     = strategy_params['bullish']
                bearish     = strategy_params['bearish']
                minibullish = strategy_params['minibullish']
                minibearish = strategy_params['minibearish']
                ifreverse   = strategy_params['ifreverse']
                ret = ichicross_v4(df, fdf, bullish, bearish, minibullish, minibearish, ifreverse)
                return ret
            elif strategy_name == "ichicross_v5":
                bullish     = strategy_params['bullish']
                bearish     = strategy_params['bearish']
                minibullish = strategy_params['minibullish']
                minibearish = strategy_params['minibearish']
                flag        = strategy_params['flag']
                ret = ichicross_v5(df, fdf, bullish, bearish, minibullish, minibearish, flag)
                return ret
            elif strategy_name == "cancellation_v0":
                threshold = strategy_params['threshold']
                rsibounds = strategy_params['rsibounds']
                ret     = cancellation_v0(df, threshold, rsibounds)
                return ret
            elif strategy_name == "bollband_v0":
                tipoutp = strategy_params['tipoutp']
                slfactor = strategy_params['slfactor']
                ret = bollband_v0(df, tipoutp, slfactor)
                return ret
            elif strategy_name == "rsidiff_v0":
                d   = strategy_params['main']['diff']
                ret = rsidiff_v0(df, d)
                return ret
            elif strategy_name == "emaCross":
                df = emaCross(df)
            elif strategy_name == "ichimokubull":
                df = Swingrabber(df)
            else:
                raise('Invalid Strategy!')

        except Exception as e:
            print(e)
            print("\nException raised when trying to compute " + strategy_name + " strategy")
            raise(e)

    @staticmethod
    def tpsl(df, pos, tpsl_name, tpsl_params:dict={}):

        try:
            if tpsl_name == "tpslfixed":
                slperc   = 0.4 if not 'slperc' in tpsl_params else tpsl_params['slperc']
                tpfactor = 2 if not 'tpfactor' in tpsl_params else tpsl_params['tpfactor']
                sl, tp   = tpslfixed(pos['entryPrice'], slperc, tpfactor, pos['signal'])
                return sl, tp
            elif tpsl_name == "tpslfromstrategy":
                sl       = pos['sl']
                tpfactor = 2 if not 'tpfactor' in tpsl_params else tpsl_params['tpfactor']
                tp   = tpslfromstrategy(pos['entryPrice'], sl, tpfactor, pos['signal'])
                return sl, tp
            elif tpsl_name == "candletrailsl":
                sl = None 
                if pos['sl']:
                    sl = pos['sl']
                sl, tp = candletrailsl(df, pos['signal'], sl)
                return sl, tp
            elif tpsl_name == "kijunsensl":
                offset   = 0 if not 'offset' in tpsl_params else tpsl_params['offset']
                sl = None 
                if pos['sl']:
                    sl = pos['sl']
                sl, tp = kijunsensl(df, pos['signal'], sl, offset)
                return sl, tp
            elif tpsl_name == "kijunsensl_tpfixed":
                offset   = 0 if not 'offset' in tpsl_params else tpsl_params['offset']
                tpperc   = 0.5 if not 'offset' in tpsl_params else tpsl_params['tpperc']
                sl = None 
                if pos['sl']:
                    sl = pos['sl']
                    tp = pos['tp']
                sl, tp = kijunsensl_tpfixed(df, pos['signal'], sl, tpperc, offset, pos['entryPrice'])
                return sl, tp
            else:
                raise('Invalid tpsl strategy!')

        except Exception as e:
            print(e)
            print("\nException raised when trying to compute " + tpsl_name)
            raise(e)

