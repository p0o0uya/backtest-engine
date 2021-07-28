import pandas as pd
import plotly.graph_objs as go
from plotly.subplots import make_subplots
from plotly.offline import plot

class PlotData:
    
    def __init__(self, df, symbol, indicators, fdf = pd.DataFrame(), params:dict={}):
        self.df         = df
        self.fdf        = fdf
        self.symbol     = symbol
        self.indicators = indicators

    def plot(self, buy_signals = False, sell_signals = False, close_signals = False, take_profits = False, stop_losses = False, text_box = False, row2bounds = False, plot_title:str="NewPlot", rh:list = [0.90, 0.10]):
        df  = self.df
        fdf = self.fdf
        fig = make_subplots(rows=2, cols=1, 
                            shared_xaxes=True, 
                            vertical_spacing=0.02,
                            row_heights = rh,
                            subplot_titles=(self.symbol, ""))

        # prepare candlesticks data
        candle = go.Candlestick(x     = df['date'],
                                open  = df['open'],
                                close = df['close'],
                                high  = df['high'],
                                low   = df['low'],
                                name  = "Candlesticks")
        #data1 = [candle]
        fig.add_trace(candle, row=1, col=1)

        # prepare Indicators data
        for item in self.indicators:
            if item['isactive']:# and df.__contains__(item['col_name']):
                if item['col_name']=='volume':
                    secondary  = go.Bar(x     = df['date'],
                                        y     = df['volume'],
                                        name  = "volume")
                    fig.add_trace(secondary, row=1, col=1)
                elif item['col_name']=='rsi':
                    secondary  = go.Scatter(x     = df['date'],
                                            y     = df['rsi'],
                                            name  = "rsi")
                    fig.add_trace(secondary, row=2, col=1)
                elif item['col_name']=='rsidiff':
                    secondary  = go.Scatter(x     = df['date'],
                                            y     = df['rsidiff'],
                                            name  = "rsidiff")
                    fig.add_trace(secondary, row=2, col=1)
                elif item['col_name']=='stoch_rsi':
                    secondary  = go.Scatter(x     = df['date'],
                                            y     = df['K'],
                                            name  = "k_stoch_rsi",
                                            line  = dict(color = 'blue'))
                    fig.add_trace(secondary, row=2, col=1)

                    secondary  = go.Scatter(x     = df['date'],
                                            y     = df['D'],
                                            name  = "d_stoch_rsi",
                                            line  = dict(color = 'orange'))                        
                    fig.add_trace(secondary, row=2, col=1)

                elif item['col_name']=='fdfrsi':
                    secondary  = go.Scatter(x     = fdf['date'],
                                            y     = fdf['rsi'],
                                            name  = "fdfrsi")
                    fig.add_trace(secondary, row=2, col=1)

                # elif item['name']=='tenkiju':
                #     secondary  = go.Scatter(x     = df['date'],
                #                             y     = df['tenkiju'],
                #                             name  = "tenkiju")
                #     fig.add_trace(secondary, row=2, col=1)

                elif item['col_name']=='swing':
                    data = df[item['col_name']][0]
                    # print(data)
                    shapes = []
                    for pj in data:
                        shapes.append(dict(type= 'line', xref= 'paper', x0= 0, x1= 1, yref= 'y', y0 = pj, y1= pj))
                    fig.update_layout(shapes=shapes)

                elif item['col_name'] in ('tenkansen', 'kijunsen', 'senkou_a', 'senkou_b', 'chikouspan', 'ema', 'lbb', 'ubb', 'x_period_high', 'x_period_low'):

                    ichi = go.Scatter(x     = df['date'],
                                      y     = df[item['col_name']],
                                      name  = item['name'],
                                      line  = dict(color = (item['color'])))
                    fig.add_trace(ichi, row=1, col=1)
                else:
                    None
                    # print(None)
                
        if buy_signals:
            buys = go.Scatter( x           = [item[0] for item in buy_signals],
                               y           = [item[1] for item in buy_signals],
                               name        = "Buy Signals",
                               mode        = "markers",
                               marker      = dict(size=20, symbol='triangle-up', opacity=1, color='green') )
            fig.add_trace(buys, row=1, col=1)

        if sell_signals:
            sells = go.Scatter( x           = [item[0] for item in sell_signals],
                                y           = [item[1] for item in sell_signals],
                                name        = "Sell Signals",
                                mode        = "markers",
                                marker      = dict(size=20, symbol='triangle-down', opacity=1, color='red'))

            fig.add_trace(sells, row=1, col=1)

        if close_signals:
            sells = go.Scatter( x           = [item[0] for item in close_signals],
                                y           = [item[1] for item in close_signals],
                                name        = "Close Signals",
                                mode        = "markers",
                                marker      = dict(size=10, symbol='diamond', opacity=1, color='black'))

            fig.add_trace(sells, row=1, col=1)

        if take_profits:
            buys = go.Scatter( x           = [item[0] for item in take_profits],
                               y           = [item[1] for item in take_profits],
                               name        = "Take Profits",
                               mode        = "lines",
                               line      = dict(width=2, shape='linear', color='blue', dash='dot'))
            fig.add_trace(buys, row=1, col=1)

        if stop_losses:
            sells = go.Scatter( x           = [item[0] for item in stop_losses],
                                y           = [item[1] for item in stop_losses],
                                name        = "Stop Losses",
                                mode        = "lines",
                                line      = dict(width=2, shape='linear', color='red', dash='dot'))

            fig.add_trace(sells, row=1, col=1)
        rng = [df['date'].iloc[0], df['date'].iloc[-1]]
        if row2bounds:
            for val in row2bounds:
                ln = go.Scatter( x              = rng,
                                    y           = [val, val],
                                    name        = "Bound",
                                    mode        = "lines",
                                    line        = dict(width=2, shape='linear', color='red', dash='dot'))

                fig.add_trace(ln, row=2, col=1)
            

        # style and display
        # let's customize our layout a little bit:
        if text_box:
            'Some<br>multi-line<br>text'
            txt = ''
            for item in text_box:
                txt += text_box[item] + '<br>'

            fig.add_annotation(dict(    x=1.12,
                                        y=0.10,
                                        showarrow=False,
                                        text=txt,
                                        textangle=0,
                                        xref="paper",
                                        yref="paper",
                                        bordercolor = 'black',
                                        borderwidth = 1,
                                        align       = 'right'     ))


        layout = go.Layout( title = plot_title,
                            xaxis = { "title" : self.symbol,
                                      "rangeslider" : dict(),
                                      "type" : "date" },
                            yaxis = { "fixedrange" : False,} )
        
        fig.update_xaxes(rangeslider_thickness = 0.04)
        fig.update_xaxes(range = rng, rangeslider = dict(visible=False, range=rng), row=1, col=1)
        fig.update_xaxes(range = rng, rangeslider = dict(range=rng), row=2, col=1)

        #fig = go.Figure(data = data, layout = layout)
        fig.update_layout(  autosize=False,
                            height= 750, width=1500,
                            margin=dict(l=15, r=15, t=20, b=20, pad=4),
                            title_text ="")

        # fig.update_layout(xaxis=dict(range=rng, rangeslider=dict(range=rng), row=1, col=1))
        # fig.update_layout(xaxis=dict(range=rng, rangeslider=dict(range=rng), row=2, col=1))

        plot(fig,  filename='/home/pj/Documents/EN001_54.38.212.90/etc/xenontradergraphs/'+plot_title+'.html')
