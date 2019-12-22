from dash.dependencies import Input, Output
import plotly.graph_objects as go
from plotly.subplots import make_subplots

import base64
import io
from scipy.io import wavfile
import numpy as np
import json
from scipy.signal import argrelextrema




#import the layout of the app
from layout import server, app


#default style of each plot
PLOT_LAYOUT = dict(
    margin={'l': 40, 'b': 30, 't': 10, 'r': 0},
    font=dict(
        family='Neucha',
        size=15,
        color='#555'
    ),
)

#placeholder for the waterfall plot
EMPTY_PLOT_A = {
    'data': [{'colorscale': [[0.0, 'rgb(12,51,131)'], [0.25, 'rgb(10,136,186)'],
                             [0.5, 'rgb(242,211,56)'], [0.75, 'rgb(242,143,56)'],
                             [1.0, 'rgb(217,30,30)']],
              'type': 'heatmap',
              'z': [[0,0,.1,1,.1,0,0]]}],
    'layout': {'font': {'color': '#555', 'family': 'Neucha', 'size': 15},
               'height': 600,
               'margin': {'b': 30, 'l': 40, 'r': 0, 't': 10},
               'template': '...',
               'xaxis': {'fixedrange': True}}
}


#placeholder plot for the ON - OFF switch times
EMPTY_PLOT_B = {
    'data': [{'mode': 'lines',
              'name': 'gradient',
              'type': 'scatter',
              'xaxis': 'x',
              'y': [0],
              'yaxis': 'y'},
             {'line': {'color': 'gray', 'dash': 'dash'},
              'mode': 'lines',
              'name': '',
              'type': 'scatter',
              'xaxis': 'x',
              'y': [0],
              'yaxis': 'y'},
             {'line': {'color': 'gray', 'dash': 'dash'},
              'mode': 'lines',
              'name': '',
              'type': 'scatter',
              'xaxis': 'x',
              'y': [0],
              'yaxis': 'y'},
             {'mode': 'markers',
              'name': 'ON',
              'type': 'scatter',
              'x': [0],
              'xaxis': 'x2',
              'y': [0],
              'yaxis': 'y2'},
             {'mode': 'markers',
              'name': 'OFF',
              'type': 'scatter',
              'x': [0],
              'xaxis': 'x2',
              'y': [0],
              'yaxis': 'y2'}],
    'layout': {'font': {'color': '#555', 'family': 'Neucha', 'size': 15},
               'height': 500,
               'margin': {'b': 30, 'l': 40, 'r': 0, 't': 10},
               'template': '...',
               'xaxis': {'anchor': 'y', 'domain': [0.0, 1.0], 'matches': 'x2', 'showticklabels': False},
               'xaxis2': {'anchor': 'y2', 'domain': [0.0, 1.0]},
               'yaxis': {'anchor': 'x', 'domain': [0.51, 1.0]},
               'yaxis2': {'anchor': 'x2', 'domain': [0.0, 0.49]}}
}



@app.callback(
    [
        Output('raw-wave-graph', 'figure'),
        Output('wave-cache', 'data'),
    ],
    [
        Input('upload-wave-file', 'contents'),
        Input('transform-window', 'value')
    ],
)
def update_raw_wave_graph(file_data, transformWindowExp):
    """
    compute a FFT of the radio waveform, show a waterfall diagram and store the
    waveform for future computation
    """
    if file_data == None:
        return EMPTY_PLOT_A, ""

    try:
        #try to read the file and extract the wave data
        content_type, content_string=file_data.split(',')
        decoded=base64.b64decode(content_string)
        fs, data=wavfile.read(io.BytesIO(decoded))
    except Exception as ex:
        return EMPTY_PLOT_A, ""

    #prepare the chunk size for the FFT transforms
    tfSize=2**transformWindowExp
    nrChunks=int(len(data)/tfSize)

    #make a complex waveform
    complexData=data[:, 0] + 1j*data[:, 1]
    

    #apply the transforms
    imageData=[np.fft.fftshift(np.fft.fft(d)) for d in np.split(
        complexData[0:nrChunks*tfSize], nrChunks)]

    #create a density map figure
    fig=go.Figure(data = go.Heatmap(z=np.absolute(imageData), colorscale="portland"))
    fig["layout"]["xaxis"]["fixedrange"]=True
    fig["layout"]["height"]=600
    fig["layout"].update(**PLOT_LAYOUT)

    #compute the absolute values of the wave and store it
    data = np.array(data).astype(float)
    if len(np.shape(data)) == 2:
        data=np.sqrt(np.square(data[:, 0]) + np.square(data[:, 1]))

    return fig, {"data": data, "fs": fs}



