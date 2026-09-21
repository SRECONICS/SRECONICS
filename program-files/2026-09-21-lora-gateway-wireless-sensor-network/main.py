#!/usr/bin/env python3
"""
LoRa Gateway for Wireless Sensor Network
Board: Raspberry Pi 3 B+
Receives sensor packets from LoRa nodes via RFM95W SPI HAT,
logs them to SQLite, publishes on Mosquitto MQTT, and serves
a live Flask dashboard on port 5000.

Wiring (RFM95W HAT — SPI0):
  MISO  -> GPIO 9  (pin 21)
  MOSI  -> GPIO 10 (pin 19)
  SCK   -> GPIO 11 (pin 23)
  CS    -> GPIO 8  (pin 24)  CE0
  IRQ   -> GPIO 25 (pin 22)
  RST   -> GPIO 22 (pin 15)

Install deps:
  pip install adafruit-circuitpython-rfm9x paho-mqtt flask
  sudo apt install mosquitto mosquitto-clients
"""

import time
import json
import struct
import sqlite3
import threading
import logging
from datetime import datetime

# CircuitPython-style LoRa driver (works on RPi via blinka)
import board
import busio
import digitalio
import adafruit_rfm9x
import paho.mqtt.client as mqtt
from flask import Flask, jsonify, render_template_string

# ─── CONFIG ───────────────────────────────────────────────────────────────
LORA_FREQ      = 915.0          # MHz — change to 433.0 for EU
MQTT_BROKER    = "localhost"
MQTT_PORT      = 1883
MQTT_TOPIC     = "sensors/lora"
DB_PATH        = "/home/pi/lora_data.db"
FLASK_PORT     = 5000
LOG_LEVEL      = logging.INFO

