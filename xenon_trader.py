#!/usr/bin/python3 -u
from telapi import *
# from sqshell import *
from binance import *
from Indicators import Indicators
from Strategies import Strategies
from xenon_params import params
import time                                 # importing the time library
from datetime import datetime, timedelta
# from string import ascii_lowercase, ascii_uppercase, digits
import secrets as sc
import hashlib
import csv
import os

class xenon_trader(params):

    STATUS_LIST           = ('initializing', 'awaiting_signals', 'placing_orders', 'handling_open_positions', 'idleing')
    STATUS                = STATUS_LIST[0]
    SIGNAL                = None
    lastPrice             = None
    entryPrice            = None
    SL                    = None
    TP                    = None
    SLORDERID             = None
    TPORDERID             = None

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
                self.exchange.setleverage(self.TRADING_SYMBOL, self.LEVERAGE)
                data1         = self.exchange.GetAccountData()
                balancestr    = data1['availableBalance']
                self.BALANCE  = float2fixed(float(balancestr), 1000)
                stat          = self.exchange.proctor(self.TRADING_SYMBOL)
                if stat==None:
                    self.STATUS   = self.STATUS_LIST[1]
                elif stat=='PROTECTED':
                    self.STATUS   = self.STATUS_LIST[3]
                elif stat=='NOT PROTECTED':
                    self.exchange.closeposition(self.TRADING_SYMBOL)
                    self.STATUS   = self.STATUS_LIST[1]
                txt           = self.MSG[4].format(self.BALANCE, self.LEVERAGE, self.STRATEGY_PARAMS['name'], self.TRADING_TIMEFRAME, self.FATHER_TIMEFRAME)
                self.send_api_msg(txt)

            except Exception as Err:
                self.STATUS = 'connection_failed'
                self.send_api_msg(self.STATUS)
                raise(Err)

    def awaiting_signals(self):
        print('awaiting signals!')
        while True:
            self.df = self.exchange.GetSymbolKlines(        self.TRADING_SYMBOL,
                                                            self.TRADING_TIMEFRAME, 
                                                            self.TRADING_WINDOW        )
            Indicators.AddIndicators(self.df, self.indicatorsList, self.STRATEGY_PARAMS)
            if 'ftf' in self.STRATEGY_PARAMS:
                self.fdf = self.exchange.GetSymbolKlines(       self.TRADING_SYMBOL,
                                                                self.STRATEGY_PARAMS['ftf'], 
                                                                self.TRADING_WINDOW_FTF         )
                Indicators.AddIndicators(self.fdf, self.ftf_indicatorsList, self.STRATEGY_PARAMS)
            # ret    = Strategies.strategy(self.df.iloc[-3:-1], self.STRATEGY_PARAMS['name'], self.STRATEGY_PARAMS, self.fdf.iloc[:-1])
            # ret    = Strategies.strategy(self.df.iloc[-2:], self.STRATEGY_PARAMS['name'], self.STRATEGY_PARAMS, self.fdf)
            ret    = Strategies.strategy(self.df.iloc[-3:-1], self.STRATEGY_PARAMS['name'], self.STRATEGY_PARAMS, self.fdf)
            print(ret)
            signal = None; ichidiff = None; rsi = None
            if ret:
                signal = ret['signal']; ichidiff = ret['ichidiff']; rsi = ret['rsi']
            lastPrice  = self.df['close'].iloc[-2]
            # signal = 'short'
            if signal:
                txt   = self.MSG[0].format(self.STRATEGY_PARAMS['name'], rsi, ichidiff, self.TRADING_SYMBOL, self.WORDS[signal], lastPrice,  self.df['date'].iloc[-2])
                self.send_api_msg(txt)
                self.STATUS = self.STATUS_LIST[2]
                self.SIGNAL = signal
                
                sl, tp           = Strategies.tpsl(ret, self.TPSL_PARAMS['name'], self.TPSL_PARAMS)
                self.entryPrice  = lastPrice
                self.SL          = float2fixed(sl, self.PRICE_PRECISION[self.TRADING_SYMBOL])
                self.TP          = float2fixed(tp, self.PRICE_PRECISION[self.TRADING_SYMBOL])
                break
            else:
                None
                # time.sleep(0.5)
                # print('pending next candle...')
                # pending_next_candle(self.INTERVAL_DETAIL[self.TRADING_TIMEFRAME]['tf_reference'])
        return signal, lastPrice, sl, tp

    def calculating_quantity(self):
        print('calculating quantity!')
        balance        = self.BALANCE
        poslot         = min([balance, self.FIXED_LOT])
        if self.FIXED:
            levdbal        = poslot*self.LEVERAGE
            lastprice      = self.df['close'].iloc[-1]
            self.QUANTITY  = float2fixed(levdbal/lastprice, self.QUANTITY_PRECISION[self.TRADING_SYMBOL])
            self.SIDE      = 'BUY' if (self.SIGNAL=='long') else 'SELL'
            return
        
        if balance < self.CAPITAL*(1+self.MAX_DRAW_SHUTDOWN/100):
            txt = self.MSG[5]
            print(txt)
            self.send_api_msg(txt)
            self.QUANTITY  = 0
            return
        levdbal        = balance*self.LEVERAGE
        levdbal        = levdbal*self.LOT
        lastprice      = self.df['close'].iloc[-1]
        self.QUANTITY  = float2fixed(levdbal/lastprice, self.QUANTITY_PRECISION[self.TRADING_SYMBOL])
        self.SIDE      = 'BUY' if (self.SIGNAL=='long') else 'SELL'

    def placing_orders(self):
        print('placing tp/sl orders!')
        self.calculating_quantity()
        slorder = self.exchange.place_sl_limit_order(self.TRADING_SYMBOL, self.SIDE, self.QUANTITY, self.SL, self.SL)
        tporder = self.exchange.place_tp_limit_order(self.TRADING_SYMBOL, self.SIDE, self.QUANTITY, self.TP, self.TP)

        print(slorder)
        print(tporder)
        if (not slorder.keys().__contains__('orderId')) or (not tporder.keys().__contains__('orderId')):
            print('sl/tp order failed to be placed!')
            if (not slorder.keys().__contains__('msg')):
                errormsg = slorder['msg']
                txt      = self.MSG[3].format(errormsg)
                self.send_api_msg(txt)
            if (not tporder.keys().__contains__('msg')):
                errormsg = tporder['msg']
                txt      = self.MSG[3].format(errormsg)
                self.send_api_msg(txt)
            self.exchange.cancel_all_orders(self.TRADING_SYMBOL)
            return False
        
        self.SLORDERID = slorder['orderId']
        self.TPORDERID = tporder['orderId']

        # Placing limit order to open position:
        liorder = self.exchange.place_limit_order(self.TRADING_SYMBOL, self.SIDE, self.QUANTITY, self.entryPrice)
        if not liorder.keys().__contains__('orderId'):
            print('market order failed to be placed!')
            errormsg = liorder['msg']
            txt      = self.MSG[3].format(errormsg)
            self.send_api_msg(txt)
            print(liorder)
            self.exchange.cancel_all_orders(self.TRADING_SYMBOL)
            return False
        self.LIORDERID = liorder['orderId']
        ret = self.exchange.pending_tofill_order(self.TRADING_SYMBOL,  self.LIORDERID, self.W84FILLING)
        if not ret:
            self.send_api_msg(self.MSG[6])      
            self.exchange.cancel_all_orders(self.TRADING_SYMBOL)
            return False
        position = self.exchange.GetPositionData(self.TRADING_SYMBOL)[0]    
        entryPrice = position['entryPrice']
        txt      = self.MSG[1].format(self.TRADING_SYMBOL, self.QUANTITY, entryPrice, self.SL, self.TP, self.BALANCE, time.time())
        self.send_api_msg(txt)      
        return True

    def handling_open_positions(self):
        while True:
            position      = self.exchange.GetPositionData(self.TRADING_SYMBOL)[0]
            # print(position)        
            if (position['positionAmt']=='0.000'):
                print('position may have concluded!')
                oldbalance    = self.BALANCE
                data1         = self.exchange.GetAccountData()  # To make sure balance is update before issuing signal
                balancestr    = data1['availableBalance'] 
                self.BALANCE  = float2fixed(float(balancestr), 1000)
                PNL           = float2fixed(self.BALANCE-oldbalance, 1000)
                ROE           = float2fixed(PNL/oldbalance*100, 1000) 
                ifhappy       = 1 if PNL>0 else -1
                txt           = self.MSG[2].format(self.TRADING_SYMBOL, None, PNL, ROE, self.CONCL[ifhappy], self.BALANCE, time.time())
                self.send_api_msg(txt)
                self.STATUS = self.STATUS_LIST[1]
                self.exchange.cancel_all_orders(self.TRADING_SYMBOL)
                return True
            else:
                ret = self.exchange.proctor(self.TRADING_SYMBOL)
                if ret == 'NOT PROTECTED':
                    self.exchange.closeposition(self.TRADING_SYMBOL)
                    # return False

    def send_api_msg(self, txt):
        for chid in self.CHID:
            ret = self.telapi.sendmessage(chid, txt, None)
        return ret
    
    def checktpsl(self, amt, side, price):
        protection = False
        params = {'symbol': self.TRADING_SYMBOL}
        orders = self.exchange.GetAllOrderInfo(params, status='NEW')
        tp = next(item for item in orders if item["type"] == "TAKE_PROFIT")
        sl = next(item for item in orders if item["type"] == "STOP_MARKET")
        if len(orders==2):
            if sl:
                if sl['side']==side and sl['quantity']==amt:
                    if tp:
                        if tp['side']==side and tp['quantity']==amt:
                            if price<max([sl['stopPrice'], tp['stopPrice']]) and price>min([sl['stopPrice'], tp['stopPrice']]):
                                protection = True
        return protection

