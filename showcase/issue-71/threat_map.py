#!/usr/bin/env python3
"""
threat_map.py — Flask/SocketIO server feeding a Leaflet.js live threat map.
Tails the Loki log stream and pushes GeoIP-resolved threat events over
WebSocket to connected browsers.

Requirements:
    pip install flask flask-socketio requests geoip2

MaxMind GeoLite2 DB (free, registration required):
    https://dev.maxmind.com/geoip/geolite2-free-geolocation-data
    Download GeoLite2-City.mmdb and place it alongside this script.

Usage:
    python3 threat_map.py --loki http://localhost:3100 --port 5000
"""

import argparse
import json
import logging
import time
from datetime import datetime, timezone, timedelta
from threading import Thread

import geoip2.database
import requests
from flask import Flask, render_template_string
from flask_socketio import SocketIO

log = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")

app    = Flask(__name__)
sio    = SocketIO(app, cors_allowed_origins="*")
reader = None   # GeoIP reader, initialised in main()

# ── Minimal inline dashboard (no external JS CDN needed) ────────
DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>🛡 Pi 4 NIDS Threat Map</title>
  <link rel="stylesheet" href="https://unpkg.com/leaflet/dist/leaflet.css">
  <script src="https://unpkg.com/leaflet/dist/leaflet.js"></script>
  <script src="https://cdn.socket.io/4.7.5/socket.io.min.js"></script>
  <style>
    body { margin: 0; background: #0d1117; color: #e6edf3; font-family: monospace; }
    #map  { height: 70vh; }
    #log  { height: 28vh; overflow-y: auto; padding: 8px; font-size: 12px; }
    .high { color: #f85149; } .info { color: #3fb950; }
  </style>
</head>
<body>
  <div id="map"></div>
  <div id="log"><b>Live Events</b><br></div>
  <script>
    const map = L.map("map").setView([20, 0], 2);
    L.tileLayer("https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png",
      { attribution: "CartoDB" }).addTo(map);

    const socket = io();
    socket.on("threat", (ev) => {
      const cls = ev.severity === "high" ? "high" : "info";
      const color = ev.severity === "high" ? "#f85149" : "#3fb950";
      if (ev.lat && ev.lon) {
        const m = L.circleMarker([ev.lat, ev.lon],
          { radius: 6, color, fillOpacity: 0.8 }).addTo(map);
        m.bindPopup(`<b>${ev.src_ip}</b><br>${ev.country}<br>${ev.ml_label}`);
        setTimeout(() => map.removeLayer(m), 30000);
      }
      const logDiv = document.getElementById("log");
      logDiv.innerHTML += `<span class="${cls}">[${ev.ts}] ${ev.src_ip} → ${ev.dst_ip}:${ev.dst_port} | ${ev.ml_label} (${(ev.ml_score*100).toFixed(1)}%)</span><br>`;
      logDiv.scrollTop = logDiv.scrollHeight;
    });
  </script>
</body>
</html>"""

@app.get("/")
def index():
    return render_template_string(DASHBOARD_HTML)

# ── Loki tail thread ────────────────────────────────────────────
def tail_loki(loki_url: str):
    """Long-poll Loki /query_range every 5 s and emit events to browsers."""
    global reader
    while True:
        try:
            end   = datetime.now(timezone.utc)
            start = end - timedelta(seconds=5)
            params = {
                "query": '{job="nids"}',
                "start": str(int(start.timestamp() * 1e9)),
                "end":   str(int(end.timestamp()   * 1e9)),
                "limit": 200,
            }
            resp = requests.get(f"{loki_url}/loki/api/v1/query_range",
                                params=params, timeout=10)
            if resp.ok:
                for stream in resp.json().get("data", {}).get("result", []):
                    for _ts, line in stream["values"]:
                        try:
                            ev = json.loads(line)
                            # GeoIP lookup
                            try:
                                geo = reader.city(ev.get("src_ip", ""))
                                ev["lat"]     = geo.location.latitude
                                ev["lon"]     = geo.location.longitude
                                ev["country"] = geo.country.name
                            except Exception:
                                ev["lat"] = ev["lon"] = None
                                ev["country"] = "Unknown"
                            sio.emit("threat", ev)
                        except json.JSONDecodeError:
                            pass
        except Exception as e:
            log.debug("Loki tail error: %s", e)
        time.sleep(5)

def main():
    global reader
    parser = argparse.ArgumentParser()
    parser.add_argument("--loki",    default="http://localhost:3100")
    parser.add_argument("--geoip",   default="GeoLite2-City.mmdb")
    parser.add_argument("--port",    type=int, default=5000)
    args = parser.parse_args()

    reader = geoip2.database.Reader(args.geoip)
    Thread(target=tail_loki, args=(args.loki,), daemon=True).start()
    log.info("🗺  Threat map running on http://0.0.0.0:%d", args.port)
    sio.run(app, host="0.0.0.0", port=args.port)

if __name__ == "__main__":
    main()
