import flask
import os

import dash
import dash_core_components as dcc
import dash_html_components as html

server = flask.Flask('app')
server.secret_key = os.environ.get('secret_key', 'secret')


# external CSS stylesheets
external_stylesheets = [
    'https://codepen.io/chriddyp/pen/bWLwgP.css',
    {
        'href': 'https://stackpath.bootstrapcdn.com/bootswatch/4.4.1/sketchy/bootstrap.min.css',
        'rel': 'stylesheet',
        'integrity': 'sha384-2kOE+STGAkgemIkUbGtoZ8dJLqfvJ/xzRnimSkQN7viOfwRvWseF7lqcuNXmjwrL',
        'crossorigin': 'anonymous'
    }
]

app = dash.Dash('app', server=server,
                external_stylesheets=external_stylesheets)

app.title = "Amplitude Modulation - Resend Code Generator"


app.layout = html.Div([
    html.H1('Amplitude Modulation - Resend Code Generator'),
    html.P('Extract the switch on and off timings from a digital amplitude modulated radio signal in order to generate a small arduino program to resend this signal.'),
    dcc.Upload(
        id='upload-wave-file',
        children=html.Div([
            'Drag and Drop or ',
            html.A('Select a WAVE file.')
        ]),
        style={
            'vw': '100%',
            'height': '60px',
            'lineHeight': '60px',
            'borderWidth': '1px',
            'borderStyle': 'dashed',
            'borderRadius': '5px',
            'textAlign': 'center',
            'margin': '10px'
        },
    ),
    dcc.Store(id='wave-cache'),


    html.H3("Raw Wave Input"),
    html.Label("FFT windows size:"),
    html.Div([
        dcc.Slider(
            id='transform-window',
            max=10,
            min=4,
            marks={i: str(2**i) for i in range(4, 11)},
            value=6,
            step=1
        )
    ], style={"height": "40px"}),
    html.P("Please zoom to the region with signal you want to resend"),
    dcc.Graph(id='raw-wave-graph'),


    html.H3("Gradient Extraction"),
    html.Label("Threshold:"),
    html.Div([
        dcc.Slider(
            id='grad-thres',
            marks={i: '{}'.format(10 ** i) for i in range(6)},
            max=5,
            value=2.8,
            step=0.01,
        )], style={"height": "40px"}
    ),

    dcc.Graph(id='grad-graph'),
    dcc.Store(id='switch-cache'),

    html.H3("Generated Code"),
    html.Pre(id="code-container")


], className="container")
