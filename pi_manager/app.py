import logging
import subprocess
import threading
import time

import requests
import urllib3
from fastapi import FastAPI

app = FastAPI()
processes = {}  # Store MediaMTX processes
last_command_time = time.time()  # Track the last command time
timer_thread = None  # Background thread for checking inactivity

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
logging.basicConfig(level=logging.DEBUG)

# Camera credentials
CAMERAS = {
    "cam1": {"ip": "169.254.40.1", "username": "admin", "password": "***"},
    "cam2": {"ip": "169.254.40.2", "username": "admin", "password": "***"},
}

# MediaMTX config files
CONFIG_FILES = {
    "cam1": "/home/pi/mediamtx/mediamtx_1_main.yml",
    "cam2": "/home/pi/mediamtx/mediamtx_2_main.yml",
}


class ReolinkCamera:
    """Class to control a Reolink camera."""

    def __init__(
        self, ip_address: str, username: str, password: str, protocol: str = "https"
    ):
        self.ip_address = ip_address
        self.username = username
        self.password = password
        self.protocol = protocol

    def _build_url(self, command: str) -> str:
        """Builds the request URL for the camera API."""
        return f"{self.protocol}://{self.ip_address}/cgi-bin/api.cgi?cmd={command}&user={self.username}&password={self.password}&channel=0"

    def move_camera(self, operation: str, speed: int = 10):
        """Moves the camera in a given direction."""
        url = self._build_url("PtzCtrl")
        data = [
            {
                "cmd": "PtzCtrl",
                "action": 0,
                "param": {"channel": 0, "op": operation, "speed": speed},
            }
        ]
        response = requests.post(url, json=data, verify=False)
        return response.json() if response.status_code == 200 else None

    def stop_camera(self):
        """Stops the camera movement."""
        return self.move_camera("Stop")

    def zoom(self, position: int):
        """Adjusts the zoom level of the camera."""
        url = self._build_url("StartZoomFocus")
        data = [
            {
                "cmd": "StartZoomFocus",
                "action": 0,
                "param": {
                    "ZoomFocus": {"channel": 0, "pos": position, "op": "ZoomPos"}
                },
            }
        ]
        response = requests.post(url, json=data, verify=False)
        return response.json() if response.status_code == 200 else None


def is_process_running(proc):
    """Check if a process is still running."""
    return proc and proc.poll() is None


def stop_any_running_stream():
    """Stops any currently running stream."""
    for cam_id, proc in list(processes.items()):
        if is_process_running(proc):
            proc.terminate()  # Graceful shutdown
            proc.wait()  # Wait for termination
            del processes[cam_id]  # Remove from tracking
            return cam_id  # Return the stopped stream


def stop_stream_if_idle():
    """Background task that stops the stream if no command is received for 60 seconds."""
    global last_command_time
    while True:
        time.sleep(60)  # Check every 60 seconds
        if time.time() - last_command_time > 60:
            stopped_cam = stop_any_running_stream()
            if stopped_cam:
                logging.info(f"Stream for {stopped_cam} stopped due to inactivity")


# Start the background thread for monitoring inactivity
timer_thread = threading.Thread(target=stop_stream_if_idle, daemon=True)
timer_thread.start()


@app.post("/start_stream/{camera_id}")
async def start_stream(camera_id: str):
    """Starts a MediaMTX stream for a given camera, stopping any active stream first."""
    global last_command_time
    last_command_time = time.time()  # Update last command time

    if camera_id not in CONFIG_FILES:
        return {"error": "Invalid camera ID. Use 'cam1' or 'cam2'."}

    # Stop any existing stream before starting a new one
    stopped_cam = stop_any_running_stream()

    config_file = CONFIG_FILES[camera_id]
    processes[camera_id] = subprocess.Popen(
        ["mediamtx", config_file], stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )

    return {
        "message": f"Stream for {camera_id} started",
        "previous_stream": (
            stopped_cam if stopped_cam else "No previous stream was running"
        ),
    }


@app.post("/stop_stream")
async def stop_stream():
    """Stops any active stream."""
    global last_command_time
    last_command_time = time.time()  # Update last command time

    stopped_cam = stop_any_running_stream()
    if stopped_cam:
        return {"message": f"Stream for {stopped_cam} stopped"}
    return {"message": "No active stream was running"}


@app.get("/status")
async def stream_status():
    """Returns which stream is currently running."""
    global last_command_time
    last_command_time = time.time()  # Update last command time

    active_streams = [
        cam_id for cam_id, proc in processes.items() if is_process_running(proc)
    ]
    if active_streams:
        return {"active_streams": active_streams}
    return {"message": "No stream is running"}


@app.post("/move/{camera_id}/{direction}")
async def move_camera(camera_id: str, direction: str):
    """Moves the camera in the specified direction (Up, Right, Down, Left)."""
    global last_command_time
    last_command_time = time.time()  # Update last command time

    if camera_id not in CAMERAS:
        return {"error": "Invalid camera ID. Use 'cam1' or 'cam2'."}

    cam = ReolinkCamera(
        CAMERAS[camera_id]["ip"],
        CAMERAS[camera_id]["username"],
        CAMERAS[camera_id]["password"],
    )
    cam.move_camera(direction, speed=5)
    return {"message": f"Camera {camera_id} moved {direction} at speed 5"}


@app.post("/stop/{camera_id}")
async def stop_camera(camera_id: str):
    """Stops the camera movement."""
    global last_command_time
    last_command_time = time.time()  # Update last command time

    if camera_id not in CAMERAS:
        return {"error": "Invalid camera ID. Use 'cam1' or 'cam2'."}

    cam = ReolinkCamera(
        CAMERAS[camera_id]["ip"],
        CAMERAS[camera_id]["username"],
        CAMERAS[camera_id]["password"],
    )
    cam.stop_camera()
    return {"message": f"Camera {camera_id} stopped moving"}


@app.post("/zoom/{camera_id}/{level}")
async def zoom_camera(camera_id: str, level: int):
    """Adjusts the camera zoom level (0 to 64)."""
    global last_command_time
    last_command_time = time.time()  # Update last command time

    if camera_id not in CAMERAS:
        return {"error": "Invalid camera ID. Use 'cam1' or 'cam2'."}

    if not (0 <= level <= 64):
        return {"error": "Zoom level must be between 0 and 64."}

    cam = ReolinkCamera(
        CAMERAS[camera_id]["ip"],
        CAMERAS[camera_id]["username"],
        CAMERAS[camera_id]["password"],
    )
    cam.zoom(level)
    return {"message": f"Camera {camera_id} zoom set to {level}"}
