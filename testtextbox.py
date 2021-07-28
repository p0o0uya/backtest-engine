import plotly.io as pio
import plotly.graph_objs as go
from plotly.offline import plot

fig = go.Figure(
    data=[
        go.Scatter(y=[2, 1, 3])
    ],
    layout=go.Layout(
        annotations=[
            go.layout.Annotation(
                text='Some<br>multi-line<br>text',
                align='left',
                showarrow=False,
                xref='paper',
                yref='paper',
                x=1.1,
                y=0.8,
                bordercolor='black',
                borderwidth=1
            )
        ]
    )
)
plot(fig)

