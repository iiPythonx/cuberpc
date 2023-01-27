# Copyright 2023 iiPython
# CubeD - album art storage server for CubeRPC

# Modules
import os
import re
import shutil
from aiohttp import web
from werkzeug.utils import secure_filename

# Initialization
app, templates = web.Application(), os.path.join(os.path.dirname(__file__), "templates")
ip_regex = re.compile(r"[0-9.]*$")

def secure_ip(ip: str) -> str:
    return not (not ip_regex.match(ip) or len(ip) > 15)

def render_html(file: str, *args) -> web.Response:
    with open(os.path.join(templates, file), "r") as fh:
        data = fh.read()

    for i, d in enumerate(args):
        data = data.replace("{{{}}}".format(i), str(d))

    return web.Response(text = data, content_type = "text/html")

def grab_ip(req: web.Request) -> str:

    # Grab a (hopefully) unique IP
    ip, cfc = req.remote, req.headers.get("CF-Connecting-IP")
    if cfc is not None:
        if not secure_ip(cfc):
            raise web.HTTPBadRequest  # People can mess with headers if we ARENT using CF

        ip = cfc

    return ip

# Settings
art_folder = os.getenv("CUBED_ALBUMART_FOLDER", "")
base_domain = os.getenv("CUBED_DOMAIN", "")  # SHOULD be in format 'https://somewebsite.tld' with NO trailing slash
if not (base_domain.strip() and art_folder.strip()):
    exit("Missing critical environment variables!")

base_domain = base_domain.rstrip("/")
if not base_domain.startswith("http"):
    base_domain = "http://" + base_domain

elif not os.path.isdir(art_folder):
    try:
        os.mkdir(art_folder)

    except Exception:
        exit("Failed to create album art folder!")

# Routes
routes = web.RouteTableDef()

@routes.route("*", "/")
async def route_index(req: web.Request) -> web.Response:

    # Grab info
    path = os.path.join(art_folder, grab_ip(req))
    count = len(os.listdir(path)) if os.path.isdir(path) else 0

    # Methods
    if req.method == "POST":
        if not count:
            return render_html("none.html")

        try:
            shutil.rmtree(path)
            return render_html("success.html")

        except Exception as err:
            print(err)
            return render_html("failure.html")

    elif req.method == "GET":
        return render_html("index.html", count)

    raise web.HTTPMethodNotAllowed

@routes.get("/a/{ip}/{file}")
async def fetch_art(req: web.Request) -> web.Response:
    if not secure_ip(req.match_info["ip"]):
        raise web.HTTPBadRequest

    path = os.path.join(art_folder, req.match_info["ip"], secure_filename(req.match_info["file"]))
    if not os.path.isfile(path):
        raise web.HTTPNotFound

    return web.FileResponse(os.path.abspath(path))

@routes.post("/upload")
async def upload_file(req: web.Request) -> web.Response:
    reader = await req.multipart()
    ip = grab_ip(req)

    # Handle upload
    field = await reader.next()
    assert field.name == "thumb"
    size, fn = 0, secure_filename(field.filename)
    if not fn:
        raise web.HTTPBadRequest

    userfolder = os.path.join(art_folder, ip)
    if not os.path.isdir(userfolder):
        os.makedirs(userfolder)

    with open(os.path.join(userfolder, fn), "wb") as f:
        while True:
            if size > 5 * (1024 ** 2):
                raise web.HTTPInsufficientStorage  # 5mb per thumbnail maximum

            chunk = await field.read_chunk()
            if not chunk:
                break

            size += len(chunk)
            f.write(chunk)

    return web.Response(text = f"{base_domain}/a/{ip}/{fn}")

app.add_routes(routes)

# Launch server
if __name__ == "__main__":
    web.run_app(
        app,
        host = "0.0.0.0",
        port = os.getenv("PORT", 8080)
    )