logging.basicConfig(level=LOG_LEVEL,
                    format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

# ─── DATABASE ─────────────────────────────────────────────────────────────
def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS readings (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            ts        TEXT    NOT NULL,
            node_id   TEXT    NOT NULL,
            sensor    TEXT,
            value     REAL,
            unit      TEXT,
            rssi      INTEGER,
            raw       TEXT
        )
    """)
    conn.commit()
    conn.close()
    log.info("DB initialised at %s", DB_PATH)

def insert_reading(node_id, sensor, value, unit, rssi, raw):
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        INSERT INTO readings (ts, node_id, sensor, value, unit, rssi, raw)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (datetime.utcnow().isoformat(), node_id, sensor, value, unit, rssi, raw))
    conn.commit()
    conn.close()

# ─── LORA SETUP ────────────────────────────────────────────────────────────
def setup_lora():
    spi  = busio.SPI(board.SCK, MOSI=board.MOSI, MISO=board.MISO)
    cs   = digitalio.DigitalInOut(board.CE0)
    rst  = digitalio.DigitalInOut(board.D22)
    rfm9x = adafruit_rfm9x.RFM9x(spi, cs, rst, LORA_FREQ)
    rfm9x.tx_power = 13
    log.info("RFM9x ready at %.1f MHz", LORA_FREQ)
    return rfm9x

def parse_packet(raw_bytes):
    """
    Simple packet format: JSON string from nodes.
    Expected: {"id":"A","s":"temp","v":23.5,"u":"C"}
    """
    try:
        text = raw_bytes.decode("utf-8").strip("\x00")
        data = json.loads(text)
        return data.get("id","?"), data.get("s","?"), data.get("v",0), data.get("u","?"), text
    except Exception as e:
        log.warning("Bad packet: %s  raw=%s", e, raw_bytes.hex())
        return "?", "raw", 0, "", raw_bytes.hex()

# ─── MQTT ─────────────────────────────────────────────────────────────────
mqtt_client = mqtt.Client()

def connect_mqtt():
    mqtt_client.connect(MQTT_BROKER, MQTT_PORT, keepalive=60)
    mqtt_client.loop_start()
    log.info("MQTT connected to %s:%d", MQTT_BROKER, MQTT_PORT)

def publish(node_id, sensor, value, unit, rssi):
    payload = json.dumps({
        "ts": datetime.utcnow().isoformat(),
        "node": node_id, "sensor": sensor,
        "value": value, "unit": unit, "rssi": rssi
    })
    mqtt_client.publish(f"{MQTT_TOPIC}/{node_id}", payload, qos=1)

# ─── FLASK DASHBOARD ───────────────────────────────────────────────────────
app = Flask(__name__)

DASHBOARD_HTML = """
<!DOCTYPE html>
<html><head>
<meta charset="utf-8">
<meta http-equiv="refresh" content="5">
<title>LoRa Gateway Dashboard</title>
<style>
  body{background:#0d1117;color:#e6edf3;font-family:monospace;padding:20px}
  h1{color:#58c96a} table{border-collapse:collapse;width:100%}
  th,td{border:1px solid #30363d;padding:8px 12px;text-align:left}
  th{background:#161b22;color:#58c96a}
  tr:nth-child(even){background:#0d1117} tr:hover{background:#1c2128}
  .node{color:#79c0ff} .val{color:#ffa657}
</style>
</head><body>
<h1>LoRa Sensor Network — Live Feed</h1>
<p>Last 50 readings · auto-refresh 5 s</p>
<table>
  <tr><th>Timestamp</th><th>Node</th><th>Sensor</th><th>Value</th><th>Unit</th><th>RSSI</th></tr>
  {% for r in rows %}
  <tr>
    <td>{{r[1]}}</td>
    <td class="node">{{r[2]}}</td>
    <td>{{r[3]}}</td>
    <td class="val">{{r[4]}}</td>
    <td>{{r[5]}}</td>
    <td>{{r[6]}}</td>
  </tr>
  {% endfor %}
</table>
</body></html>
"""

@app.route("/")
def dashboard():
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute(
        "SELECT * FROM readings ORDER BY id DESC LIMIT 50"
    ).fetchall()
    conn.close()
    return render_template_string(DASHBOARD_HTML, rows=rows)

@app.route("/api/readings")
def api_readings():
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute(
        "SELECT ts,node_id,sensor,value,unit,rssi FROM readings ORDER BY id DESC LIMIT 100"
    ).fetchall()
    conn.close()
    keys = ["ts","node","sensor","value","unit","rssi"]
    return jsonify([dict(zip(keys, r)) for r in rows])

@app.route("/api/export/csv")
def export_csv():
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute("SELECT * FROM readings ORDER BY id").fetchall()
    conn.close()
    lines = ["id,ts,node_id,sensor,value,unit,rssi,raw"]
    for r in rows:
        lines.append(",".join(str(x) for x in r))
    return "\n".join(lines), 200, {
        "Content-Type": "text/csv",
        "Content-Disposition": "attachment; filename=lora_export.csv"
    }

# ─── MAIN RECEIVE LOOP ────────────────────────────────────────────────────
def receive_loop(rfm9x):
    log.info("Listening for LoRa packets…")
    while True:
        packet = rfm9x.receive(timeout=5.0)
        if packet is not None:
            rssi = rfm9x.last_rssi
            node_id, sensor, value, unit, raw = parse_packet(packet)
            log.info("Packet  node=%-4s  sensor=%-6s  value=%-8s  RSSI=%d",
                     node_id, sensor, value, rssi)
            insert_reading(node_id, sensor, value, unit, rssi, raw)
            publish(node_id, sensor, value, unit, rssi)

def main():
    init_db()
    connect_mqtt()
    rfm9x = setup_lora()
    # Flask in background thread
    t = threading.Thread(target=lambda: app.run(host="0.0.0.0", port=FLASK_PORT), daemon=True)
    t.start()
    log.info("Dashboard at http://0.0.0.0:%d", FLASK_PORT)
    receive_loop(rfm9x)

if __name__ == "__main__":
    main()
