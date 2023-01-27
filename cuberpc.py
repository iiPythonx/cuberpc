# Copyright 2023 iiPython

# Modules
import os
import rel
import time
import json
import requests
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

# Sane defaults
albumartserver = config.get("albumserve", "albumart.iipython.cf")
musikcube_info = config.get("musikcube", {
    "metaport": 7905,
    "streamport": 7906,
    "password": None
})

# Initialization
album_cache = {}

def log(state: str, message: str) -> None:
    time = datetime.now().strftime("%D %I:%M:%S %p")
    print(f"[{state.upper()} {time}]: {message}")

def get_album_art_link(author: str, album: str, thumb_id: int) -> str:
    if thumb_id in album_cache:
        return album_cache[thumb_id]

    try:
        return requests.post(
            f"http://{albumartserver}/upload",
            data = {"id": f"{author} - {album}.jpg"},
            files = {"thumb": requests.get(
                f"http://localhost:{musikcube_info.get('streamport', 7906)}/thumbnail/{thumb_id}",
                auth = ("default", musikcube_info.get("password") or "")
            ).content}
        ).text

    except Exception:
        return "unknown"

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
    log("debug", m)
    if m["name"] != "playback_overview_changed":
        return

    metadata = m["options"]["playing_track"]
    if m["options"]["state"] not in ["paused", "playing"]:
        return rpc.clear()

    t = time.time()
    album_link = get_album_art_link(metadata["artist"], metadata["album"], metadata["thumbnail_id"])
    rpc.update(
        details = metadata["title"],
        state = f"{metadata['artist']} - {metadata['album']}",
        large_image = album_link,
        large_text = metadata["album"],
        start = t,
        end = t + (m["options"]["playing_duration"] - m["options"]["playing_current_time"])
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
        "options": {"password": musikcube_info.get("password")}
    })

# CubeRPC Connection
if __name__ == "__main__":

    # Connect to Musikcube
    ws = websocket.WebSocketApp(
        f"ws://localhost:{musikcube_info.get('metaport', 7905)}",
        on_open = on_open,
        on_message = on_message,
        on_error = on_error,
        on_close = on_close
    )
    ws.run_forever(dispatcher = rel, reconnect = 5)
    rel.signal(2, rel.abort)
    rel.dispatch()
