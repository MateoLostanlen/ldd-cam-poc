# 🔥 Reolink Camera Control & Visualization

This repository contains two main components:

1. A **FastAPI backend**, running on a Raspberry Pi connected to a Reolink PTZ camera, handling camera control and live streaming with FFmpeg.
2. A **Dash-based frontend app**, providing an easy web interface to control the camera remotely.

---

## 📸 Step 1 – Run the FastAPI backend on the Raspberry Pi

The FastAPI app is responsible for controlling the Reolink camera and managing the video stream using **FFmpeg** (no MediaMTX required).

👉 **To set it up:**

- Install `ffmpeg` on the Pi.
- Configure your `.env` file with the camera login details.
- Launch the FastAPI server.

Once running, the API will be accessible at:

```
http://<pi_ip>:8000
```

You can interact with the API via Swagger UI at:

```
http://<pi_ip>:8000/docs
```

---

## 💻 Step 2 – Run the Dash frontend (on your local machine)

This is the visualization and remote control interface for your camera.

### 1. Set the Raspberry Pi IP

Open the file:

```
platform/app.py
```

And update the Pi IP address:

```python
TARGET_IP = "<your-pi-ip>"
```

---

### 2. Install dependencies

From the `platform/` folder, install Python packages:

```bash
pip install -r requirements.txt
```

---

### 3. Run the Dash app

```bash
python app.py
```

Then open your browser at:

```
http://127.0.0.1:8050
```

You will be able to view the video stream and control the camera movements and zoom.

---

## ✅ Requirements

- Raspberry Pi connected to a Reolink PTZ camera
- Python 3.11+
- FFmpeg installed on the Raspberry Pi
- Local machine to run the Dash frontend
