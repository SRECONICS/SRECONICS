#!/usr/bin/env python3
"""
Smart Home Energy Monitor — Pi 4 Edition
-----------------------------------------
Reads 4 split-core CT clamps via ADS1115 (I2C), computes RMS current,
real power (W), energy (kWh), and publishes readings to MQTT.
InfluxDB writer and Grafana dashboard are configured via setup.sh.

Wiring (ADS1115 → Pi 4):
  VDD  → 3.3 V (Pin 1)
  GND  → GND   (Pin 6)
  SCL  → GPIO3 / Pin 5
  SDA  → GPIO2 / Pin 3
  ADDR → GND   (I2C address 0x48)
  A0–A3 → CT clamp burden resistor outputs (one per circuit)

CT Clamp calibration:
  SCT-013-030 (30 A) with 62 Ω burden resistor → 1 A : ~0.0667 V
  Adjust CALIBRATION_FACTOR per your clamp + burden combo.

Dependencies:
  pip install adafruit-circuitpython-ads1x15 paho-mqtt influxdb-client
"""

import time
import math
import json
import board
import busio
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn
import paho.mqtt.client as mqtt
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS

# ── Configuration ────────────────────────────────────────────────────────────
MQTT_BROKER   = "localhost"
MQTT_PORT     = 1883
MQTT_TOPIC    = "home/energy"

INFLUX_URL    = "http://localhost:8086"
INFLUX_TOKEN  = "YOUR_INFLUX_TOKEN"       # set after running setup.sh
INFLUX_ORG    = "sreconics"
INFLUX_BUCKET = "energy"

MAINS_VOLTAGE      = 230.0   # Vrms — change to 110.0 for North America
CALIBRATION_FACTOR = 30.0    # SCT-013-030: 30 A full-scale
ADC_MAX_VOLTAGE    = 3.3
SAMPLES_PER_CYCLE  = 200     # samples for one 50/60 Hz RMS window
SAMPLE_INTERVAL_S  = 0.0001  # 10 kHz polling rate

CIRCUITS = {
    "kitchen":  ADS.P0,
    "living":   ADS.P1,
    "bedroom":  ADS.P2,
    "solar_in": ADS.P3,
}

# ── Hardware init ─────────────────────────────────────────────────────────────
i2c = busio.I2C(board.SCL, board.SDA)
ads = ADS.ADS1115(i2c)
ads.gain = 1          # ±4.096 V full-scale

channels = {name: AnalogIn(ads, pin) for name, pin in CIRCUITS.items()}

# ── MQTT init ─────────────────────────────────────────────────────────────────
mqttc = mqtt.Client(client_id="pi4-energy-monitor")
mqttc.connect(MQTT_BROKER, MQTT_PORT, keepalive=60)
mqttc.loop_start()

# ── InfluxDB init ─────────────────────────────────────────────────────────────
influx = InfluxDBClient(url=INFLUX_URL, token=INFLUX_TOKEN, org=INFLUX_ORG)
write_api = influx.write_api(write_options=SYNCHRONOUS)


def measure_rms(channel, n_samples: int = SAMPLES_PER_CYCLE) -> float:
    """Return RMS current (A) from n voltage samples centred around mid-rail."""
    sum_sq = 0.0
    for _ in range(n_samples):
        raw = channel.voltage - (ADC_MAX_VOLTAGE / 2)  # remove DC bias
        sum_sq += raw * raw
        time.sleep(SAMPLE_INTERVAL_S)
    vrms = math.sqrt(sum_sq / n_samples)
    # SCT-013-030: Irms = Vrms_burden × (30 A / 1 V) ÷ sqrt(2) already included
    return vrms * CALIBRATION_FACTOR


def compute_power(irms: float) -> dict:
    """Compute apparent power (VA), assuming unity power factor for this demo."""
    apparent_va = irms * MAINS_VOLTAGE
    # Real power estimate (PF ≈ 0.9 for mixed resistive/inductive loads)
    real_w = apparent_va * 0.9
    return {"irms_A": round(irms, 3), "apparent_VA": round(apparent_va, 1), "real_W": round(real_w, 1)}


def publish(readings: dict) -> None:
    payload = json.dumps(readings)
    mqttc.publish(MQTT_TOPIC, payload, qos=1)

    points = []
    for circuit, data in readings.items():
        p = (
            Point("power")
            .tag("circuit", circuit)
            .field("irms_A",      data["irms_A"])
            .field("apparent_VA", data["apparent_VA"])
            .field("real_W",      data["real_W"])
        )
        points.append(p)
    write_api.write(bucket=INFLUX_BUCKET, org=INFLUX_ORG, record=points)


# ── Main loop ─────────────────────────────────────────────────────────────────
print("Energy monitor started — publishing every 5 s")
total_kwh = {name: 0.0 for name in CIRCUITS}
last_ts = time.time()

try:
    while True:
        readings = {}
        for name, ch in channels.items():
            irms = measure_rms(ch)
            data = compute_power(irms)
            # Accumulate kWh
            now = time.time()
            dt_h = (now - last_ts) / 3600.0
            total_kwh[name] += data["real_W"] * dt_h / 1000.0
            data["total_kWh"] = round(total_kwh[name], 4)
            readings[name] = data
            last_ts = now

        publish(readings)
        total_w = sum(r["real_W"] for r in readings.values())
        print(f"[{time.strftime('%H:%M:%S')}] Total: {total_w:.0f} W | {json.dumps(readings)}")
        time.sleep(5)

except KeyboardInterrupt:
    print("Shutting down.")
    mqttc.loop_stop()
    influx.close()
