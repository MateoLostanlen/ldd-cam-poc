# 🔥 Reolink Camera Control & Visualization

This repository contains two main components:

1. A **FastAPI backend**, to be run on a Raspberry Pi connected to a Reolink PTZ camera, which handles camera control and video streaming.
2. A **Dash-based frontend demo**, which connects to the Pi and lets you control the camera via a simple web interface.

---

## 📸 Step 1 – Run the FastAPI backend on the Raspberry Pi

The FastAPI app is responsible for controlling the Reolink camera and managing live streaming via MediaMTX.

👉 **Follow the instructions in [`pi_manager/README.md`](pi_manager/README.md)** to:

- Install MediaMTX on your Pi
- Configure camera connection
- Run the FastAPI server in the background

Once running, the API will be accessible at:

```
http://<pi_ip>:8000
```

You can test it via Swagger UI:  
`http://<pi_ip>:8000/docs`

---

## 💻 Step 2 – Run the Dash demo app (on your local machine)

This is the visualization and control interface for your camera.

### 1. Register the Raspberry Pi IP

Open the file:

```
platform/app.py
```

And replace the `PI_IP` variable with the IP address of your Raspberry Pi:

```python
PI_IP = "http://<your-pi-ip>:8000"
```

---

### 2. Install dependencies

Make sure you’re in the `platform/` directory, then install the required Python packages:

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

You should see the demo interface to control your camera via the FastAPI backend running on the Pi.

---

## ✅ Requirements

- Raspberry Pi connected to Reolink PTZ camera
- Python 3.11+
- Local machine for running the Dash demo
