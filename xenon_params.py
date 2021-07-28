from string import ascii_lowercase, ascii_uppercase, digits

class params():

    
#####################################################################################################
# GLOBAL PARAMETERS
#####################################################################################################

    TRADING_SYMBOL     = 'BTCUSDT'
    TRADING_TIMEFRAME  = '1m'
    ideling_sleep      = 2*60
    FATHER_TIMEFRAME   = '1h'
    STARTING_CAPITAL   = 100
    MAX_DRAW_SHUTDOWN  = -95
    CAPITAL            = 12 #USDT
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

    PRICE_PRECISION = {}
    PRICE_PRECISION['BTCUSDT']    = 100
    PRICE_PRECISION['ETHUSDT']    = 1000

    QUANTITY_PRECISION = {}
    QUANTITY_PRECISION['BTCUSDT'] = 1000
    QUANTITY_PRECISION['ETHUSDT'] = 1000

#####################################################################################################
# STRATEGY PARAMETERS
#####################################################################################################

    STRATEGY_PARAMS               = {}
    STRATEGY_PARAMS['t']          = 9
    STRATEGY_PARAMS['k']          = 26
    STRATEGY_PARAMS['s']          = 52
    STRATEGY_PARAMS['d']          = 26
    STRATEGY_PARAMS['n']          = 14
    STRATEGY_PARAMS['ftf']        = FATHER_TIMEFRAME
    STRATEGY_PARAMS['rsibullish'] = (65, 100)
    STRATEGY_PARAMS['rsibearish'] = (0, 35)
    STRATEGY_PARAMS['name']       = 'ichicross_v2'   #('ichicross_v2', 'Swing', 'Vol')

    TPSL_PARAMS             = {}
    TPSL_PARAMS['slperc']   = 0.5
    TPSL_PARAMS['tpfactor'] = 3
    TPSL_PARAMS['name']     = 'tpslfixed'

    TRADING_WINDOW      = 53
    TRADING_WINDOW_FTF  = 1000

    LEVERAGE            = 30
    LOT                 = 0.95          # 0 to 0.95 of the available balance
    FIXED               = True
    FIXED_LOT           = 8.5

    W84FILLING          = 60*1*4

    indicatorsList      = ['tenkiju']
    ftf_indicatorsList  = ['rsi'] #indicators to be used in the father timeframe

#####################################################################################################
# TELAPI PARAMETERS
#####################################################################################################
    MSG    = {}
    MSG[0] = '=================\n{} Detected!rsi:{}\nichidiff: {}\n\nsymbol: {} \nside: {}\nprice: {}\ndatetime: {}\n=================\n'
    MSG[1] = '=================\nPosition Opened!\nsymbol: {} \nvolume: {}\navg price: {}\nSL: {}\nTP: {}\nbalance: {} USDT\ntime index: {}\n=================\n'
    MSG[2] = '=================\nPosition Concluded!\nsymbol: {} \navg price: {}\nPNL(ROE %): {} ({}) {}\nconc. bal.: {} USDT\ntime index: {}\n=================\n'
    MSG[3] = '❌=================\nOrder Failed to be placed or filled. The error message is: {}❌'
    MSG[4] = '🌀🌀🌀...XENON_TRADER Engine is Initializing and going live...\nCapital: {} USDT\nLeverage: {}\nStrategy: {}\nTimeframes: {}, {}\n🌀🌀🌀'
    MSG[5] = 'Balance is below max drawdown!'
    MSG[6] = '❌❌❌Limit order failed to be filled. Position did not start.❌❌❌'
    CHID   = []
    CHID.append(-1001440485279)

#####################################################################################################
    WORDS                 = {}

    WORDS['long']         = 'long 🚀'                     #0
    WORDS['short']        = 'short 🔻'                    #1

    ISVALID               = {True: 'issued ✅', False: 'not issued ❌'}

    SIDER                 = {1:'BUY', -1:'SELL'}
    CONCL                 = {1:'❇️💚', -1:'🔻💔'}
    CHECK                 = {'long': 'low', 'short': 'high'}
    SGN                   = {'long': 1, 'short': -1}


if __name__ == "__main__":
    inst = params()
    print(inst.TRADING_WINDOW)
