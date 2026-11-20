import re
import json
import socket
import subprocess
import urllib.request
import psutil
import os
CONFIG_FILE = 'config.json'

from flask import Flask, render_template, jsonify, request, Response

app = Flask(__name__)

def init_config():
    if not os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump({'hub_title':'PC Control Hub','default_theme':'dark','default_lang':'ru','lan_broadcast':'192.168.1.255','agent_port':5050,'agent_token':os.urandom(16).hex(),'devices':[]}, f, indent=2)

def load_config():
    init_config()
    with open('config.json', 'r', encoding='utf-8') as f:
        return json.load(f)

def check_port(ip, port=3389):
    if not ip:
        return False
    try:
        with socket.create_connection((ip, port), timeout=1.2):
            return True
    except Exception:
        return False

def get_active_ip(dev, cfg):
    port = cfg.get('agent_port', 5050)
    if check_port(dev.get('lan_ip'), port) or check_port(dev.get('lan_ip'), 3389):
        return dev.get('lan_ip')
    if check_port(dev.get('zt_ip'), port) or check_port(dev.get('zt_ip'), 3389):
        return dev.get('zt_ip')
    return None

def get_hub_stats():
    mem = psutil.virtual_memory()
    temp = "N/A"
    try:
        temps = psutil.sensors_temperatures()
        if 'coretemp' in temps:
            temp = f"{temps['coretemp'][0].current:.0f}°C"
    except Exception:
        pass
    return {
        "cpu": psutil.cpu_percent(interval=0.1),
        "ram_used": round(mem.used / (1024**3), 1),
        "ram_total": round(mem.total / (1024**3), 1),
        "ram_percent": mem.percent,
        "temp": temp
    }

@app.route('/')
def index():
    cfg = load_config()
    return render_template('index.html', config=cfg)

@app.route('/api/status')
def api_status():
    cfg = load_config()
    statuses = {}
    for dev in cfg['devices']:
        lan_ip, zt_ip = dev.get('lan_ip'), dev.get('zt_ip')
        lan_ok = check_port(lan_ip, 3389) or check_port(lan_ip, cfg.get('agent_port', 5050)) or (bool(lan_ip) and subprocess.run(['ping', '-c', '1', '-W', '1', lan_ip], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0)
        zt_ok = check_port(zt_ip, 3389) or check_port(zt_ip, cfg.get('agent_port', 5050)) or (bool(zt_ip) and subprocess.run(['ping', '-c', '1', '-W', '1', zt_ip], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0)
        statuses[dev['id']] = {
            "online": lan_ok or zt_ok,
            "lan": lan_ok,
            "zt": zt_ok
        }
    return jsonify({"hub": get_hub_stats(), "devices": statuses})

@app.route('/api/wol/<dev_id>', methods=['POST'])
def api_wol(dev_id):
    cfg = load_config()
    dev = next((d for d in cfg['devices'] if d['id'] == dev_id), None)
    if not dev:
        return jsonify({"ok": False, "msg": "Device not found"}), 404
    bcast = cfg.get('lan_broadcast', '192.168.2.255')
    subprocess.run(['wakeonlan', '-i', bcast, dev['mac']])
    return jsonify({"ok": True, "msg": f"WOL отправлен на {dev['name']}"})

@app.route('/api/agent/<dev_id>/<action>', methods=['GET', 'POST'])
def proxy_agent(dev_id, action):
    cfg = load_config()
    dev = next((d for d in cfg['devices'] if d['id'] == dev_id), None)
    if not dev:
        return jsonify({"ok": False, "msg": "Устройство не найдено"}), 404
    ip = get_active_ip(dev, cfg)
    if not ip:
        return jsonify({"ok": False, "msg": "ПК недоступен по сети"}), 503
    url = f"http://{ip}:{cfg.get('agent_port', 5050)}/{action}?token={cfg.get('agent_token')}"
    try:
        req = urllib.request.Request(url, method=request.method)
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = resp.read()
            ctype = resp.headers.get('Content-Type', 'application/json')
            return Response(data, mimetype=ctype)
    except Exception as e:
        return jsonify({"ok": False, "msg": f"Агент не отвечает ({e})"}), 502

@app.route('/rdp/<mode>/<dev_id>.rdp')
def download_rdp(mode, dev_id):
    cfg = load_config()
    dev = next((d for d in cfg['devices'] if d['id'] == dev_id), None)
    if not dev:
        return "Not found", 404
    target_ip = dev['zt_ip'] if mode == 'zt' else dev['lan_ip']
    rdp_content = f"full address:s:{target_ip}\nusername:s:{dev['rdp_user']}\nprompt for credentials:i:1\n"
    return Response(
        rdp_content,
        mimetype="application/x-rdp",
        headers={"Content-Disposition": f"attachment;filename={dev_id}_{mode}.rdp"}
    )

@app.route('/api/rename/<dev_id>', methods=['POST'])
def api_rename(dev_id):
    cfg = load_config()
    data = request.get_json(silent=True) or {}
    new_name = str(data.get('name', '')).strip()
    if not new_name:
        return jsonify({"ok": False, "msg": "Имя не может быть пустым"}), 400
    for d in cfg['devices']:
        if d['id'] == dev_id:
            d['name'] = new_name
            with open('config.json', 'w', encoding='utf-8') as f:
                json.dump(cfg, f, ensure_ascii=False, indent=2)
            return jsonify({"ok": True, "name": new_name})
    return jsonify({"ok": False, "msg": "Устройство не найдено"}), 404

@app.route('/api/device/add', methods=['POST'])
def api_device_add():
    cfg = load_config()
    data = request.get_json(silent=True) or {}
    lan_ip = str(data.get('lan_ip', '')).strip()
    if not lan_ip:
        return jsonify({"ok": False, "msg": "Локальный IP (LAN) обязателен"}), 400
    name = str(data.get('name', '')).strip() or f"ПК ({lan_ip})"
    os_name = str(data.get('os', '')).strip() or "Windows / Linux"
    zt_ip = str(data.get('zt_ip', '')).strip()
    mac = str(data.get('mac', '')).strip().replace('-', ':')
    rdp_user = str(data.get('rdp_user', '')).strip() or "User"
    moonlight = bool(data.get('moonlight', False))

    dev_id = "dev-" + re.sub(r'[^a-zA-Z0-9]', '', lan_ip) + "-" + str(len(cfg['devices']) + 1)
    new_dev = {
        "id": dev_id,
        "name": name,
        "os": os_name,
        "lan_ip": lan_ip,
        "zt_ip": zt_ip,
        "mac": mac,
        "rdp_user": rdp_user,
        "moonlight": moonlight
    }
    cfg['devices'].append(new_dev)
    with open('config.json', 'w', encoding='utf-8') as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)
    return jsonify({"ok": True, "device": new_dev})

@app.route('/api/device/delete/<dev_id>', methods=['POST'])
def api_device_delete(dev_id):
    cfg = load_config()
    cfg['devices'] = [d for d in cfg['devices'] if d['id'] != dev_id]
    with open('config.json', 'w', encoding='utf-8') as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)
    return jsonify({"ok": True})

