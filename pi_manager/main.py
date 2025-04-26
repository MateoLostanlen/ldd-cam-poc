import logging
import subprocess
import threading
import time
import yaml
import requests
import urllib3
from fastapi import FastAPI

app = FastAPI()
processes = {}  # Store FFmpeg processes
last_command_time = time.time()  # Track the last command time
timer_thread = None  # Background thread for checking inactivity

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
logging.basicConfig(level=logging.DEBUG)

# Load the YAML configuration file
with open("config.yaml", "r") as file:
    config = yaml.safe_load(file)

# Access the data
CAMERAS = config["cameras"]
STREAMS = config["streams"]  # New structure: streams settings

class ReolinkCamera:
    """Class to control a Reolink camera."""

    def __init__(self, ip_address: str, username: str, password: str, protocol: str = "https"):
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
        data = [{"cmd": "PtzCtrl", "action": 0, "param": {"channel": 0, "op": operation, "speed": speed}}]
        response = requests.post(url, json=data, verify=False)
        return response.json() if response.status_code == 200 else None

    def stop_camera(self):
        """Stops the camera movement."""
        return self.move_camera("Stop")

    def zoom(self, position: int):
        """Adjusts the zoom level of the camera."""
        url = self._build_url("StartZoomFocus")
        data = [{"cmd": "StartZoomFocus", "action": 0, "param": {"ZoomFocus": {"channel": 0, "pos": position, "op": "ZoomPos"}}}]
        response = requests.post(url, json=data, verify=False)
        return response.json() if response.status_code == 200 else None


def is_process_running(proc):
    """Check if a process is still running."""
    return proc and proc.poll() is None

def stop_any_running_stream():
    """Stops any currently running stream."""
    for cam_id, proc in list(processes.items()):
        if is_process_running(proc):
            proc.terminate()
            proc.wait()
            del processes[cam_id]
            return cam_id
    return None

def stop_stream_if_idle():
    """Background task that stops the stream if no command is received for 60 seconds."""
    global last_command_time
    while True:
        time.sleep(60)
        if time.time() - last_command_time > 60:
            stopped_cam = stop_any_running_stream()
            if stopped_cam:
                logging.info(f"Stream for {stopped_cam} stopped due to inactivity")

# Start background thread
timer_thread = threading.Thread(target=stop_stream_if_idle, daemon=True)
timer_thread.start()


@app.post("/start_stream/{camera_id}")
async def start_stream(camera_id: str):
    """Starts an FFmpeg stream for a given camera."""
    global last_command_time
    last_command_time = time.time()

    if camera_id not in STREAMS:
        return {"error": "Invalid camera ID."}

    # Stop any existing stream
    stopped_cam = stop_any_running_stream()

    stream_info = STREAMS[camera_id]
    input_url = stream_info["input_url"]
    output_url = stream_info["output_url"]

    command = [
        "ffmpeg",
        "-fflags", "discardcorrupt+nobuffer",  # Ignorer paquets corrompus, réduire bufferisation
        "-flags", "low_delay",                 # Mode faible latence
        "-rtsp_transport", "udp",               # RTSP en UDP (plus rapide mais risque de pertes)
        "-i", input_url,                        # URL RTSP de la caméra
        "-c:v", "libx264",                      # Encoder vidéo en H.264 (x264)
        "-bf", "0",                              # Pas de B-frames (IP only) pour réduire la latence
        "-b:v", "500k",                         # Bitrate vidéo à 500 kbps
        "-r", "15",                             # Framerate à 10 fps
        "-preset", "veryfast",                  # Preset x264 rapide (faible usage CPU)
        "-tune", "zerolatency",                 # Optimisation x264 pour la latence minimale
        "-s", "640x360",                        # Redimensionner la vidéo en 640x360
        "-an",                                  # Supprimer l'audio
        "-f", "mpegts",                         # Format de sortie MPEG-TS (nécessaire pour SRT)
        output_url                              # URL de destination SRT
    ]



    processes[camera_id] = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    return {
        "message": f"Stream for {camera_id} started",
        "previous_stream": (stopped_cam if stopped_cam else "No previous stream was running"),
    }


@app.post("/stop_stream")
async def stop_stream():
    """Stops any active stream."""
    global last_command_time
    last_command_time = time.time()

    stopped_cam = stop_any_running_stream()
    if stopped_cam:
        return {"message": f"Stream for {stopped_cam} stopped"}
    return {"message": "No active stream was running"}


@app.get("/status")
async def stream_status():
    """Returns which stream is currently running."""
    global last_command_time
    last_command_time = time.time()

    active_streams = [cam_id for cam_id, proc in processes.items() if is_process_running(proc)]
    if active_streams:
        return {"active_streams": active_streams}
    return {"message": "No stream is running"}



@app.post("/move/{camera_id}/{direction}/{speed}")
async def move_camera(camera_id: str, direction: str, speed: int):
    """Moves the camera in the specified direction (Up, Right, Down, Left) with a given speed."""
    global last_command_time
    last_command_time = time.time()  # Update last command time

    if camera_id not in CAMERAS:
        return {"error": "Invalid camera ID. Use 'cam1' or 'cam2'."}

    cam = ReolinkCamera(
        CAMERAS[camera_id]["ip"],
        CAMERAS[camera_id]["username"],
        CAMERAS[camera_id]["password"],
    )
    cam.move_camera(direction, speed=speed)
    return {"message": f"Camera {camera_id} moved {direction} at speed {speed}"}


@app.post("/stop/{camera_id}")
async def stop_camera(camera_id: str):
    """Stops the camera movement."""
    global last_command_time
    last_command_time = time.time()

    if camera_id not in CAMERAS:
        return {"error": "Invalid camera ID."}

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
    last_command_time = time.time()

    if camera_id not in CAMERAS:
        return {"error": "Invalid camera ID."}

    if not (0 <= level <= 64):
        return {"error": "Zoom level must be between 0 and 64."}

    cam = ReolinkCamera(
        CAMERAS[camera_id]["ip"],
        CAMERAS[camera_id]["username"],
        CAMERAS[camera_id]["password"],
    )
    cam.zoom(level)
    return {"message": f"Camera {camera_id} zoom set to {level}"}