@app.callback(
    [
        Output('grad-graph', 'figure'),
        Output('switch-cache', 'data')
    ],
    [
        Input('wave-cache', 'data'),
        Input('raw-wave-graph', 'relayoutData'),

        Input('transform-window', 'value'),


        Input('grad-thres', 'value'),
    ],
)
def update_output(cache, layout, transformWindowExp, threshold):
    """
    aplly a gradient transformation on the selected waveform
    and extract the switch on and off times in order to compute
    a small source code
    """

    if not "data" in cache:
        return EMPTY_PLOT_B, {}

    # extract the waveform and the frames per second from the cache
    data=cache["data"]
    data=np.array(data).astype(float)
    fs=cache["fs"]

    # get the extraction window from the zoom region
    tfSize=2**transformWindowExp
    if "yaxis.range[0]" in layout:
        start=int(layout['yaxis.range[0]'])*tfSize
        end=int(layout['yaxis.range[1]'])*tfSize
        data=data[start:end]
    else:
        return EMPTY_PLOT_B, {}

    # compute the gradient of the waveform
    length=len(data)
    data=np.nan_to_num(data)
    grad=np.gradient(data)

    # rescale it
    rescale=np.max(grad)/1000.0
    grad /= rescale

    # set all values below the threshold to zero
    grad_data=grad * (np.abs(grad) > 10**threshold)

    # get the switch on times and switch off times
    switchON=argrelextrema(grad_data, np.greater)[0]
    switchOFF=argrelextrema(grad_data, np.less)[0]

    # create a combined plot of the gradients, with a threshold line
    # and a plot with dots for switch on and switch off
    fig=make_subplots(
        rows = 2, cols = 1, shared_xaxes = True, vertical_spacing = 0.02
    )
    fig.add_trace(go.Scatter(y=grad_data, mode='lines',
                             name="gradient"), row=1, col=1)
    fig.add_trace(go.Scatter(y=np.ones_like(grad_data)*(10**threshold),
                             mode='lines', name="", line={'dash': 'dash', 'color': 'gray'}), row=1, col=1)
    fig.add_trace(go.Scatter(y=-np.ones_like(grad_data)*(10**threshold),
                             mode='lines', name="", line={'dash': 'dash', 'color': 'gray'}), row=1, col=1)

    fig.add_trace(go.Scatter(x=switchON, y=np.ones_like(
        switchON), mode="markers", name="ON"), row=2, col=1)
    fig.add_trace(go.Scatter(x=switchOFF, y=np.ones_like(
        switchOFF), mode="markers", name="OFF"), row=2, col=1)

    #apply layout
    fig["layout"]["height"] = 500
    fig["layout"].update(**PLOT_LAYOUT)


    return fig, {"on": switchON, "off": switchOFF, "fs": fs, "length": length}



@app.callback(Output("code-container", "children"),
              [
    Input('switch-cache', 'data')
],
)
def generate_code(data):
    """
    generate a small arduino program code with the switch on and off extracted 
    from the waveform
    """

    if not "on" in data:
        return "Please add data"

    # extract the data from the swtich on - off store container
    switchON = data["on"]
    switchOFF = data["off"]
    fs = data["fs"]
    length = data["length"]

    # fill an array with the switch on and off timings needed for the source code
    timings = []

    # transform all times into microseconds 
    timeScale = 1000000 / fs

    # check all switch on ans offs and check and make a smale plausible check
    for i in range(len(switchON)):
        if switchOFF[i] < switchON[i]:
            return "Error! Please optimize the signal extraction."
        if i < len(switchON)-1:
            if switchON[i+1] < switchOFF[i]:
                return "Error! Please optimize the signal extraction."
            timings.append( [round((switchOFF[i] - switchON[i])*timeScale),  round((switchON[i+1] - switchOFF[i])*timeScale)] )
        else:
            timings.append( [round((switchOFF[i] - switchON[i])*timeScale),  round((length - switchOFF[i])*timeScale)] )

    # transform this into source code using json serialization and transforms to get c++ 11
    output = """
# include <Arduino.h>

const int signalPin = 32;
unsigned int timings[{}][2] = {};

void myDelay(unsigned int d)
{{
  if (d < 10000)
  {{
    delayMicroseconds(d);
  }}
  else
  {{
    delay(d / 1000);
  }}
}}

void setup()
{{
  pinMode(signalPin, OUTPUT);
}}

void loop()
{{
  for (unsigned int* elem : timings)
  {{
    digitalWrite(signalPin, HIGH);
    myDelay(elem[0]);
    digitalWrite(signalPin, LOW);
    myDelay(elem[1]);
  }}
}}
""".format(
        len(timings),
        json.dumps(timings).replace('[', '{').replace(']', '}').replace('}, ', '},\n\t').replace('{{', '{\n\t{').replace('}}', '}\n}'))



    return output


if __name__ == '__main__':
    app.run_server(debug=True)
