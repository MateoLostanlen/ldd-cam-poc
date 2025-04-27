import dash
import dash_bootstrap_components as dbc
import requests
import time
from dash import Input, Output, State, dcc, html
from dash_extensions import EventListener

pyro_logo = "https://pyronear.org/img/logo_letters_orange.png"
TARGET_IP = "192.168.1.28"

STREAM_URL = "http://91.134.47.14:8889/mateostream"

# FastAPI server address
FASTAPI_URL = f"http://{TARGET_IP}:8000"

# Camera Selection
CAMERAS = {"Camera 1": "cam1", "Camera 2": "cam2"}

def Navbar():
    """Returns a Navbar with the Pyronear logo."""
    return dbc.Navbar(
        [
            dbc.Row(
                [dbc.Col(html.Img(src=pyro_logo, height="30px"), width=3)],
                align="center",
            )
        ],
        color="#044448",
        dark=True,
        className="mb-4",
    )

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

app.layout = dbc.Container(
    [
        Navbar(),
        dbc.Row(
            [
                # IFRAME VIDEO (LEFT)
                dbc.Col(
                    html.Div(
                        [
                            html.Div(
                                [
                                    html.Iframe(
                                        id="video-stream",
                                        src=STREAM_URL,
                                        style={
                                            "position": "absolute",
                                            "top": "0",
                                            "left": "0",
                                            "width": "100%",
                                            "height": "100%",
                                            "border": "none",
                                            "borderRadius": "10px",
                                            "display": "block",
                                        },
                                    ),
                                    EventListener(
                                        id="click-listener",
                                        children=html.Div(
                                            id="click-overlay",
                                            n_clicks=0,
                                            style={
                                                "position": "absolute",
                                                "top": 0,
                                                "left": 0,
                                                "width": "100%",
                                                "height": "100%",
                                                "border": "2px dashed red",
                                                "zIndex": 2,
                                                "cursor": "crosshair",
                                                "backgroundColor": "rgba(255, 255, 255, 0.01)",
                                            },
                                        ),
                                        events=[{"event": "pointerdown"}],
                                    ),
                                ],
                                style={
                                    "position": "relative",
                                    "height": "500px",
                                    "width": f"{round(500 * 16 / 9)}px",  # 16:9 aspect ratio
                                    "overflow": "hidden",
                                    "margin": "auto",
                                },
                            ),
                        ],
                        id="video-container",
                    ),
                    md=8,
                ),
                # CAMERA CONTROLS (RIGHT)
                dbc.Col(
                        [
                            html.H5("Stream & Camera Controls", className="text-center mb-3"),

                            html.Label("Select Camera:"),
                            dcc.Dropdown(
                                id="camera-select",
                                options=[{"label": name, "value": cam_id} for name, cam_id in CAMERAS.items()],
                                value="cam1",
                                clearable=False,
                                className="mb-3",
                            ),

                            html.Label("Move Speed (1-10):"),
                            dcc.Slider(
                                id="speed-slider",
                                min=1, max=10, step=1, value=5,
                                marks={1: "1", 5: "5", 10: "10"},
                                className="mb-4",
                            ),

                            # Stream control buttons
                            dbc.Row([
                                dbc.Col(dbc.Button("Start Stream", id="start-stream", color="success", className="w-100"), width=6),
                                dbc.Col(dbc.Button("Stop Stream", id="stop-stream", color="danger", className="w-100"), width=6),
                            ], className="mb-3"),

                            # Move controls
                            html.Div([
                                dbc.Row([
                                    dbc.Col(),
                                    dbc.Col(dbc.Button("↑", id="move-up", color="primary", size="sm"), width="auto"),
                                    dbc.Col(),
                                ], justify="center"),
                                dbc.Row([
                                    dbc.Col(dbc.Button("←", id="move-left", color="primary", size="sm"), width="auto"),
                                    dbc.Col(dbc.Button("STOP", id="stop-move", color="danger", size="sm"), width="auto"),
                                    dbc.Col(dbc.Button("→", id="move-right", color="primary", size="sm"), width="auto"),
                                ], justify="center", className="my-2"),
                                dbc.Row([
                                    dbc.Col(),
                                    dbc.Col(dbc.Button("↓", id="move-down", color="primary", size="sm"), width="auto"),
                                    dbc.Col(),
                                ], justify="center"),
                            ], className="mb-4"),

                            # Zoom control
                            html.Label("Zoom Level:"),
                            dcc.Slider(
                                id="zoom-slider",
                                min=0, max=64, step=1, value=32,
                                marks={0: "0", 32: "32", 64: "64"},
                                className="mb-2",
                            ),
                            dbc.Button("Set Zoom", id="set-zoom", color="success", className="mb-4 w-100"),

                            # Map Button
                            dbc.Button(
                                "🗺️ Map", 
                                id="map-button", 
                                color="info", 
                                size="sm", 
                                style={"borderRadius": "50%", "width": "50px", "height": "50px", "fontSize": "20px"},
                                className="d-block mx-auto"
                            ),
                        ],
                        md=4,
                    )

            ],
            className="mb-4",
        ),
        html.Div(
            id="output-message",
            className="text-center",
            style={"fontWeight": "bold"},
        ),
        html.Div(
            id="timer-countdown",
            className="text-center",
            style={"fontWeight": "bold", "color": "red", "fontSize": "20px"},
        ),
        html.Div(
            id="click-coordinates",
            className="text-center",
            style={"fontWeight": "bold", "color": "green"},
        ),
        dcc.Store(id="click-coords"),
        dcc.Store(id="stream-start-time"),
        dcc.Interval(id="timer-interval", interval=1000, n_intervals=0),
    ],
    fluid=True,
)

