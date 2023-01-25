# Copyright 2023 iiPython

# Modules
import os
import rel
import json
import websocket

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

def on_message(ws, message):
    print(message)

def on_error(ws, message):
    print(message)

def on_close(ws, close_status_code, close_msg):
    print("### closed ###")

def on_open(ws):
    print("Opened connection")
    ws.send({"name": "authenticate", "type": "request", "id": "IUuishdfiuG", "device_id": "cuberpc", "options": {"password": None}})

if __name__ == "__main__":
    ws = websocket.WebSocketApp(
        "ws://localhost:7905",
        on_open = on_open,
        on_message = on_message,
        on_error = on_error,
        on_close = on_close
    )
    ws.run_forever(dispatcher = rel, reconnect = 5)
    rel.signal(2, rel.abort)
    rel.dispatch()
