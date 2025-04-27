import dash
import dash_bootstrap_components as dbc
import requests
from dash import Input, Output, State, dcc, html
import dash_leaflet as dl
from dotenv import load_dotenv
import os
load_dotenv()

CAM_USER = os.getenv("CAM_USER")
CAM_PWD = os.getenv("CAM_PWD")
MEDIAMTX_SERVER_IP = os.getenv("MEDIAMTX_SERVER_IP")
STREAM_NAME = os.getenv("STREAM_NAME")

pyro_logo = "https://pyronear.org/img/logo_letters_orange.png"
TARGET_IP = "192.168.1.28"
STREAM_URL = f"{MEDIAMTX_SERVER_IP}:8889/{STREAM_NAME}"
FASTAPI_URL = f"http://{TARGET_IP}:8000"
CAMERAS = {"Camera 1": "cam1", "Camera 2": "cam2"}

def Navbar():
    return dbc.Navbar(
        dbc.Row([dbc.Col(html.Img(src=pyro_logo, height="30px"), width=3)], align="center"),
        color="#044448",
        dark=True,
        className="mb-4",
    )

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

# Styles
button_style = {
    "background": "none",
    "border": "none",
    "fontSize": "28px",
    "padding": "0",
    "margin": "0",
    "cursor": "pointer",
}

small_button_style = {
    "background": "none",
    "border": "1px solid #ccc",
    "fontSize": "16px",
    "padding": "5px 10px",
    "marginBottom": "8px",
    "cursor": "pointer",
    "width": "100%"
}

app.layout = dbc.Container(
    [
        Navbar(),

        dbc.Row(
            [
                # LEFT: Stream + controls
                dbc.Col(
                    [
                        # Stream + joystick
                        html.Div([
                            html.Iframe(
                                id="video-stream",
                                src=STREAM_URL,
                                style={
                                    "width": "100%",
                                    "height": "500px",
                                    "border": "none",
                                    "borderRadius": "10px",
                                },
                            ),
                            html.Div([
                                dbc.Row([
                                    dbc.Col(),
                                    dbc.Col(html.Button("⬆️", id="move-up", n_clicks=0, style=button_style), width="auto"),
                                    dbc.Col(),
                                ], justify="center"),
                                dbc.Row([
                                    dbc.Col(html.Button("⬅️", id="move-left", n_clicks=0, style=button_style), width="auto"),
                                    dbc.Col(html.Button("🛑", id="stop-move", n_clicks=0, style=button_style), width="auto"),
                                    dbc.Col(html.Button("➡️", id="move-right", n_clicks=0, style=button_style), width="auto"),
                                ], justify="center"),
                                dbc.Row([
                                    dbc.Col(),
                                    dbc.Col(html.Button("⬇️", id="move-down", n_clicks=0, style=button_style), width="auto"),
                                    dbc.Col(),
                                ], justify="center"),
                            ], style={
                                "position": "absolute",
                                "bottom": "10px",
                                "right": "10px",
                                "padding": "5px",
                                "borderRadius": "8px",
                            })
                        ], style={"position": "relative"}),

                        # Row for sliders side by side
                        dbc.Row([
                            dbc.Col([
                                html.Div("Move Speed", style={"textAlign": "center", "fontWeight": "bold"}),
                                dcc.Slider(id="speed-input", min=1, max=10, step=1, value=5, marks={1: "1", 5: "5", 10: "10"}),
                            ], width=6),
                            dbc.Col([
                                html.Div("Zoom Level", style={"textAlign": "center", "fontWeight": "bold"}),
                                dcc.Slider(id="zoom-input", min=0, max=64, step=1, value=0, marks={0: "0", 32: "32", 64: "64"}),
                            ], width=6),
                        ], className="mt-4"),
                    ],
                    md=8,
                ),

                # RIGHT: Camera select + map
                dbc.Col(
                    [
                        html.H5("Camera Selection", className="text-center mb-3"),
                        dcc.Dropdown(
                            id="camera-select",
                            options=[{"label": name, "value": cam_id} for name, cam_id in CAMERAS.items()],
                            value="cam1",
                            clearable=False,
                            className="mb-2",
                        ),
                        # Start/Stop side by side with no background
                        dbc.Row([
                            dbc.Col(
                                html.Button("▶️ Start", id="start-stream", n_clicks=0, style={
                                    "background": "none",
                                    "border": "none",
                                    "fontSize": "18px",
                                    "cursor": "pointer",
                                    "width": "100%"
                                }),
                                width=6
                            ),
                            dbc.Col(
                                html.Button("⏹️ Stop", id="stop-stream", n_clicks=0, style={
                                    "background": "none",
                                    "border": "none",
                                    "fontSize": "18px",
                                    "cursor": "pointer",
                                    "width": "100%"
                                }),
                                width=6
                            ),
                        ], justify="center", className="mb-4"),

                        html.H6("Camera Location", className="text-center mb-2"),
                        dl.Map(center=[48.8986, 2.3760], zoom=12, children=[
                            dl.TileLayer(),
                            dl.Marker(position=[48.8986, 2.3760])
                        ], style={"width": "100%", "height": "350px", "borderRadius": "10px"}),
                    ],
                    md=4,
                ),
            ],
            className="mb-4",
        ),

        html.Div(id="output-message", className="text-center mb-2", style={"fontWeight": "bold"}),
    ],
    fluid=True,
)


app.index_string = """
<!DOCTYPE html>
<html>
<head>{%metas%}<title>Pyronear Camera</title>{%favicon%}{%css%}</head>
<body>{%app_entry%}<footer>{%config%}{%scripts%}{%renderer%}</footer></body>
</html>
"""

# API Communication
def send_api_request(endpoint: str):
    try:
        response = requests.post(f"{FASTAPI_URL}{endpoint}")
        return response.json().get("message", "Unknown response")
    except requests.exceptions.RequestException:
        return "Error: Could not reach API server."

# Main Callback
@app.callback(
    Output("output-message", "children"),
    [
        Input("start-stream", "n_clicks"),
        Input("stop-stream", "n_clicks"),
        Input("move-up", "n_clicks"),
        Input("move-down", "n_clicks"),
        Input("move-left", "n_clicks"),
        Input("move-right", "n_clicks"),
        Input("stop-move", "n_clicks"),
        Input("zoom-input", "value"),
    ],
    [
        State("camera-select", "value"),
        State("speed-input", "value"),
    ],
)
def control_camera(start_stream, stop_stream, up, down, left, right, stop, zoom_level, camera_id, move_speed):
    ctx = dash.callback_context
    if not ctx.triggered:
        return ""

    button_id = ctx.triggered[0]["prop_id"].split(".")[0]

    direction_map = {
        "move-up": "Up",
        "move-down": "Down",
        "move-left": "Left",
        "move-right": "Right",
        "stop-move": "Stop",
    }

    if button_id == "start-stream":
        return send_api_request(f"/start_stream/{camera_id}")
    elif button_id == "stop-stream":
        return send_api_request("/stop_stream")
    elif button_id in direction_map:
        direction = direction_map[button_id]
        if direction != "Stop":
            return send_api_request(f"/move/{camera_id}/{direction}/{move_speed}")
        else:
            return send_api_request(f"/stop/{camera_id}")
    elif button_id == "zoom-input":
        return send_api_request(f"/zoom/{camera_id}/{zoom_level}")

    return ""

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8050)
