#!/usr/bin/env python3
"""
Pocket VPN Gateway with WireGuard & Live Client Dashboard
Board: Raspberry Pi Zero 2 W
Project: sreconics/sreconics daily-showcase  |  2026-09-29

This script is the main application that runs as a systemd service.
It monitors the WireGuard interface (wg0), collects peer statistics
(handshake time, transferred bytes, allowed IPs), and serves a live
dashboard on http://vpn.local:8080.

Setup:
  sudo pip3 install flask psutil
  sudo systemctl enable wg-quick@wg0
  sudo systemctl enable vpn-dashboard
"""

import subprocess
import re
import time
import json
import logging
from datetime import datetime, timezone
from flask import Flask, render_template_string, jsonify

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger("vpn-dashboard")

app = Flask(__name__)

WG_IFACE = "wg0"
DASHBOARD_PORT = 8080
REFRESH_INTERVAL = 10  # seconds


# ── WireGuard helpers ─────────────────────────────────────────

def wg_show() -> dict:
    """
    Parse `wg show wg0 dump` output into a structured dict.
    Returns {
        'server': {listen_port, public_key, private_key_hash},
        'peers': [
            {public_key, endpoint, allowed_ips, latest_handshake,
             rx_bytes, tx_bytes, keepalive}
        ]
    }
    """
    try:
        out = subprocess.check_output(
            ["sudo", "wg", "show", WG_IFACE, "dump"],
            stderr=subprocess.DEVNULL,
            timeout=5,
            text=True,
        )
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired) as e:
        log.warning("wg show failed: %s", e)
        return {"server": {}, "peers": []}

    lines = [l.strip() for l in out.strip().splitlines() if l.strip()]
    if not lines:
        return {"server": {}, "peers": []}

    # First line: interface info (private_key, public_key, listen_port, fwmark)
    parts = lines[0].split("\t")
    server = {
        "private_key_hash": hash(parts[0]) if len(parts) > 0 else "",
        "public_key": parts[1] if len(parts) > 1 else "",
        "listen_port": int(parts[2]) if len(parts) > 2 else 51820,
    }

    peers = []
    for line in lines[1:]:
        cols = line.split("\t")
        if len(cols) < 8:
            continue
        pub_key, preshared, endpoint, allowed_ips, latest_hs, rx, tx, keepalive = cols[:8]
        ts = int(latest_hs) if latest_hs.isdigit() else 0
        peers.append({
            "public_key": pub_key,
            "public_key_short": pub_key[:12] + "…",
            "endpoint": endpoint if endpoint != "(none)" else "—",
            "allowed_ips": allowed_ips,
            "latest_handshake": datetime.fromtimestamp(ts, tz=timezone.utc).isoformat() if ts else "never",
            "latest_handshake_ago": _ago(ts),
            "rx_bytes": int(rx),
            "tx_bytes": int(tx),
            "rx_human": _human(int(rx)),
            "tx_human": _human(int(tx)),
            "keepalive": keepalive if keepalive != "off" else "off",
            "online": (time.time() - ts) < 180 if ts else False,
        })

    return {"server": server, "peers": peers}


def _human(n: int) -> str:
    for unit in ("B", "KiB", "MiB", "GiB"):
        if n < 1024:
            return f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} TiB"


def _ago(ts: int) -> str:
    if not ts:
        return "never"
    diff = int(time.time() - ts)
    if diff < 60:
        return f"{diff}s ago"
    if diff < 3600:
        return f"{diff//60}m ago"
    if diff < 86400:
        return f"{diff//3600}h ago"
    return f"{diff//86400}d ago"


def system_stats() -> dict:
    """Return CPU temp and load average."""
    try:
        temp_raw = open("/sys/class/thermal/thermal_zone0/temp").read().strip()
        temp_c = int(temp_raw) / 1000
    except Exception:
        temp_c = 0.0

    try:
        load = open("/proc/loadavg").read().split()[:3]
        load1, load5, load15 = (float(x) for x in load)
    except Exception:
        load1 = load5 = load15 = 0.0

    try:
        import psutil
        mem = psutil.virtual_memory()
        mem_pct = mem.percent
    except Exception:
        mem_pct = 0.0

    return {
        "temp_c": round(temp_c, 1),
        "load1": load1, "load5": load5, "load15": load15,
        "mem_pct": round(mem_pct, 1),
        "uptime": _uptime(),
    }


def _uptime() -> str:
    try:
        raw = float(open("/proc/uptime").read().split()[0])
        h, rem = divmod(int(raw), 3600)
        m = rem // 60
        return f"{h}h {m}m"
    except Exception:
        return "—"


# ── Dashboard HTML ────────────────────────────────────────────

DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta http-equiv="refresh" content="{{ refresh }}">
<title>VPN Gateway Dashboard</title>
<style>
  :root {--bg:#0d1117;--card:#161b22;--border:#30363d;--accent:#38bdf8;
          --green:#3fcf8e;--orange:#fb923c;--red:#f87171;--text:#e6edf3;--muted:#6e7681}
  * { box-sizing: border-box; margin: 0; padding: 0 }
  body { background: var(--bg); color: var(--text); font-family: ui-monospace, monospace; padding: 24px }
  h1 { color: var(--accent); font-size: 1.5rem; margin-bottom: 4px }
  .subtitle { color: var(--muted); font-size: 0.85rem; margin-bottom: 24px }
  .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: 12px; margin-bottom: 24px }
  .stat { background: var(--card); border: 1px solid var(--border); border-radius: 8px; padding: 16px }
  .stat-val { font-size: 1.8rem; font-weight: bold; color: var(--accent) }
  .stat-label { font-size: 0.75rem; color: var(--muted); margin-top: 4px }
  table { width: 100%; border-collapse: collapse; background: var(--card);
          border: 1px solid var(--border); border-radius: 8px; overflow: hidden }
  th { background: var(--border); color: var(--muted); font-size: 0.75rem;
       text-transform: uppercase; padding: 10px 14px; text-align: left }
  td { padding: 10px 14px; font-size: 0.85rem; border-top: 1px solid var(--border) }
  .dot { display:inline-block;width:8px;height:8px;border-radius:50%;margin-right:6px }
  .online  { background: var(--green) }
  .offline { background: var(--red) }
  footer { margin-top: 24px; color: var(--muted); font-size: 0.75rem; text-align: center }
</style>
</head>
<body>
<h1>&#x1F512; Pocket VPN Gateway</h1>
<p class="subtitle">Raspberry Pi Zero 2 W &nbsp;·&nbsp; WireGuard wg0 &nbsp;·&nbsp;
  refreshes every {{ refresh }}s &nbsp;·&nbsp; {{ now }}</p>

<div class="grid">
  <div class="stat"><div class="stat-val">{{ stats.temp_c }}°C</div><div class="stat-label">CPU Temp</div></div>
  <div class="stat"><div class="stat-val">{{ stats.load1 }}</div><div class="stat-label">Load (1 min)</div></div>
  <div class="stat"><div class="stat-val">{{ stats.mem_pct }}%</div><div class="stat-label">Mem Used</div></div>
  <div class="stat"><div class="stat-val">{{ stats.uptime }}</div><div class="stat-label">Uptime</div></div>
  <div class="stat"><div class="stat-val">{{ peers|length }}</div><div class="stat-label">WG Peers</div></div>
  <div class="stat"><div class="stat-val" style="color:var(--green)">{{ online_count }}</div><div class="stat-label">Online Now</div></div>
</div>

<table>
  <thead>
    <tr>
      <th>Peer</th><th>Endpoint</th><th>Allowed IPs</th>
      <th>Last Handshake</th><th>&#x2193; Rx</th><th>&#x2191; Tx</th><th>Status</th>
    </tr>
  </thead>
  <tbody>
    {% for p in peers %}
    <tr>
      <td>{{ p.public_key_short }}</td>
      <td>{{ p.endpoint }}</td>
      <td>{{ p.allowed_ips }}</td>
      <td>{{ p.latest_handshake_ago }}</td>
      <td>{{ p.rx_human }}</td>
      <td>{{ p.tx_human }}</td>
      <td><span class="dot {{ 'online' if p.online else 'offline' }}"></span>
          {{ 'Online' if p.online else 'Offline' }}</td>
    </tr>
    {% else %}
    <tr><td colspan="7" style="color:var(--muted);text-align:center">No peers configured yet.</td></tr>
    {% endfor %}
  </tbody>
</table>

<footer>DevNode Technologies · Pocket VPN Gateway · {{ server.listen_port or 51820 }} UDP</footer>
</body>
</html>
"""


@app.route("/")
def dashboard():
    data = wg_show()
    stats = system_stats()
    online_count = sum(1 for p in data["peers"] if p["online"])
    return render_template_string(
        DASHBOARD_HTML,
        peers=data["peers"],
        server=data["server"],
        stats=stats,
        online_count=online_count,
        now=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        refresh=REFRESH_INTERVAL,
    )


@app.route("/api/status")
def api_status():
    data = wg_show()
    stats = system_stats()
    return jsonify({
        "server": data["server"],
        "peers": data["peers"],
        "system": stats,
        "timestamp": datetime.now(tz=timezone.utc).isoformat(),
    })


if __name__ == "__main__":
    log.info("Starting VPN Dashboard on port %d", DASHBOARD_PORT)
    app.run(host="0.0.0.0", port=DASHBOARD_PORT, debug=False)
