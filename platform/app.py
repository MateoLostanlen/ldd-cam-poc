import dash
import dash_bootstrap_components as dbc
import requests
from dash import Input, Output, State, dcc, html
from dash_extensions import EventListener


pyro_logo = "https://pyronear.org/img/logo_letters_orange.png"

TARGET_IP = "192.168.1.104"

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
                                        src=f"http://{TARGET_IP}:8889/cam",
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
                                    "width": f"{round(500 * 16 / 9)}px",  # 16:9 aspect ratio width for 500px height = ~889px
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
                        html.H5(
                            "Stream & Camera Controls", className="text-center mb-3"
                        ),
                        html.Label("Select Camera:"),
                        dcc.Dropdown(
                            id="camera-select",
                            options=[
                                {"label": name, "value": cam_id}
                                for name, cam_id in CAMERAS.items()
                            ],
                            value="cam1",
                            clearable=False,
                            className="mb-3",
                        ),
                        dbc.Button(
                            "Start Stream",
                            id="start-stream",
                            color="success",
                            className="mb-2 w-100",
                        ),
                        dbc.Button(
                            "Stop Stream",
                            id="stop-stream",
                            color="danger",
                            className="mb-2 w-100",
                        ),
                        dbc.Row(
                            [
                                dbc.Col(),
                                dbc.Col(
                                    dbc.Button(
                                        "↑", id="move-up", color="primary", size="lg"
                                    ),
                                    width="auto",
                                ),
                                dbc.Col(),
                            ],
                            className="mb-2 text-center",
                        ),
                        dbc.Row(
                            [
                                dbc.Col(
                                    dbc.Button(
                                        "←", id="move-left", color="primary", size="lg"
                                    ),
                                    width="auto",
                                ),
                                dbc.Col(
                                    dbc.Button(
                                        "STOP",
                                        id="stop-move",
                                        color="danger",
                                        size="lg",
                                    ),
                                    width="auto",
                                ),
                                dbc.Col(
                                    dbc.Button(
                                        "→", id="move-right", color="primary", size="lg"
                                    ),
                                    width="auto",
                                ),
                            ],
                            className="mb-2 text-center",
                        ),
                        dbc.Row(
                            [
                                dbc.Col(),
                                dbc.Col(
                                    dbc.Button(
                                        "↓", id="move-down", color="primary", size="lg"
                                    ),
                                    width="auto",
                                ),
                                dbc.Col(),
                            ],
                            className="mb-3 text-center",
                        ),
                        html.Label("Zoom Level:"),
                        dcc.Slider(
                            id="zoom-slider",
                            min=0,
                            max=64,
                            step=1,
                            marks={0: "0", 32: "32", 64: "64"},
                            value=32,
                        ),
                        dbc.Button(
                            "Set Zoom",
                            id="set-zoom",
                            color="success",
                            className="mb-2 w-100",
                        ),
                    ],
                    md=4,
                ),
            ],
            className="mb-4",
        ),
        html.Div(
            id="output-message",
            className="text-center",
            style={"fontWeight": "bold"},
        ),
        html.Div(
            id="click-coordinates",
            className="text-center",
            style={"fontWeight": "bold", "color": "green"},
        ),
        dcc.Store(id="click-coords"),
    ],
    fluid=True,
)

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


# 📌 Combined Callback for Stream, Movement & Zoom
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
        Input("set-zoom", "n_clicks"),
    ],
    [State("camera-select", "value"), State("zoom-slider", "value")],
)
def control_camera(
    start_stream, stop_stream, up, down, left, right, stop, zoom, camera_id, zoom_level
):
    ctx = dash.callback_context
    if not ctx.triggered:
        return ""

    button_id = ctx.triggered[0]["prop_id"].split(".")[0]

    # Mapping buttons to API endpoints
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
        return send_api_request(
            f"/move/{camera_id}/{direction}"
            if direction != "Stop"
            else f"/stop/{camera_id}"
        )

    elif button_id == "set-zoom":
        return send_api_request(f"/zoom/{camera_id}/{zoom_level}")

    return ""


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
