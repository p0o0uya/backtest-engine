from pyti.smoothed_moving_average import smoothed_moving_average as sma
from pyti.exponential_moving_average import exponential_moving_average as ema0
from pyti.bollinger_bands import lower_bollinger_band as lbb
from pyti.bollinger_bands import upper_bollinger_band as ubb
import pandas as pd
import numpy as np
# Now, we're going to compute an indicator on our own (actually, a collection of indicators) called the ichimoku cloud...
# it contains 4 indicators: tenkan sen, kijun sen, senkou span a and senkou span b...
# I won't go in detail about what each of them means, but they are useful in certain strategies

def askbidratio(df):
    df['abratio'] = (df['close']-df['open'])/df['volume']
    return df

def ema(df, n_ema):
    # df['ema'] = ema0(df['close'].to_list(), n_ema)
    # print(df['ema'])
    # alpha0 = 2/(1+n_ema)
    # alpha1 = 1/(n_ema)
    df['ema'] = pd.Series.ewm(df['close'], span=n_ema, adjust=False).mean()
    # df['ema'] = pd.Series.ewm(df['close'], alpha=alpha0, adjust=False).mean()
    # df['ema'] = pd.Series.ewm(df['close'], alpha=alpha1, adjust=False).mean()
    return df

def rsi_raw(df, n, round_rsi:bool=True):
    # RSI = 100 - (100 / (1 + RS))
    # where RS = (Wilder-smoothed n-period average of gains / Wilder-smoothed n-period average of -losses)
    # Note that losses above should be positive values
    # Wilder-smoothing = ((previous smoothed avg * (n-1)) + current value to average) / n
    # delta          = df["close"].diff()
    delta          = df["open"].diff()
    up             = delta.copy()
    up[up < 0]     = 0
    up             = pd.Series.ewm(up, alpha=1/n).mean()
    down           = delta.copy()
    down[down > 0] = 0
    down          *= -1
    down           = pd.Series.ewm(down, alpha=1/n).mean()
    rs             = up / down
    rsi            = np.where(up == 0, 0, np.where(down == 0, 100, 100 - (100 / (1 + rs))))
    ret            = np.round(rsi, 2) if round_rsi else rsi
    return ret

def rsi(df, n, round_rsi:bool=True):
    rsi            = rsi_raw(df, n, round_rsi)
    df["rsi"]      = rsi
    return df

def fdfrsi(df, n, fdf):
    def inrange(a, rng):
        if a>=rng[0] and a<rng[1]:
            return True
        return False
    fdt = fdf['time'].iloc[-1] - fdf['time'].iloc[-2]
    dt  = df['time'].iloc[-1] - df['time'].iloc[-2]
    fdf       = rsi(fdf, n)
    fdfrsi    = []
    k = 0
    for item in df.iloc:
        itt   = item['time']
        while True:

            tmrng = (fdf['time'].iloc[k-1], fdf['time'].iloc[k-1]+fdt)
            # print(itt)
            # print(tmrng)
            if not inrange(itt, tmrng):
                k += 1
                continue
            break
        fdfrsi.append(fdf['rsi'].iloc[k-1])
    df['fdfrsi']   = fdfrsi
    return df

def rsi_diff(df, n1, n2):
    rsin1 = rsi_raw(df, n1)
    rsin2 = rsi_raw(df, n2)
    df['rsidiff'] = rsin1 - rsin2
    return df

def maximin(df, x):
    #(x-period hign and x-period low)
    df['x_period_high'] = df['high'].rolling(window=x).max()
    df['x_period_low']  = df['low'].rolling(window=x).min()
    return df

def stoch_rsi(df, k, d, n, sn):
    df['rsi']    = rsi_raw(df, n)
    stoch_high   = df['rsi'].rolling(window=sn).max()
    stoch_low    = df['rsi'].rolling(window=sn).min()
    stoch_rsi_K  = 100*(df['rsi'] - stoch_low)/(stoch_high - stoch_low)
    df['K']      = stoch_rsi_K.rolling(window=k).mean()
    df['D']      = df['K'].rolling(window=d).mean()
    return df

def ichi(df, x):
    #(x-period hign + x-period low)/2
    x_period_high = df['high'].rolling(window=x).max()
    x_period_low  = df['low'].rolling(window=x).min()
    return (x_period_high + x_period_low)/2

def tenkansen(df, t, k, s, d):
    # Tenkan-sen (Conversion Line): (9-period high + 9-period low)/2
    df['tenkansen'] = ichi(df, t)
    return df