def pending_next_candle(divisable):
    # eps  = 1000000000
    eps  = 0
    now  = time.time_ns()
    next = now + divisable - now%divisable + eps
    while True:
        if time.time_ns() > next:
            return None

def main():
    print('starting main loop!')
    inst = xenon_trader()
    try:
        if not inst.STATUS in inst.STATUS_LIST:
            raise('Error: Invalid System Status')
        while True:
            print('looping!!!')
            time.sleep(0.5)
            if inst.STATUS == 'awaiting_signals':
                signal = inst.awaiting_signals()
            elif inst.STATUS == 'placing_orders':
                situation = inst.placing_orders()
                if situation:
                    inst.STATUS = inst.STATUS_LIST[3]
                else:
                    inst.STATUS = inst.STATUS_LIST[4]
            elif inst.STATUS == 'handling_open_positions':
                print('handling open positions with tp/sl')
                ret = inst.handling_open_positions()
                inst.STATUS = inst.STATUS_LIST[1]
            elif inst.STATUS == 'idleing':
                print('waiting for the next candle')
                time.sleep(inst.ideling_sleep)
                inst.STATUS = inst.STATUS_LIST[1]
    except Exception as Err:
        inst.send_api_msg(Err)
        raise(Err)
                
if __name__ == "__main__":
    main()
