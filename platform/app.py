import dash
import dash_bootstrap_components as dbc
import requests
from dash import Input, Output, State, dcc, html
from dash_extensions import EventListener
import numpy as np

pyro_logo = "https://pyronear.org/img/logo_letters_orange.png"

TARGET_IP = "192.168.1.28"

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
                                        src=f"http://91.134.47.14:8889/mateostream/",
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
                        html.Hr(),
                        html.H5("Calibration Points", className="text-center mb-3"),
                        html.Div(id="calibration-table"),

                        dbc.Button("Set Point 1", id="set-point1", color="primary", className="mb-2 w-100"),
                        dbc.Button("Random Move", id="random-move", color="info", className="mb-2 w-100"),
                        dbc.Button("Set Point 2", id="set-point2", color="success", className="mb-2 w-100"),
                        dbc.Button("Compute Speeds", id="compute-speeds", color="warning", className="mb-2 w-100"),
                        html.Div(id="calibration-status", className="text-center", style={"fontWeight": "bold"}),
                        dcc.Store(id="calibration-store", data={"mode": "idle", "current_point": {}, "point_values": []}),



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
                        dbc.Row(
                        [
                            dbc.Col(dbc.Button("Switch Mode", id="switch-mode", color="secondary")),
                            dbc.Col(html.Div(id="current-mode", className="mt-2")),
                        ],
                        className="mb-3",
                    ),

                    dcc.Store(id="mode-store", data="move"),  # Initial mode is 'move'

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
            f"/move/{camera_id}/{direction}/3"
            if direction != "Stop"
            else f"/stop/{camera_id}"
        )

    elif button_id == "set-zoom":
        return send_api_request(f"/zoom/{camera_id}/{zoom_level}")

    return ""

@app.callback(
    Output("mode-store", "data"),
    Output("current-mode", "children"),
    Input("switch-mode", "n_clicks"),
    State("mode-store", "data"),
    prevent_initial_call=True
)
def toggle_mode(n_clicks, current_mode):
    if current_mode == "move":
        return "point", "🟢 Mode: Point (display only)"
    else:
        return "move", "🔵 Mode: Move (click to move camera)"

@app.callback(
    Output("click-coordinates", "children"),
    Input("click-coords", "data"),
    State("camera-select", "value"),
    State("mode-store", "data"),
    prevent_initial_call=True,
)
def show_coords(data, camera_id, mode):
    if not data:
        return ""

    x_percent = round((data["offsetX"] / data["width"]) * 100, 2)
    y_percent = round((data["offsetY"] / data["height"]) * 100, 2)

    if mode == "point":
        return f"📍 Clicked at x={data['offsetX']}px ({x_percent}%), y={data['offsetY']}px ({y_percent}%) [Point Mode]"

    # Move mode
    try:
        response = requests.post(
            f"http://{TARGET_IP}:8000/move_to/{camera_id}",
            json={"x": x_percent, "y": y_percent},
            timeout=30,
        )
        if response.status_code == 200:
            move_result = response.json()
            return (
                f"📍 Clicked at x={data['offsetX']}px ({x_percent}%), "
                f"y={data['offsetY']}px ({y_percent}%) → 📡 Moving camera.\n"
                f"✅ Server: {move_result.get('message')}"
            )
        else:
            return f"⚠️ Click registered, but move failed: {response.status_code}"
    except Exception as e:
        return f"⚠️ Click registered, but move request failed: {str(e)}"

import random
import time

from dash import dash_table


@app.callback(
    Output("calibration-table", "children"),
    Input("calibration-store", "data"),
)
def update_calibration_table(calib_data):
    point_values = calib_data.get("point_values", [])

    if not point_values:
        return html.P("No points collected yet.", style={"textAlign": "center", "color": "gray"})

    # Format for Dash DataTable
    rows = []
    for x0, y0, x1, y1, th, tv in point_values:
        rows.append({
            "x0 (%)": f"{x0:.2f}",
            "y0 (%)": f"{y0:.2f}",
            "x1 (%)": f"{x1:.2f}",
            "y1 (%)": f"{y1:.2f}",
            "Δx (%)": f"{(x1-x0):.2f}",
            "Δy (%)": f"{(y1-y0):.2f}",
            "th (s)": f"{th:.2f}",
            "tv (s)": f"{tv:.2f}",
        })

    return dash_table.DataTable(
        columns=[{"name": col, "id": col} for col in rows[0].keys()],
        data=rows,
        style_table={"overflowX": "auto"},
        style_cell={"textAlign": "center", "padding": "5px"},
        style_header={"backgroundColor": "#eee", "fontWeight": "bold"},
        page_size=10,
    )


import numpy as np

