import json

import requests
from fastapi import FastAPI, HTTPException

# File path for storing Pi mappings
PI_FILE = "pi_servers.json"

app = FastAPI()


# Load Raspberry Pi mappings from JSON file
def load_pi_mappings():
    """Load the Raspberry Pi IP mappings from a JSON file."""
    try:
        with open(PI_FILE, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


# Save Raspberry Pi mappings to JSON file
def save_pi_mappings(data):
    """Save updated Raspberry Pi IP mappings to a JSON file."""
    with open(PI_FILE, "w") as f:
        json.dump(data, f, indent=4)


# Store active Raspberry Pi selection per session
active_sessions = {}


@app.post("/select_pi/{pi_name}")
async def select_pi(pi_name: str):
    """Set the target Raspberry Pi for the session"""
    pi_servers = load_pi_mappings()

    if pi_name not in pi_servers or pi_servers[pi_name] is None:
        raise HTTPException(status_code=400, detail="Invalid or missing IP for this Pi")

    active_sessions["selected_pi"] = pi_name
    return {"message": f"Selected Pi: {pi_name} ({pi_servers[pi_name]})"}


@app.post("/{command:path}")
async def proxy_command(command: str):
    """Forwards commands to the selected Raspberry Pi"""
    if "selected_pi" not in active_sessions:
        raise HTTPException(
            status_code=400, detail="No Pi selected. Use /select_pi/{pi_name} first."
        )

    pi_servers = load_pi_mappings()
    selected_pi = active_sessions["selected_pi"]
    pi_ip = pi_servers[selected_pi]

    try:
        response = requests.post(f"http://{pi_ip}:8000/{command}")
        return response.json()
    except requests.exceptions.RequestException:
        raise HTTPException(
            status_code=500, detail="Could not reach the selected Raspberry Pi"
        )


@app.post("/update_pi/{pi_name}/{ip}")
async def update_pi_mapping(pi_name: str, ip: str):
    """Update the Raspberry Pi IP mapping and save to file."""
    pi_servers = load_pi_mappings()
    pi_servers[pi_name] = ip
    save_pi_mappings(pi_servers)
    return {"message": f"Updated {pi_name} to {ip}"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