# Client-side callback for click coordinates
app.clientside_callback(
    """
    function(n_clicks) {
        if (!n_clicks) return window.dash_clientside.no_update;
        return window.lastClick || null;
    }
    """,
    Output("click-coords", "data"),
    Input("click-overlay", "n_clicks"),
)

app.index_string = """
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>Pyronear Camera</title>
        {%favicon%}
        {%css%}
        <script>
            document.addEventListener("DOMContentLoaded", function () {
                document.body.addEventListener("click", function (e) {
                    const rect = e.target.getBoundingClientRect();
                    window.lastClick = {
                        offsetX: Math.round(e.clientX - rect.left),
                        offsetY: Math.round(e.clientY - rect.top),
                        width: Math.round(rect.width),
                        height: Math.round(rect.height)
                    };
                });
            });
        </script>
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
"""

# 📌 Function to Send API Requests
def send_api_request(endpoint: str):
    try:
        response = requests.post(f"{FASTAPI_URL}{endpoint}")
        return response.json().get("message", "Unknown response")
    except requests.exceptions.RequestException:
        return "Error: Could not reach API server."

# 📌 Callback for Stream, Movement & Zoom
@app.callback(
    [Output("output-message", "children"), Output("stream-start-time", "data")],
    [
        Input("start-stream", "n_clicks"),
        Input("stop-stream", "n_clicks"),
        Input("move-up", "n_clicks"),
        Input("move-down", "n_clicks"),
        Input("move-left", "n_clicks"),
        Input("move-right", "n_clicks"),
        Input("stop-move", "n_clicks"),
        Input("set-zoom", "n_clicks"),
    ],
    [
        State("camera-select", "value"),
        State("zoom-slider", "value"),
        State("speed-slider", "value"),
    ],
)
def control_camera(
    start_stream, stop_stream, up, down, left, right, stop, zoom,
    camera_id, zoom_level, move_speed
):
    ctx = dash.callback_context
    if not ctx.triggered:
        return "", None

    button_id = ctx.triggered[0]["prop_id"].split(".")[0]

    direction_map = {
        "move-up": "Up",
        "move-down": "Down",
        "move-left": "Left",
        "move-right": "Right",
        "stop-move": "Stop",
    }

    if button_id == "start-stream":
        return send_api_request(f"/start_stream/{camera_id}"), time.time()

    elif button_id == "stop-stream":
        return send_api_request("/stop_stream"), None

    elif button_id in direction_map:
        direction = direction_map[button_id]
        if direction != "Stop":
            return send_api_request(f"/move/{camera_id}/{direction}/{move_speed}"), dash.no_update
        else:
            return send_api_request(f"/stop/{camera_id}"), dash.no_update

    elif button_id == "set-zoom":
        return send_api_request(f"/zoom/{camera_id}/{zoom_level}"), dash.no_update

    return "", None

# 📌 Timer Countdown Callback
@app.callback(
    Output("timer-countdown", "children"),
    Input("timer-interval", "n_intervals"),
    State("stream-start-time", "data"),
)
def update_timer(n_intervals, stream_start_time):
    if stream_start_time is None:
        return ""

    elapsed = time.time() - stream_start_time
    remaining = max(0, 60 - int(elapsed))

    if remaining <= 0:
        return ""

    return f"⏳ Stream will stop in {remaining} seconds..."

# 📌 Show clicked coordinates
@app.callback(
    Output("click-coordinates", "children"),
    Input("click-coords", "data"),
    prevent_initial_call=True,
)
def show_coords(data):
    if not data:
        return ""
    x_percent = round((data["offsetX"] / data["width"]) * 100, 2)
    y_percent = round((data["offsetY"] / data["height"]) * 100, 2)
    return f"Clicked at x={data['offsetX']}px ({x_percent}%), y={data['offsetY']}px ({y_percent}%)"

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8050)
