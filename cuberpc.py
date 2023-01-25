# Copyright 2023 iiPython

# Modules
import os
import rel
import json
import websocket
from typing import Any
from datetime import datetime
from pypresence import Presence

# Load configuration
config_files, config = [
    "/etc/cuberpc/config.json",
    os.path.join(os.path.dirname(__file__), "config.json")
], {}
for file in config_files:
    if not os.path.isfile(file):
        continue

    try:
        with open(file, "r") as fh:
            config = json.loads(fh.read())

    except Exception:
        pass

# Initialization
def log(state: str, message: str) -> None:
    time = datetime.now().strftime("%D %I:%M:%S %p")
    print(f"[{state.upper()} {time}]: {message}")

log("info", "Connecting to discord RPC!")
try:
    rpc = Presence(config["client_id"], pipe = config.get("pipe", 0))
    rpc.connect()

except IndexError:
    log("error", "Configuration file requires a discord app client ID!")
    exit(1)

except Exception as m:
    log("error", m)
    exit(1)

# Callbacks
def on_message(ws: websocket.WebSocketApp, m: Any):
    m = json.loads(m)
    if m["name"] != "playback_overview_changed":
        return

    log("debug", m)
    metadata = m["options"]["playing_track"]
    if m["options"]["state"] == "paused":
        pass

    elif m["options"]["state"] == "playing":
        pass

    else:
        log("error", f"Unknown state '{m['options']['state']}'!")

    rpc.update(
        details = metadata["title"],
        state = f"{metadata['artist']} - {metadata['album']}"
    )

def on_error(ws: websocket.WebSocketApp, m: Any):
    log("error", m)

def on_close(ws: websocket.WebSocketApp, ec: int, m: Any):
    log("warn", f"MusikCube closed connection with status code {ec}; message: '{m}'")

def on_open(ws):
    ws.send({
        "name": "authenticate",
        "type": "request",
        "id": "cuberpc",
        "device_id": "cuberpc",
        "options": {"password": config.get("password")}
    })

# CubeRPC Connection
if __name__ == "__main__":

    # Connect to Musikcube
    ws = websocket.WebSocketApp(
        f"ws://localhost:{config.get('port', 7905)}",
        on_open = on_open,
        on_message = on_message,
        on_error = on_error,
        on_close = on_close
    )
    ws.run_forever(dispatcher = rel, reconnect = 5)
    rel.signal(2, rel.abort)
    rel.dispatch()
