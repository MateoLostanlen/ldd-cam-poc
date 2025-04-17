# Reolink Camera Stream Controller

This FastAPI app lets you control Reolink cameras (PTZ, zoom) and manage live streams using [MediaMTX](https://github.com/bluenviron/mediamtx). It supports two cameras (`cam1` and `cam2`), and automatically stops inactive streams after 60 seconds.

---

## 🛠 Installation

### 1. Install MediaMTX

**For Linux (x86_64):**

```bash
wget https://github.com/bluenviron/mediamtx/releases/download/v1.11.3/mediamtx_v1.11.3_linux_amd64.tar.gz
tar -xvzf mediamtx_v1.11.3_linux_amd64.tar.gz
sudo mv mediamtx /usr/local/bin/
```

**For Raspberry Pi (ARM64):**

```bash
wget https://github.com/bluenviron/mediamtx/releases/download/v1.11.3/mediamtx_v1.11.3_linux_arm64v8.tar.gz
tar -xvzf mediamtx_v1.11.3_linux_arm64v8.tar.gz
sudo mv mediamtx /usr/local/bin/
```

### 2. Prepare MediaMTX Config Files

Make sure you have your MediaMTX configuration files for each camera:

- `cam1`: `/home/pi/ldd-cam-poc/pi_manager/mediamtx_1_main.yml`
- `cam2`: `/home/pi/ldd-cam-poc/pi_manager/mediamtx_2_main.yml`

Here is an example:

```yml
paths:
  cam:
    source: rtsp://admin:@Pyronear@169.254.40.1:554/h264Preview_01_main
    sourceOnDemand: yes       # Fetch the source only when there's a viewer
```

You can test the config directly by running:

```bash
mediamtx /home/pi/ldd-cam-poc/pi_manager/mediamtx_1_main.yml
```

---

## 🚀 Run the App

Set config file to config.yaml
```yaml
cameras:
  cam1:
    ip: 169.254.40.1
    username: login
    password: "***"
  cam2:
    ip: 169.254.40.2
    username: login
    password: "***"

config_files:
  cam1: /home/pi/ldd-cam-poc/pi_manager/mediamtx_1_main.yml
  cam2: /home/pi/ldd-cam-poc/pi_manager/mediamtx_2_main.yml
```

Start the FastAPI server with:

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

or run it background

```bash
screen -S reolink-app
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

---

## 📡 API Endpoints

### Stream Control

- `POST /start_stream/{camera_id}` – Start stream for `cam1` or `cam2`
- `POST /stop_stream` – Stop any active stream
- `GET /status` – Get the current stream status

### Camera Control

- `POST /move/{camera_id}/{direction}` – Move PTZ camera (`Up`, `Down`, `Left`, `Right`)
- `POST /stop/{camera_id}` – Stop camera movement
- `POST /zoom/{camera_id}/{level}` – Set zoom level (0 to 64)

---

## 🔒 Notes

- Cameras use HTTPS and disable SSL verification for API calls.
- Only one stream can run at a time. Starting a new one will stop the previous.
- Streams are stopped automatically after 60 seconds of inactivity.

