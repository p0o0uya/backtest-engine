#!/usr/bin/python3 -u
from telapi import *
# from sqshell import *
from binance import *
from Indicators import Indicators
from xenon_params import params
import time                                 # importing the time library
from datetime import datetime, timedelta
# from string import ascii_lowercase, ascii_uppercase, digits
import secrets as sc
import hashlib
import csv
import os

class xenon_trader(params):

    STATUS_LIST           = ('initializing', 'awaiting_signals', 'placing_orders', 'handling_open_positions')
    STATUS                = STATUS_LIST[0]
    SIGNAL                = None
    PRICE                 = None
    SL                    = None
    SLORDERID             = None

    def __init__(self):
        print('Initializing the class for XENON TRADER!')
        self.telapi     = telapi()
        # self.sqshell    = sqshell()
        self.exchange   = binance(filename = '/etc/xenontrader/keys.txt')
        self.df         = self.exchange.GetSymbolKlines(    self.TRADING_SYMBOL,
                                                            self.TRADING_TIMEFRAME, 
                                                            self.TRADING_WINDOW        )
        if self.STATUS  == 'initializing':
            try:
                params        = {   'symbol':   self.TRADING_SYMBOL,
                                    'leverage': self.LEVERAGE           }
                self.exchange.setleverage(params)
                self.cancelallorders()
                self.closeposition()
                data1         = self.exchange.GetAccountData()
                balancestr    = data1['availableBalance']
                self.BALANCE  = float2fixed(float(balancestr), 1000)
                self.STATUS   = self.STATUS_LIST[1]
                txt           = self.MSG[6].format(self.BALANCE, self.STRATEGY_NAME)
                self.send_api_msg(txt)

            except Exception as Err:
                self.STATUS = 'connection_failed'
                raise(Err)

    def validating_signals(self, signal, price):

        if signal == 'long':
            check = 'low'
            sgn   = 1
            sl    = min(list(self.df[check].iloc[-(self.TRAILING_LAG+1):-1]))
        else:
            check = 'high'
            sgn   = -1
            sl    =  max(list(self.df[check].iloc[-(self.TRAILING_LAG+1):-1]))

        slpercent = (sgn*(sl - price)/price) * self.LEVERAGE * 100
        sllockH   = sgn*self.MAX_DRAW_PER_TARDE/(self.LEVERAGE*100)*price + price
        sllockL   = sgn*self.MIN_DRAW_PER_TARDE/(self.LEVERAGE*100)*price + price
        if (slpercent < self.MAX_DRAW_PER_TARDE):
            sl   = float2fixed(sllockH, 100)
            return sl, slpercent, self.MAX_DRAW_PER_TARDE
        elif (slpercent > self.MIN_DRAW_PER_TARDE):
            sl   = float2fixed(sllockL, 100)
            return sl, slpercent, self.MIN_DRAW_PER_TARDE
        else:
            return sl, slpercent, 'Not Given'

    def awaiting_signals_cross(self):
        print('awaiting cross signals!')
        while True:
            self.df = self.exchange.GetSymbolKlines(        self.TRADING_SYMBOL,
                                                            self.TRADING_TIMEFRAME, 
                                                            self.TRADING_WINDOW        )

            Indicators.AddIndicator(self.df, indicator_name="tenkiju")
            signal, ichidiff = crossdetector(self.df)
            price  = self.df['close'].iloc[-1]
            # signal = 'long'
            if signal:
                txt0    = self.MSG[0].format(self.TRADING_SYMBOL, self.WORDS[signal], price,  self.df['date'].iloc[-1])
                sl, slpercent, stoplock = self.validating_signals(signal, price)
                txt1    = self.MSG[1].format(slpercent, stoplock)
                self.send_api_msg(txt0+txt1)
                self.STATUS = self.STATUS_LIST[2]
                self.SIGNAL = signal
                self.PRICE  = price
                self.SL     = sl
                print(self.df)

                break
            else:
                time.sleep(1)
                # print('pending next candle...')
                # pending_next_candle(self.INTERVAL_DETAIL[self.TRADING_TIMEFRAME]['tf_reference'])
        return signal, price, sl

    def awaiting_signals_swing(self):
        print('awaiting swing signals!')
        while True:
            self.df = self.exchange.GetSymbolKlines(        self.TRADING_SYMBOL,
                                                            self.TRADING_TIMEFRAME, 
                                                            4        )

            signal, sl, isvalid, slpercent = swingdetector(self.df, self.LEVERAGE, self.MAX_DRAW_PER_TARDE, self.MIN_DRAW_PER_TARDE)
            price  = self.df['close'].iloc[-2]
            # signal = 'long'
            if signal:
                txt0    = self.MSG[7].format(self.TRADING_SYMBOL, self.WORDS[signal], price,  self.df['date'].iloc[-2])
                txt1    = self.MSG[8].format(self.ISVALID[isvalid], slpercent, self.MAX_DRAW_PER_TARDE, self.MIN_DRAW_PER_TARDE)
                print(txt0+txt1)
                if isvalid:
                    self.STATUS = self.STATUS_LIST[2]
                    self.SIGNAL = signal
                    self.PRICE  = price
                    self.SL     = sl
                    print(self.df)
                    self.send_api_msg(txt0+txt1)
                    break
            else:
                time.sleep(0.1)
                # print('pending next candle...')
                # pending_next_candle(self.INTERVAL_DETAIL[self.TRADING_TIMEFRAME]['tf_reference'])
        return signal, price, sl

    def awaiting_signals_vol(self):
        print('awaiting vol signals!')
        while True:
            self.df = self.exchange.GetSymbolKlines(    self.TRADING_SYMBOL,
                                                        self.TRADING_TIMEFRAME, 
                                                        4                          )
            # self.df['volume'].iloc[-2] = 6000
            signal, entryPrice, tp, sl, vol = voldetector(self.df, self.LEVERAGE, sllockfactor=self.sllockfactor, tpp=self.TPP, t=self.t)
            price  = self.df['close'].iloc[-2]
            if signal:
                print(vol)
                txt0    = self.MSG[0].format(self.STRATEGY_NAME, self.TRADING_SYMBOL, self.WORDS[signal], price,  self.df['date'].iloc[-2])
                txt1    = self.MSG[7].format(tp)
                print(txt0+txt1)
                self.STATUS = self.STATUS_LIST[2]
                self.SIGNAL = signal
                self.PRICE  = price
                self.TP     = float2fixed(tp, self.PRICE_PRECISION[self.TRADING_SYMBOL])
                self.SL     = float2fixed(sl, self.PRICE_PRECISION[self.TRADING_SYMBOL])
                self.send_api_msg(txt0+txt1)
                break
            else:
                time.sleep(0.1)
        return signal, entryPrice, tp

    def place_sl_order(self):
        params = {}
        params['symbol']      = self.TRADING_SYMBOL
        params['side']        = self.SIDER[-self.SIDE]
        params['quantity']    = self.QUANTITY
        params['type']        = 'STOP_MARKET'
        params['stopPrice']   = self.SL
        params['reduceOnly']  = True
        print(params)
        order = self.exchange.PlaceOrder(params, test=False)
        return order

    def place_tp_order(self):
        params = {}
        params['symbol']      = self.TRADING_SYMBOL
        params['side']        = self.SIDER[-self.SIDE]
        params['quantity']    = self.QUANTITY
        # params['type']        = 'TAKE_PROFIT_MARKET'
        params['stopPrice']   = self.TP
        params['type']        = 'TAKE_PROFIT'
        params['price']       = self.TP
        params['reduceOnly']  = True
        params['timeInForce'] = 'GTC'
        order = self.exchange.PlaceOrder(params, test=False)
        return order

    def calculating_quantity(self):
        print('calculating quantity!')
        balance        = self.BALANCE
        levdbal        = balance*self.LEVERAGE
        levdbal        = levdbal*self.LOT
        lastprice      = self.df['close'].iloc[-1]
        self.QUANTITY  = float2fixed(levdbal/lastprice, self.QUANTITY_PRECISION[self.TRADING_SYMBOL])
        self.SIDE      = 1 if (self.SIGNAL=='long') else -1

    def placing_orders_tp_sl(self):
        print('placing tp/sl orders!')
        self.calculating_quantity()
        price = self.df['close'].iloc[-2]
        # Placing Stop loss order first as reduce only:
        slorder = self.place_sl_order()
        print(slorder)
        if not slorder.keys().__contains__('orderId'):
            print('stop order failed to be placed!')
            errormsg = slorder['msg']
            txt      = self.MSG[4].format(errormsg)
            self.send_api_msg(txt)
            print(slorder)
            return False
        
        self.SLORDERID = slorder['orderId']
        # Placing take profit order first as reduce only:
        tporder = self.place_tp_order()
        print(tporder)
        if not tporder.keys().__contains__('orderId'):
            print('take profit order failed to be placed!')
            errormsg = tporder['msg']
            txt      = self.MSG[4].format(errormsg)
            self.send_api_msg(txt)
            print(tporder)
            return False

        self.TPORDERID = tporder['orderId']
        # # Placing market order to open position:
        # params = {}
        # params['symbol']      = self.TRADING_SYMBOL
        # params['side']        = self.SIDER[self.SIDE]
        # params['quantity']    = self.QUANTITY
        # maorder = self.exchange.PlaceOrder(params, test=False)
        # if not maorder.keys().__contains__('orderId'):
        #     print('market order failed to be placed!')
        #     errormsg = maorder['msg']
        #     txt      = self.MSG[4].format(errormsg)
        #     self.send_api_msg(txt)
        #     print(maorder)
        #     return False

        # Placing Limit order to open position:
        params = {}
        params['symbol']      = self.TRADING_SYMBOL
        params['side']        = self.SIDER[self.SIDE]
        params['quantity']    = self.QUANTITY
        params['type']        = 'LIMIT'
        params['price']       = price
        params['timeInForce'] = 'GTC'
        liorder = self.exchange.PlaceOrder(params, test=False)
        if not liorder.keys().__contains__('orderId'):
            print('market order failed to be placed!')
            errormsg = liorder['msg']
            txt      = self.MSG[4].format(errormsg)
            self.send_api_msg(txt)
            print(maorder)
            return False

        time.sleep(60)
        params   = {'symbol': self.TRADING_SYMBOL, 'orderId': liorder['orderId']}
        position = self.exchange.GetOrderInfo(params)
        if not position['status']=='FILLED':
            errormsg = 'limit order failed to be filled!'
            print(errormsg)
            txt      = self.MSG[4].format(errormsg)
            self.send_api_msg(txt)
            print(position)
            return False
        
        avgprice = position['avgPrice']
        txt      = self.MSG[2].format(self.TRADING_SYMBOL, self.QUANTITY, avgprice, self.SL, self.BALANCE, time.time())
        self.send_api_msg(txt)      
        return True


    def placing_orders(self):
        print('placing orders!')
        self.calculating_quantity()
        # Placing Stop loss order first as reduce only:
        slorder = self.place_sl_order()
        print(slorder)
        if not slorder.keys().__contains__('orderId'):
            print('stop order failed to be placed!')
            errormsg = slorder['msg']
            txt      = self.MSG[4].format(errormsg)
            self.send_api_msg(txt)
            print(slorder)
            return False

        self.SLORDERID = slorder['orderId']

        # Placing market order to open position:
        params = {}
        params['symbol']      = self.TRADING_SYMBOL
        params['side']        = self.SIDER[self.SIDE]
        params['quantity']    = self.QUANTITY
        maorder = self.exchange.PlaceOrder(params, test=False)
        if not maorder.keys().__contains__('orderId'):
            print('market order failed to be placed!')
            errormsg = maorder['msg']
            txt      = self.MSG[4].format(errormsg)
            self.send_api_msg(txt)
            print(maorder)
            params   = {'symbol': self.TRADING_SYMBOL, 'orderId': slorder['orderId']}
            self.exchange.CancelOrder(params)
            return False

        time.sleep(0.2)
        params   = {'symbol': self.TRADING_SYMBOL, 'orderId': maorder['orderId']}
        position = self.exchange.GetOrderInfo(params)
        if not position['status']=='FILLED':
            print('market order failed to be filled!')
            errormsg = 'market order failed to be filled!'
            txt      = self.MSG[4].format(errormsg)
            self.send_api_msg(txt)
            print(position)
            params   = {'symbol': self.TRADING_SYMBOL, 'orderId': slorder['orderId']}
            self.exchange.CancelOrder(params)
            params   = {'symbol': self.TRADING_SYMBOL, 'orderId': maorder['orderId']}
            self.exchange.CancelOrder(params)
            return False
        
        avgprice = position['avgPrice']
        txt      = self.MSG[2].format(self.TRADING_SYMBOL, self.QUANTITY, avgprice, self.SL, balance, time.time())
        self.send_api_msg(txt)      
        return True

    def handling_open_positions(self):
        print('handling open positions')
        
        while True:
            # print('pending next candle...')
            # pending_next_candle(self.INTERVAL_DETAIL[self.TRADING_TIMEFRAME]['tf_reference'])
            oldslparams = {'symbol': self.TRADING_SYMBOL, 'orderId': self.SLORDERID}
            oldslorder  = self.exchange.GetOrderInfo(oldslparams.copy())
            print(oldslorder)
            if oldslorder:
                if oldslorder['status']=='NEW':
                    # print('here we have to upgrade the SL')
                    self.df         = self.exchange.GetSymbolKlines(    self.TRADING_SYMBOL,
                                                                        self.TRADING_TIMEFRAME, 
                                                                        self.TRADING_WINDOW        )
                    oldsl      = self.SL
                    signal     = self.SIGNAL
                    newsl      = self.df[self.CHECK[signal]].iloc[-(self.TRAILING_LAG+1)]
                    closenow   = self.df['close'].iloc[-1]
                    
                    if self.SGN[signal]*(newsl - oldsl) > 0:
                        if self.SGN[signal]*(newsl - closenow) < 0:
                            print('updating stop loss')
                            print(oldsl)
                            print(signal)
                            print(newsl)
                            print(closenow)

                            self.SL      = newsl
                            newslorder   = self.place_sl_order()
                            print(newslorder)
                            if newslorder.keys().__contains__('orderId'):
                                print('canceling old sl ')
                                print(oldslparams)
                                print(self.SLORDERID)
                                cancel         = self.exchange.CancelOrder(oldslparams.copy())
                                print(cancel)
                                self.SLORDERID = newslorder['orderId']
                                print(self.SLORDERID)
                            else:
                                print('failed to place new sl order!')
                                errormsg = newslorder['msg']
                                txt      = self.MSG[4].format(errormsg)
                                self.send_api_msg(txt)
                            continue
                else:
                    print('position may have concluded!')
                    oldbalance    = self.BALANCE
                    data1         = self.exchange.GetAccountData()  # To make sure balance is update before issuing signal
                    balancestr    = data1['availableBalance'] 
                    self.BALANCE  = float2fixed(float(balancestr), 1000)
                    avgprice      = oldslorder['avgPrice']
                    PNL           = float2fixed(self.BALANCE-oldbalance, 1000)
                    ROE           = float2fixed(PNL/oldbalance*100, 1000) 
                    ifhappy       = 1 if PNL>0 else -1
                    txt           = self.MSG[3].format(self.TRADING_SYMBOL, avgprice, PNL, ROE, self.CONCL[ifhappy], self.BALANCE, time.time())
                    self.send_api_msg(txt)
                    self.STATUS = self.STATUS_LIST[1]
                    break
        return 

    def handling_open_positions_tp_sl(self):
        print('handling open positions in a candle with tp/sl')
        
        print('pending next candle...')
        pending_next_candle(self.INTERVAL_DETAIL[self.TRADING_TIMEFRAME]['tf_reference'])
        self.cancelallorders()
        self.closeposition()
        print('position concluded!')
        oldbalance    = self.BALANCE
        data1         = self.exchange.GetAccountData()  # To make sure balance is update before issuing signal
        balancestr    = data1['availableBalance'] 
        self.BALANCE  = float2fixed(float(balancestr), 1000)
        PNL           = float2fixed(self.BALANCE-oldbalance, 1000)
        ROE           = float2fixed(PNL/oldbalance*100, 1000) 
        ifhappy       = 1 if PNL>0 else -1
        txt           = self.MSG[3].format(self.TRADING_SYMBOL, None, PNL, ROE, self.CONCL[ifhappy], self.BALANCE, time.time())
        self.send_api_msg(txt)
        self.STATUS = self.STATUS_LIST[1]
        return

    def send_api_msg(self, txt):
        for chid in self.CHID:
            ret = self.telapi.sendmessage(chid, txt, None)
        return ret
    
    def cancelallorders(self):
        params = {'symbol': self.TRADING_SYMBOL}
        orders = self.exchange.GetAllOrderInfo(params, status='NEW')
        if orders:
            for item in orders:
                self.exchange.CancelOrder({'symbol': self.TRADING_SYMBOL, 'orderId': item['orderId']})
    
    def closeposition(self):
        position      = self.exchange.GetPositionData(self.TRADING_SYMBOL)[0]
        print(position)        
        if not (position['positionAmt']=='0.000'):
            posamt_signed  = position['positionAmt']
            posamt         = str(abs(float(posamt_signed)))
            entryPrice     = position['entryPrice']
            liqPrice       = position['liquidationPrice']
            side           = whichside(entryPrice, liqPrice)
            params = {}
            params['symbol']      = self.TRADING_SYMBOL
            params['side']        = 'BUY' if side=='SELL' else 'SELL'
            params['quantity']    = posamt
            params['type']        = 'MARKET'
            params['reduceOnly']  = True
            order = self.exchange.PlaceOrder(params, test=False)
            print(order)