def kijunsen(df, t:int=9, k:int=26, s:int=52, d:int=26):
    # Kijun-sen (Base Line): (26-period high + 26-period low)/2
    df['kijunsen'] = ichi(df, k)
    return df

def tenkiju(df, t:int=9, k:int=26, s:int=52, d:int=26):
    # Kijun-sen (Base Line): (26-period high + 26-period low)/2
    df['tenkansen'] = ichi(df, t)
    df['kijunsen']  = ichi(df, k)
    df['tenkiju']   = df['tenkansen']-df['kijunsen']
    return df

def fdftenkiju(df, t, k, s, d, fdf):
    def inrange(a, rng):
        if a>=rng[0] and a<rng[1]:
            return True
        return False
    fdt           = fdf['time'].iloc[-1] - fdf['time'].iloc[-2]
    dt            = df['time'].iloc[-1] - df['time'].iloc[-2]
    fdf           = tenkiju(fdf, t, k, s, d)
    fdftenkiju    = []
    k = 0
    for item in df.iloc:
        itt   = item['time']
        while True:
            tmrng = (fdf['time'].iloc[k], fdf['time'].iloc[k]+fdt)
            # print(itt)
            # print(tmrng)
            if not inrange(itt, tmrng):
                k += 1
                continue
            break
        fdftenkiju.append(fdf['tenkiju'].iloc[k])
    df['fdftenkiju']   = fdftenkiju
    return df


def senkou_a(df, t:int=9, k:int=26, s:int=52, d:int=26):
    # Senkou Span A (Leading Span A): (Conversion Line + Base Line)/2
    df['senkou_a'] = ((df['tenkansen'] + df['kijunsen'])/2).shift(d)
    return df

def senkou_b(df, t:int=9, k:int=26, s:int=52, d:int=26):
    # Senkou Span B (Leading Span B): (52-period high + 52-period low)/2
    df['senkou_b'] = (ichi(df, s)).shift(d)
    return df

def chikouspan(df, t:int=9, k:int=26, s:int=52, d:int=26):
    # Chikou Span: Most recent closing price, plotted d periods behind (optional)
    df['chikouspan'] = df['close'].shift(-d)
    return df

def swingFilter1(data, perc, cnt):
    data.sort()
    filtered = []
    for pj in range(len(data)):
        datp = data[pj]+perc*data[pj]
        datm = data[pj]-perc*data[pj]
        ct   = 0
        for item in data:
            if ((item > datm) and (item < datp)):
                ct += 1
        if ct > cnt:
            filtered.append(data[pj])
    return filtered

def swingFilter2(data, perc, cnt):
    data.sort()
    group    = []
    filtered = []
    gaper    = 0
    for pj in range(len(data)-1):
        gap   = (data[pj+1]-data[pj])
        gapc  = (data[pj+1]+data[pj])/2
        gaper = gap/gapc
        group.append(data[pj])
        if gaper > perc:
            gaper = 0
            filtered.append(group)
            group = []
    group.append(data[-1])
    filtered.append(group)
    newfilter = []
    for item in filtered:
        ave  = sum(item)/len(item)
        lnit = len(item)
        if (lnit>cnt):
            newfilter.append(ave)
    return newfilter

def Swingrabber(df, perc, cnt):
    lndf  = len(df)
    print(lndf)
    swing = []
    for pj in range(1, len(df)-1):
        if (df['low'][pj]==min([df['low'][pj-1], df['low'][pj], df['low'][pj+1]])):
            swing.append(df['low'][pj])
        if (df['high'][pj]==max([df['high'][pj-1], df['high'][pj], df['high'][pj+1]])):
            swing.append(df['high'][pj])
    print('number of swing points {}'.format(len(swing)))
    # swing = swingFilter1(swing, perc, cnt)
    swing = swingFilter2(swing, perc, cnt)
    data = [swing]*lndf
    df['swing'] = data
    # print(df)
    return df

def volume(df):
    scale    = 1
    df['volume'] = df['volume']/scale
    return df

# Now, we're going to write the function used to compute any indicator that we 
# want and add it to the dataframe. This is the function that will be called 
# from outside this class, when a TradingModel needs an indicator to be added 
# to it, in order to compute a strategy

