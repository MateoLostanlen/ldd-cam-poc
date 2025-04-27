import dash
import dash_bootstrap_components as dbc
import requests
from dash import Input, Output, State, dcc, html
import dash_leaflet as dl
from dotenv import load_dotenv
import os
from utils import build_vision_polygon


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

site_lat = 48.426746125557
site_lon = 2.71087590966019
azimuth = 45
opening_angle = 54
dist_km = 15


def Navbar():
    return dbc.Navbar(
        dbc.Row(
            [dbc.Col(html.Img(src=pyro_logo, height="30px"), width=3)], align="center"
        ),
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
    "width": "100%",
}

app.layout = html.Div(

    [
        Navbar(),
        
        html.Div(
    [
        html.Div(
            id="stream-status",
            style={
                "color": "white",
                "fontWeight": "bold",
                "fontSize": "16px",
                "paddingLeft": "16px",
                "height": "50px",
                "display": "flex",
                "alignItems": "center",
            },
        ),
        html.Button(
            "Fermer la levée de doute",
            id="close-doubt",
            n_clicks=0,
            style={
                "background": "none",
                "border": "1px solid white",
                "color": "white",
                "borderRadius": "8px",
                "padding": "6px 12px",
                "cursor": "pointer",
                "fontSize": "14px",
                "marginRight": "16px",
                "height": "36px",
            },
        ),
    ],
    style={
        "backgroundColor": "black",
        "height": "50px",
        "width": "100%",
        "marginTop": "-25px",
        "marginBottom": "8px",
        "padding": "0",
        "display": "flex",
        "justifyContent": "space-between",  
        "alignItems": "center",           
    },
),

        dbc.Row(
            [
                # LEFT: Stream + controls
                dbc.Col(
                    [
                        # Stream + joystick
                        html.Div(
                            [
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
                                html.Div(
                                    [
                                        dbc.Row(
                                            [
                                                dbc.Col(),
                                                dbc.Col(
                                                    html.Button(
                                                        "⬆️",
                                                        id="move-up",
                                                        n_clicks=0,
                                                        style=button_style,
                                                    ),
                                                    width="auto",
                                                ),
                                                dbc.Col(),
                                            ],
                                            justify="center",
                                        ),
                                        dbc.Row(
                                            [
                                                dbc.Col(
                                                    html.Button(
                                                        "⬅️",
                                                        id="move-left",
                                                        n_clicks=0,
                                                        style=button_style,
                                                    ),
                                                    width="auto",
                                                ),
                                                dbc.Col(
                                                    html.Button(
                                                        "🛑",
                                                        id="stop-move",
                                                        n_clicks=0,
                                                        style=button_style,
                                                    ),
                                                    width="auto",
                                                ),
                                                dbc.Col(
                                                    html.Button(
                                                        "➡️",
                                                        id="move-right",
                                                        n_clicks=0,
                                                        style=button_style,
                                                    ),
                                                    width="auto",
                                                ),
                                            ],
                                            justify="center",
                                        ),
                                        dbc.Row(
                                            [
                                                dbc.Col(),
                                                dbc.Col(
                                                    html.Button(
                                                        "⬇️",
                                                        id="move-down",
                                                        n_clicks=0,
                                                        style=button_style,
                                                    ),
                                                    width="auto",
                                                ),
                                                dbc.Col(),
                                            ],
                                            justify="center",
                                        ),
                                    ],
                                    style={
                                        "position": "absolute",
                                        "bottom": "10px",
                                        "right": "10px",
                                        "padding": "5px",
                                        "borderRadius": "8px",
                                    },
                                ),
                            ],
                            style={"position": "relative"},
                        ),
                        # Row for sliders side by side
                        dbc.Row(
                            [
                                dbc.Col(
                                    html.Div(
                                        [
                                            html.Div(
                                                "Move Speed",
                                                style={
                                                    "textAlign": "center",
                                                    "fontWeight": "bold",
                                                    "marginBottom": "8px",
                                                },
                                            ),
                                            dcc.Slider(
                                                id="speed-input",
                                                min=0,
                                                max=100,
                                                step=10,
                                                value=0,
                                                marks={i: str(i) for i in range(0, 101, 10)},  # Show every 10
                                            ),
                                        ],
                                        style={
                                            "border": "2px solid #098386",  # Teal border
                                            "borderRadius": "10px",  # Rounded corners
                                            "padding": "8px",  # Inner padding
                                            "marginBottom": "16px",  # Space below
                                        },
                                    ),
                                    width=6,
                                ),
                                dbc.Col(
                                    html.Div(
                                        [
                                            html.Div(
                                                "Zoom Level",
                                                style={
                                                    "textAlign": "center",
                                                    "fontWeight": "bold",
                                                    "marginBottom": "8px",
                                                },
                                            ),
                                            dcc.Slider(
                                                id="zoom-input",
                                                min=0,
                                                max=100,
                                                step=10,
                                                value=0,
                                                marks={i: str(i) for i in range(0, 101, 10)},  # Show every 10
                                            ),

                                        ],
                                        style={
                                            "border": "2px solid #098386",  # Teal border
                                            "borderRadius": "10px",  # Rounded corners
                                            "padding": "8px",  # Inner padding
                                            "marginBottom": "16px",  # Space below
                                        },
                                    ),
                                    width=6,
                                ),
                            ],
                            className="mt-4",
                        ),
                    ],
                    md=8,
                    style={"padding": "0"},
                ),
                # RIGHT: Camera select + map
                dbc.Col(
                    [
                        html.Div(
                            dcc.Dropdown(
                                id="camera-select",
                                options=[
                                    {"label": name, "value": cam_id}
                                    for name, cam_id in CAMERAS.items()
                                ],
                                value="cam1",
                                clearable=False,
                                className="mb-2",
                                style={
                                    "border": "none",  # No border for the dropdown itself
                                    "borderRadius": "8px",  # Still rounded inside
                                    "backgroundColor": "white",
                                    "fontWeight": "bold",
                                    "width": "100%",
                                },
                            ),
                            style={
                                "border": "2px solid #098386",  # <-- Border around the wrapper
                                "borderRadius": "10px",  # <-- Round the corners
                                "marginBottom": "16px",
                            },
                        ),
                        # Start/Stop side by side with no background
                        dbc.Row(
                            [
                                dbc.Col(
                                    html.Button(
                                        "▶️ Start",
                                        id="start-stream",
                                        n_clicks=0,
                                        style={
                                            "background": "none",
                                            "border": "2px solid #098386",
                                            "borderRadius": "8px",
                                            "fontSize": "18px",
                                            "cursor": "pointer",
                                            "width": "100%",
                                            "color": "#098386",
                                        },
                                    ),
                                    width=6,
                                ),
                                dbc.Col(
                                    html.Button(
                                        "⏹️ Stop",
                                        id="stop-stream",
                                        n_clicks=0,
                                        style={
                                            "background": "none",
                                            "border": "2px solid #098386",
                                            "borderRadius": "8px",
                                            "fontSize": "18px",
                                            "cursor": "pointer",
                                            "width": "100%",
                                            "color": "#098386",
                                        },
                                    ),
                                    width=6,
                                ),
                            ],
                            justify="center",
                            className="mb-4",
                        ),
                        # Updated map with vision cone
                        dl.Map(
                            center=[site_lat, site_lon],
                            zoom=10,
                            children=[
                                dl.TileLayer(),
                                dl.LayerGroup(
                                    id="vision-layer",
                                    children=[
                                        build_vision_polygon(
                                            site_lat=site_lat,
                                            site_lon=site_lon,
                                            azimuth=azimuth,
                                            opening_angle=opening_angle,
                                            dist_km=dist_km,
                                        )[0]
                                    ],
                                ),
                                dl.Marker(position=[site_lat, site_lon]),
                            ],
                            style={
                                "width": "100%",
                                "height": "350px",
                                "borderRadius": "10px",
                            },
                        ),
                    ],
                    md=4,
                    style={"padding": "0", "paddingLeft": "16px"},
                ),
            ],
            className="mb-4",
        ),
        html.Div(
            id="output-message",
            className="text-center mb-2",
            style={"fontWeight": "bold", "display": "none"},
        ),
        dcc.Interval(id="stream-timer", interval=1000, n_intervals=0, disabled=True),
        dcc.Store(id="detection-status", data="stopped"),


    ],
    style={"padding": "0", "margin": "0", "width": "100%", "height": "100%"},
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
def control_camera(
    start_stream,
    stop_stream,
    up,
    down,
    left,
    right,
    stop,
    zoom_level,
    camera_id,
    move_speed,
):
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
            true_speed = int(move_speed / 10)
            return send_api_request(f"/move/{camera_id}/{direction}/{true_speed}")
        else:
            return send_api_request(f"/stop/{camera_id}")
    # Inside your control_camera callback
    elif button_id == "zoom-input":
        # Convert 0-100 scale to 0-41 scale
        true_zoom = int(zoom_level * 41 / 100)
        return send_api_request(f"/zoom/{camera_id}/{true_zoom}")


    return ""

from dash import ctx
import datetime

start_time = None

@app.callback(
    Output("stream-timer", "disabled"),
    Output("detection-status", "data"),
    Input("start-stream", "n_clicks"),
    Input("stop-stream", "n_clicks"),
    prevent_initial_call=True
)
def control_detection(start_clicks, stop_clicks):
    triggered = ctx.triggered_id
    global start_time

    if triggered == "start-stream":
        start_time = datetime.datetime.now()
        return False, "running"  # Enable timer
    elif triggered == "stop-stream":
        start_time = None
        return True, "stopped"   # Disable timer

    return dash.no_update, dash.no_update

@app.callback(
    Output("stream-status", "children"),
    Input("stream-timer", "n_intervals"),
    State("detection-status", "data"),
)
def update_status(n, detection_status):
    if detection_status == "running" and start_time:
        elapsed = datetime.datetime.now() - start_time
        minutes, seconds = divmod(int(elapsed.total_seconds()), 60)
        timer_text = f"{minutes:02d}:{seconds:02d}"
        return html.Div([
            html.Span("🔴 Live stream", style={
                "backgroundColor": "#f99",
                "color": "black",
                "borderRadius": "6px",
                "padding": "4px 8px",
                "marginRight": "8px",
                "fontWeight": "bold",
            }),
            html.Span(f"Levée de doute en cours, la détection n'est plus active depuis {timer_text}")
        ])
    else:
        return ""



if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8050)