def random_horizontal_move(camera_id):
    th = random.uniform(1, 3)
    horiz = random.choice(["Left", "Right"])
    send_api_request(f"/move/{camera_id}/{horiz}/3")  # speed=3 for horizontal
    time.sleep(th)
    send_api_request(f"/stop/{camera_id}")
    return th

def random_vertical_move(camera_id):
    tv = random.uniform(1, 3)
    vert = random.choice(["Up", "Down"])
    send_api_request(f"/move/{camera_id}/{vert}/2")  # speed=2 for vertical
    time.sleep(tv)
    send_api_request(f"/stop/{camera_id}")
    return tv



def estimate_speed_and_reaction(point_values):
    fov_x = 54.2  # Horizontal FOV in degrees
    fov_y = 44    # Vertical FOV in degrees

    vxs = []
    vys = []

    for x0, y0, x1, y1, th, tv in point_values:
        dx = abs(x1 - x0)
        dy = abs(y1 - y0)

        vx = dx / th if th > 0 else 0  # %/s
        vy = dy / tv if tv > 0 else 0  # %/s

        vxs.append(vx)
        vys.append(vy)

    avg_vx_percent = np.mean(vxs)
    avg_vy_percent = np.mean(vys)

    avg_vx_deg = avg_vx_percent * (fov_x / 100)  # convert %/s -> °/s
    avg_vy_deg = avg_vy_percent * (fov_y / 100)  # convert %/s -> °/s

    return avg_vx_deg, avg_vy_deg



# Main callback
@app.callback(
    Output("calibration-store", "data"),
    Output("calibration-status", "children"),
    Input("set-point1", "n_clicks"),
    Input("random-move", "n_clicks"),
    Input("set-point2", "n_clicks"),
    Input("compute-speeds", "n_clicks"),
    Input("click-coords", "data"),
    State("calibration-store", "data"),
    State("camera-select", "value"),
    prevent_initial_call=True,
)
def calibration_process(set_p1, move_click, set_p2, compute_click, click_data, calib_data, camera_id):
    ctx = dash.callback_context
    if not ctx.triggered:
        return dash.no_update, dash.no_update

    triggered = ctx.triggered[0]["prop_id"].split(".")[0]
    mode = calib_data["mode"]
    current_point = calib_data.get("current_point", {})
    point_values = calib_data.get("point_values", [])

    if triggered == "set-point1":
        return {"mode": "waiting_point1", "current_point": {}, "point_values": point_values}, "🖱️ Click to set reference point (x0, y0)."

    elif triggered == "random-move":
        if "x0" not in current_point:
            return dash.no_update, "⚠️ You must set Point 1 first!"
        th = random_horizontal_move(camera_id)
        tv = random_vertical_move(camera_id)

        current_point["th"] = th
        current_point["tv"] = tv
        return {"mode": "moving_done", "current_point": current_point, "point_values": point_values}, f"📡 Move done: th={th:.2f}s, tv={tv:.2f}s. Now set Point 2."

    elif triggered == "set-point2":
        if "th" not in current_point:
            return dash.no_update, "⚠️ You must move the camera first!"
        return {"mode": "waiting_point2", "current_point": current_point, "point_values": point_values}, "🖱️ Click to set after-move point (x1, y1)."

    elif triggered == "click-coords" and click_data:
        x = round((click_data["offsetX"] / click_data["width"]) * 100, 2)
        y = round((click_data["offsetY"] / click_data["height"]) * 100, 2)

        if mode == "waiting_point1":
            current_point["x0"] = x
            current_point["y0"] = y
            return {"mode": "idle", "current_point": current_point, "point_values": point_values}, f"✅ Reference Point set at ({x:.2f}%, {y:.2f}%)."

        elif mode == "waiting_point2":
            if "x0" not in current_point or "th" not in current_point:
                return dash.no_update, "⚠️ Missing data, restart calibration!"
            x0 = current_point["x0"]
            y0 = current_point["y0"]
            th = current_point["th"]
            tv = current_point["tv"]
            x1 = x
            y1 = y
            point_values.append((x0, y0, x1, y1, th, tv))
            print("POINT_VALUES", point_values)
            return {"mode": "idle", "current_point": {}, "point_values": point_values}, f"✅ Point added: Δx={(x1-x0):.2f}%, Δy={(y1-y0):.2f}%."

    elif triggered == "compute-speeds":
        if not point_values:
            return {"mode": "idle", "current_point": {}, "point_values": []}, "⚠️ No points collected."

        # Use the new estimation
        vx_deg, vy_deg = estimate_speed_and_reaction(point_values)

        return {"mode": "idle", "current_point": {}, "point_values": point_values}, (
            f"✅ Estimated Speeds:\n"
            f"Horizontal: {vx_deg:.2f}°/s\n"
            f"Vertical: {vy_deg:.2f}°/s"
        )


    return dash.no_update, dash.no_update


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8050)