class Indicators:

    INDICATORS_DICT = {}
    INDICATORS_DICT["sma"]         = sma
    INDICATORS_DICT["ema"]         = ema
    INDICATORS_DICT["lbb"]         = lbb
    INDICATORS_DICT["ubb"]         = ubb
    INDICATORS_DICT["tenkansen"]   = tenkansen
    INDICATORS_DICT["kijunsen"]    = kijunsen
    INDICATORS_DICT["tenkiju"]     = tenkiju
    INDICATORS_DICT["senkou_a"]    = senkou_a
    INDICATORS_DICT["senkou_b"]    = senkou_b
    INDICATORS_DICT["chikouspan"]  = chikouspan
    INDICATORS_DICT["swing"]       = Swingrabber
    INDICATORS_DICT["rsi"]         = rsi
    INDICATORS_DICT["volume"]      = volume
    INDICATORS_DICT["askbidratio"] = askbidratio
    INDICATORS_DICT["maximin"]     = maximin
    INDICATORS_DICT["rsi_diff"]    = rsi_diff



    @staticmethod
    def AddIndicator(df, indicator_name, indiparams:dict={}):
        # df is the dataframe to which we will add the indicator
        # indicator_name is the name of the indicator as found in the dict above
        # col_name is the name that the indicator will appear under in the dataframe
        # args are arguments that might be used when calling the indicator function
        try:
            if indicator_name == "tenkansen": 
                # this is a special case, because it will create more columns in the df
                t = 9 if not 't' in indiparams else indiparams['t']
                k = 26 if not 'k' in indiparams else indiparams['k']
                s = 52 if not 's' in indiparams else indiparams['s']
                d = 26 if not 'd' in indiparams else indiparams['d']
                df = tenkansen(df, t, k, s, d)
            elif indicator_name == "kijunsen":
                t = 9 if not 't' in indiparams else indiparams['t']
                k = 26 if not 'k' in indiparams else indiparams['k']
                s = 52 if not 's' in indiparams else indiparams['s']
                d = 26 if not 'd' in indiparams else indiparams['d']
                df = kijunsen(df, t, k, s, d)
            elif indicator_name == "tenkiju":
                t = 9 if not 't' in indiparams else indiparams['t']
                k = 26 if not 'k' in indiparams else indiparams['k']
                s = 52 if not 's' in indiparams else indiparams['s']
                d = 26 if not 'd' in indiparams else indiparams['d']
                df = tenkiju(df, t, k, s, d)
            elif indicator_name == "fdftenkiju":
                t = 9 if not 't' in indiparams else indiparams['t']
                k = 26 if not 'k' in indiparams else indiparams['k']
                s = 52 if not 's' in indiparams else indiparams['s']
                d = 26 if not 'd' in indiparams else indiparams['d']
                df = fdftenkiju(df, t, k, s, d, fdf)
            elif indicator_name == "swing":
                df = Swingrabber(df, perc, cnt)
            elif indicator_name == "volume":
                df = volume(df)
            elif indicator_name == "rsi":
                n = 14 if not 'n' in indiparams else indiparams['n']
                df = rsi(df, n)
            elif indicator_name == "rsidiff":
                n1 = 14 if not 'n1' in indiparams else indiparams['n1']
                n2 = 28 if not 'n2' in indiparams else indiparams['n2']
                df = rsi_diff(df, n1, n2)
            elif indicator_name == "stoch_rsi":
                k  = 3  if not 'k'  in indiparams else indiparams['k']
                d  = 3  if not 'd'  in indiparams else indiparams['d']
                n  = 14 if not 'n'  in indiparams else indiparams['n']
                sn = 14 if not 'sn' in indiparams else indiparams['sn']
                df = stoch_rsi(df, k, d, n, sn)
            elif indicator_name == "ema":
                n_ema = 21 if not 'n_ema' in indiparams else indiparams['n_ema']
                df = ema(df, n_ema)
            elif indicator_name == "fdfrsi":
                n = 14 if not 'n' in indiparams else indiparams['n']
                df = fdfrsi(df, n)
            elif indicator_name == "maximin":
                x = 9 if not 'x' in indiparams else indiparams['x']
                df = maximin(df, x)
            elif indicator_name == "askbidratio":
                df = askbidratio(df)
            elif indicator_name == "ubb":
                t = 20 if not 't' in indiparams else indiparams['t']
                upper_boll = ubb(df['close'], t)
                df['ubb']  = upper_boll

            elif indicator_name == "lbb":
                t = 20 if not 't' in indiparams else indiparams['t']
                lower_boll = lbb(df['close'], t)
                df['lbb']  = lower_boll
            else:
                print('invalid indicator!')
        except Exception as e:
            print("\nException raised when trying to compute " + indicator_name + " indicator")
            print(e)
            raise(e)

    @staticmethod
    def AddIndicators(df, indicator_list, indiparams:dict={}):
        for item in indicator_list:
            Indicators.AddIndicator(df, item, indiparams)

