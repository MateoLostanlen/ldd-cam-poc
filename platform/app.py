import dash
import dash_bootstrap_components as dbc
import requests
from dash import Input, Output, State, dcc, html

pyro_logo = "https://pyronear.org/img/logo_letters_orange.png"

TARGET_IP = "192.168.255.146"

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
        html.H3("Live Camera Feed", className="text-center mb-3"),
        html.Iframe(
            src=f"http://{TARGET_IP}:8889/cam",
            style={
                "width": "100%",
                "height": "500px",
                "border": "none",
                "borderRadius": "10px",
            },
            className="mb-4 shadow-sm",
        ),
        html.H4("Stream & Camera Controls", className="text-center mt-3"),
        # Camera Selection Dropdown
        dbc.Row(
            [
                dbc.Col(html.Label("Select Camera:"), width=2),
                dbc.Col(
                    dcc.Dropdown(
                        id="camera-select",
                        options=[
                            {"label": name, "value": cam_id}
                            for name, cam_id in CAMERAS.items()
                        ],
                        value="cam1",
                        clearable=False,
                    ),
                    width=4,
                ),
            ],
            className="mb-3",
        ),
        # Start/Stop Stream Buttons
        dbc.Row(
            [
                dbc.Col(
                    dbc.Button("Start Stream", id="start-stream", color="success"),
                    width=3,
                ),
                dbc.Col(
                    dbc.Button("Stop Stream", id="stop-stream", color="danger"), width=3
                ),
            ],
            className="mb-3 text-center",
        ),
        # PTZ Control Buttons
        dbc.Row(
            [
                dbc.Col(width=3),
                dbc.Col(
                    dbc.Button("↑", id="move-up", color="primary", size="lg"), width=2
                ),
                dbc.Col(width=3),
            ],
            className="mb-2 text-center",
        ),
        dbc.Row(
            [
                dbc.Col(
                    dbc.Button("←", id="move-left", color="primary", size="lg"),
                    width=2,
                    className="text-right",
                ),
                dbc.Col(
                    dbc.Button("STOP", id="stop-move", color="danger", size="lg"),
                    width=2,
                    className="text-center",
                ),
                dbc.Col(
                    dbc.Button("→", id="move-right", color="primary", size="lg"),
                    width=2,
                    className="text-left",
                ),
            ],
            className="mb-2 text-center",
        ),
        dbc.Row(
            [
                dbc.Col(width=3),
                dbc.Col(
                    dbc.Button("↓", id="move-down", color="primary", size="lg"), width=2
                ),
                dbc.Col(width=3),
            ],
            className="mb-3 text-center",
        ),
        # Zoom Slider
        html.Label("Zoom Level:", className="mt-3"),
        dcc.Slider(
            id="zoom-slider",
            min=0,
            max=64,
            step=1,
            marks={0: "0", 32: "32", 64: "64"},
            value=32,
        ),
        dbc.Button("Set Zoom", id="set-zoom", color="success", className="mt-2"),
        # Output message
        html.Div(
            id="output-message",
            className="mt-3 text-center",
            style={"fontWeight": "bold"},
        ),
    ],
    fluid=True,
)


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


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8050)
