from string import ascii_lowercase, ascii_uppercase, digits

class params():

    
#####################################################################################################
# GLOBAL PARAMETERS
#####################################################################################################

    TRADING_SYMBOL     = 'BTCUSDT'
    TRADING_TIMEFRAME  = '5m'
    STARTING_CAPITAL   = 100
    MAX_DRAW_PER_TARDE = -6
    MIN_DRAW_PER_TARDE = -0.8
    MAX_DRAW_SHUTDOWN  = -20

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
    PRICE_PRECISION['BTCUSDT'] = 100
    PRICE_PRECISION['ETHUSDT'] = 1000

    QUANTITY_PRECISION = {}
    QUANTITY_PRECISION['BTCUSDT'] = 1000
    QUANTITY_PRECISION['ETHUSDT'] = 1000

#####################################################################################################
# STRATEGY PARAMETERS
#####################################################################################################

    ICHIMOKOU          = {'t': 9, 'k': 26} # 's': 52, 'd':26}
    TRADING_WINDOW     = max(list(ICHIMOKOU.values()))+1
    TRAILING_LAG       = 1 + 1
    LEVERAGE           = 10
    LOT                = 0.95            # 0 to 95 % of the available funds
    STRATEGY_NAME      = 'Vol'         # ('Cross', 'Swing', 'Vol')
    TPP                = 0.021
    t                  = [5500, 30000]
    sllockfactor       = 0.5

#####################################################################################################
# TELAPI PARAMETERS
#####################################################################################################
    MSG                 = []
    MSG.append('=================\n{} Detected!\nsymbol: {} \nposition: {}\nprice: {}\ndatetime: {}\n=================\n')
    MSG.append('Signal is issued \nexpected stop loss: {:.2f} %\nreplaced by stop lock: {}\n=================')
    MSG.append('=================\nPosition Opened!\nsymbol: {} \nvolume: {}\navg price: {}\nSL: {}\nbalance: {} USDT\ntime index: {}\n=================\n')
    MSG.append('=================\nPosition Concluded!\nsymbol: {} \navg price: {}\nPNL(ROE %): {} ({}) {}\nconc. bal.: {} USDT\ntime index: {}\n=================\n')
    MSG.append('❌=================\nOrder Failed to be placed or filled. The error message is: {}❌')
    MSG.append('❌=================\nSL order failed to be upgraded. The error message is: {}❌')
    MSG.append('🌀🌀🌀...XENON_TRADER Engine is Initializing and going live with a capital of {} USDT...\nStrategy: {}\n🌀🌀🌀' )
    MSG.append('Signal is issued \nexpected take profit: {:.2f} %\n=================')
    MSG.append('Signal is {} \nbecause expected maximum loss: {:.2f} %\nshould be in range[{}, {}]\n=================')
    
    
    CHID                = []
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