def crossdetector(df):
    ichidiff = list(df.iloc[-2:]['tenkiju'])
    signal = None
    print(ichidiff)
    if (ichidiff[1] >= 0) and (ichidiff[0] < 0):
        signal = 'long'
    if (ichidiff[1] <= 0) and (ichidiff[0] > 0):
        signal = 'short'
    return signal, ichidiff

def voldetector(df, leverage, tpp:float=0.021, sllockfactor:int=5, t:float=[5500, 30000]):
    signal     = None
    tp         = None
    sl         = None
    vol        = df['volume'].iloc[-2]
    entryPrice = df['close'].iloc[-2]
    side       = 'long' if entryPrice<df['open'].iloc[-2] else 'short'
    sgn        = 1 if side=='long' else -1
    if vol>t[0] and vol<t[1]:
        signal = side
        tp     = entryPrice + sgn*tpp*entryPrice/leverage
        sl     = entryPrice - sgn*sllockfactor*tpp*entryPrice/leverage
    return signal, entryPrice, tp, sl, vol

def swingdetector(df, leverage, mxdraw, mndraw):
    signal    = None
    sl        = None
    isvalid   = False
    slpercent = 0
    pj        = -2
    if (df['low'].iloc[pj-1] == min((df['low'].iloc[pj], df['low'].iloc[pj-1], df['low'].iloc[pj-2]))):
        if (df['close'].iloc[pj-1] == min((df['close'].iloc[pj], df['close'].iloc[pj-1], df['close'].iloc[pj-2]))):
            if (df['high'].iloc[pj] == max((df['high'].iloc[pj], df['high'].iloc[pj-1], df['high'].iloc[pj-2]))):
                signal = 'long'

    elif (df['high'].iloc[pj-1] == max((df['high'].iloc[pj], df['high'].iloc[pj-1], df['high'].iloc[pj-2]))):
        if (df['close'].iloc[pj-1] == max((df['close'].iloc[pj], df['close'].iloc[pj-1], df['close'].iloc[pj-2]))):
            if (df['low'].iloc[pj] == min((df['low'].iloc[pj], df['low'].iloc[pj-1], df['low'].iloc[pj-2]))):
                signal = 'short'

    if not signal:
        return signal, sl, isvalid, slpercent

    if signal == 'long':
        check = 'low'
        sgn   = 1
    else:
        check = 'high'
        sgn   = -1

    sl      = df[check].iloc[pj-1]
    price   = df['close'].iloc[pj-1]
    slpercent = (sgn*(sl - price)/price)*leverage*100

    if (slpercent > mxdraw) and (slpercent < mndraw):
        isvalid = True
        return signal, sl, isvalid, slpercent
    else:
        return signal, sl, isvalid, slpercent

