import io
import os
import platform
import subprocess
import psutil
from flask import Flask, request, jsonify, Response, send_file

app = Flask(__name__)
TOKEN = "REPLACE_WITH_TOKEN_FROM_CONFIG_JSON"
IS_WIN = platform.system() == "Windows"

if not IS_WIN and "DISPLAY" not in os.environ:
    os.environ["DISPLAY"] = ":0"

def auth():
    return request.args.get("token") == TOKEN

@app.route("/stats")
def stats():
    if not auth():
        return jsonify({"ok": False, "msg": "Unauthorized"}), 403
    mem = psutil.virtual_memory()
    procs = sorted(
        psutil.process_iter(['name', 'memory_info']),
        key=lambda p: p.info['memory_info'].rss if p.info['memory_info'] else 0,
        reverse=True
    )
    top = procs[0].info['name'] if procs else "N/A"
    return jsonify({
        "ok": True,
        "cpu": psutil.cpu_percent(interval=0.2),
        "ram_used": round(mem.used / (1024**3), 1),
        "ram_total": round(mem.total / (1024**3), 1),
        "top_proc": top
    })

@app.route("/screenshot")
def screenshot():
    if not auth():
        return jsonify({"ok": False, "msg": "Unauthorized"}), 403
    if IS_WIN:
        import mss
        from PIL import Image
        with mss.mss() as sct:
            raw = sct.grab(sct.monitors[1])
            img = Image.frombytes("RGB", raw.size, raw.bgra, "raw", "BGRX")
            img.thumbnail((1280, 720))
            buf = io.BytesIO()
            img.save(buf, format="JPEG", quality=75)
            return Response(buf.getvalue(), mimetype="image/jpeg")
    else:
        img_path, thumb_path = "/tmp/hub_screen.jpg", "/tmp/hub_screen-thumb.jpg"
        if os.path.exists(img_path):
            os.remove(img_path)
        res = subprocess.run(["scrot", "-q", "75", "-t", "50", img_path], capture_output=True, text=True)
        if os.path.exists(thumb_path):
            return send_file(thumb_path, mimetype="image/jpeg")
        return jsonify({"ok": False, "msg": f"Display error: {res.stderr.strip()}"}), 500

@app.route("/reboot", methods=["POST"])
def reboot():
    if not auth():
        return jsonify({"ok": False, "msg": "Unauthorized"}), 403
    if IS_WIN:
        subprocess.Popen(["shutdown", "/r", "/f", "/t", "3"], shell=True)
    else:
        subprocess.Popen(["sudo", "reboot"])
    return jsonify({"ok": True, "msg": "Reboot command sent"})

@app.route("/shutdown", methods=["POST"])
def shutdown():
    if not auth():
        return jsonify({"ok": False, "msg": "Unauthorized"}), 403
    if IS_WIN:
        subprocess.Popen(["shutdown", "/s", "/f", "/t", "3"], shell=True)
    else:
        subprocess.Popen(["sudo", "poweroff"])
    return jsonify({"ok": True, "msg": "Shutdown command sent"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5050)