@app.route('/api/device/edit/<dev_id>', methods=['POST'])
def api_device_edit(dev_id):
    cfg = load_config()
    data = request.get_json(silent=True) or {}
    lan_ip = str(data.get('lan_ip', '')).strip()
    if not lan_ip:
        return jsonify({"ok": False, "msg": "LAN IP обязателен"}), 400
    for d in cfg['devices']:
        if d['id'] == dev_id:
            d['name'] = str(data.get('name', '')).strip() or d['name']
            d['os'] = str(data.get('os', '')).strip() or "Windows / Linux"
            d['lan_ip'] = lan_ip
            d['zt_ip'] = str(data.get('zt_ip', '')).strip()
            d['mac'] = str(data.get('mac', '')).strip().replace('-', ':')
            d['rdp_user'] = str(data.get('rdp_user', '')).strip() or "User"
            d['moonlight'] = bool(data.get('moonlight', False))
            d['copyparty'] = bool(data.get('copyparty', False))
            with open('config.json', 'w', encoding='utf-8') as f:
                json.dump(cfg, f, ensure_ascii=False, indent=2)
            return jsonify({"ok": True})
    return jsonify({"ok": False, "msg": "Устройство не найдено"}), 404

import zlib, struct

def make_png_icon():
    w, h = 32, 32
    rows = []
    for y in range(h):
        row = bytearray([0])
        for x in range(w):
            # Тёмно-синий фон (15, 23, 42) и голубая рамка (56, 189, 248)
            if x < 2 or x >= w-2 or y < 2 or y >= h-2:
                r, g, b, a = 56, 189, 248, 255
            # Зелёный индикатор в правом верхнем углу
            elif (x - 25)**2 + (y - 7)**2 <= 6:
                r, g, b, a = 16, 185, 129, 255
            # Белый символ >_
            elif (abs((y - 16) - (12 - x)) <= 1 and 7 <= x <= 12) or (abs((16 - y) - (12 - x)) <= 1 and 7 <= x <= 12) or (20 <= y <= 21 and 15 <= x <= 23):
                r, g, b, a = 255, 255, 255, 255
            else:
                r, g, b, a = 15, 23, 42, 255
            row.extend([r, g, b, a])
        rows.append(bytes(row))
    raw = b''.join(rows)
    def chunk(tag, data):
        return struct.pack('!I', len(data)) + tag + data + struct.pack('!I', zlib.crc32(tag + data) & 0xffffffff)
    ihdr = struct.pack('!IIBBBBB', w, h, 8, 6, 0, 0, 0)
    return b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', ihdr) + chunk(b'IDAT', zlib.compress(raw)) + chunk(b'IEND', b'')

PNG_ICON_BYTES = make_png_icon()

@app.route('/favicon.ico')
def favicon():
    return Response(PNG_ICON_BYTES, mimetype='image/png')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80)