def pending_next_candle(divisable):
    # eps  = 1000000000
    eps  = 0
    now  = time.time_ns()
    next = now + divisable - now%divisable + eps
    while True:
        if time.time_ns() > next:
            return None

def whichside(entryPrice, liqPrice):
    if liqPrice > entryPrice:
        return 'SELL'
    else:
        return 'BUY'

def float2fixed(flt, prec):
    return int(flt * prec)/prec

def main():
    print('starting main loop!')
    inst = xenon_trader()
    if not inst.STATUS in inst.STATUS_LIST:
        raise('Error: Invalid System Status')
    while True:
        print('looping!!!')
        time.sleep(1)
        if inst.STATUS == 'awaiting_signals':
            if inst.STRATEGY_NAME=='Cross':
                signal = inst.awaiting_signals_cross()
            elif inst.STRATEGY_NAME=='Swing':
                signal = inst.awaiting_signals_swing()
            elif inst.STRATEGY_NAME=='Vol':
                signal = inst.awaiting_signals_vol()
            else:
                raise('invalid strategy name')
        if inst.STATUS == 'placing_orders':
            if inst.STRATEGY_NAME=='Cross':
                situation = inst.placing_orders()
                if situation:
                    inst.STATUS = inst.STATUS_LIST[3]
                else:
                    inst.STATUS = inst.STATUS_LIST[1]
            elif inst.STRATEGY_NAME=='Swing':
                situation = inst.placing_orders()
                if situation:
                    inst.STATUS = inst.STATUS_LIST[3]
                else:
                    inst.STATUS = inst.STATUS_LIST[1]
            elif inst.STRATEGY_NAME=='Vol':
                situation = inst.placing_orders_tp_sl()
                if not situation:
                    inst.STATUS = inst.STATUS_LIST[1]
                    inst.cancelallorders()
                else:
                    inst.STATUS = inst.STATUS_LIST[3]
            else:
                raise('invalid strategy name')

        if inst.STATUS == 'handling_open_positions':
            if inst.STRATEGY_NAME=='Cross':
                signal = inst.handling_open_positions()
            elif inst.STRATEGY_NAME=='Swing':
                signal = inst.handling_open_positions()
            elif inst.STRATEGY_NAME=='Vol':
                signal = inst.handling_open_positions_tp_sl()
            else:
                raise('invalid strategy name')
            

if __name__ == "__main__":
    main()
