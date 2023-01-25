# Copyright 2023 iiPython

# Modules
import os
import sys
from flask import Flask, request, abort, send_from_directory
from werkzeug.utils import secure_filename

# Initialization
app = Flask("cubed")

# Settings
art_folder = sys.argv[1]
domain_base = sys.argv[2]

if not os.path.isdir(art_folder):
    os.mkdir(art_folder)

# Routes
@app.route("/a/<path:file>")
def fetch_art(file: str) -> None:
    return send_from_directory(art_folder, file)

@app.route("/upload", methods = ["POST"])
def upload_file() -> None:
    if "thumb" not in request.files:
        print(request.files)
        return abort(400)

    # Fetch request information
    if "id" not in request.form:
        return abort(400)

    fn = secure_filename(request.form["id"])
    thumbnail = request.files["thumb"]
    if not thumbnail.filename.strip():
        return abort(400)

    # Check for file
    filename = os.path.join(art_folder, fn)
    if not os.path.isfile(filename):
        thumbnail.save(filename)

    return f"{domain_base}/a/{fn}"

# Launch server
if __name__ == "__main__":
    app.run(
        host = "0.0.0.0",
        port = os.getenv("PORT", 8080)
    )
