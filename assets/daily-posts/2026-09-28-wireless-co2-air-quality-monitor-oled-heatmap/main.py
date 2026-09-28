"""
Wireless CO2 & Air-Quality Monitor with OLED Heatmap
Board: Raspberry Pi Pico W (MicroPython)
Author: DevNode Technologies
Date: 2026-09-28

Hardware connections:
  SCD41  — I2C0 SDA=GP4, SCL=GP5
  SSD1306 OLED — I2C1 SDA=GP6, SCL=GP7 (128x64)
  DS3231 RTC (optional) — I2C0 SDA=GP4, SCL=GP5
  LED alert — GP15

Features:
  - Reads CO2 (ppm), temperature (°C), humidity (%) every 5 s
  - Renders a scrolling 24-column heatmap on the OLED
  - Publishes readings to MQTT broker (WiFi)
  - Serves a live JSON endpoint at http://pico.local/
  - Fires a webhook POST when CO2 > threshold
"""

import time
import network
import ujson
import usocket as socket
from machine import I2C, Pin, SoftI2C
import scd4x        # install: mip.install("scd4x")  (Peter Hinch's driver)
import ssd1306      # install: mip.install("micropython-ssd1306")

# ── CONFIG ────────────────────────────────────────────────────────────────────
WIFI_SSID    = "YOUR_SSID"
WIFI_PASS    = "YOUR_PASSWORD"
MQTT_HOST    = "192.168.1.100"     # IP of your Mosquitto broker
MQTT_PORT    = 1883
MQTT_TOPIC   = b"home/air_quality"
WEBHOOK_URL  = "http://your-alert-server/webhook"
CO2_WARN_PPM = 1000                # fire webhook above this level

SAMPLE_INTERVAL_S = 5
OLED_COLS         = 24             # heatmap columns (pixels per reading)

# ── I2C BUSES ─────────────────────────────────────────────────────────────────
i2c0 = I2C(0, sda=Pin(4), scl=Pin(5), freq=100_000)   # SCD41 (+ RTC)
i2c1 = SoftI2C(sda=Pin(6), scl=Pin(7), freq=400_000)  # OLED

# ── PERIPHERALS ───────────────────────────────────────────────────────────────
oled    = ssd1306.SSD1306_I2C(128, 64, i2c1)
sensor  = scd4x.SCD4X(i2c0)
led     = Pin(15, Pin.OUT)

sensor.stop_periodic_measurement()
sensor.start_periodic_measurement()
time.sleep(5)   # SCD41 needs ~5 s warm-up

# ── WIFI ──────────────────────────────────────────────────────────────────────
def wifi_connect():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        wlan.connect(WIFI_SSID, WIFI_PASS)
        for _ in range(20):
            if wlan.isconnected():
                break
            time.sleep(0.5)
    return wlan.isconnected()

wifi_ok = wifi_connect()

# ── MINIMAL MQTT (no external lib needed for publish-only) ────────────────────
def mqtt_publish(payload: bytes):
    """Bare-metal MQTT PUBLISH without an external library."""
    try:
        s = socket.socket()
        s.settimeout(3)
        s.connect(socket.getaddrinfo(MQTT_HOST, MQTT_PORT)[0][-1])
        # CONNECT packet
        cid = b"pico_aq_monitor"
        pkt = (b"\x10" +
               bytes([len(b"\x00\x04MQTT\x04\x02\x00\x3c\x00" + bytes([len(cid)]) + cid) + 2]) +
               b"\x00\x04MQTT\x04\x02\x00\x3c" +
               bytes([0, len(cid)]) + cid)
        s.send(pkt)
        time.sleep_ms(100)
        # PUBLISH (QoS 0)
        topic = MQTT_TOPIC
        msg   = payload
        pub   = (b"\x30" +
                 bytes([2 + len(topic) + len(msg)]) +
                 bytes([0, len(topic)]) + topic + msg)
        s.send(pub)
        s.close()
    except Exception as e:
        print("MQTT error:", e)


# ── WEBHOOK ───────────────────────────────────────────────────────────────────
def send_webhook(co2, temp, hum):
    try:
        body = ujson.dumps({"co2": co2, "temp": temp, "hum": hum, "alert": "CO2_HIGH"}).encode()
        host, path = WEBHOOK_URL.replace("http://", "").split("/", 1)
        s = socket.socket()
        s.settimeout(4)
        s.connect(socket.getaddrinfo(host, 80)[0][-1])
        s.send(
            f"POST /{path} HTTP/1.0\r\nHost: {host}\r\n"
            f"Content-Type: application/json\r\nContent-Length: {len(body)}\r\n\r\n"
            .encode() + body
        )
        s.close()
    except Exception as e:
        print("Webhook error:", e)


# ── OLED HEATMAP ──────────────────────────────────────────────────────────────
history = []   # rolling list of (co2, col_x)

def co2_to_row(co2, min_ppm=400, max_ppm=2000, height=40):
    """Map CO2 ppm to a bar height in pixels (bottom-aligned)."""
    ratio = max(0, min(1, (co2 - min_ppm) / (max_ppm - min_ppm)))
    return int(ratio * height)

def render_oled(co2, temp, hum):
    oled.fill(0)
    # Header row
    oled.text(f"CO2:{co2:4}ppm", 0, 0)
    oled.text(f"T:{temp:.1f}C H:{hum:.0f}%", 0, 9)
    # Heatmap baseline at y=55, height 40 px
    baseline = 55
    col_w    = 5   # pixels per column
    for i, (val, _) in enumerate(history[-OLED_COLS:]):
        h    = co2_to_row(val)
        x    = i * col_w
        # pick shade: dim if ok, bright if warning
        fill = 1
        oled.fill_rect(x, baseline - h, col_w - 1, h, fill)
    oled.hline(0, baseline, 128, 1)
    oled.text("400", 0, 57)
    oled.text("2k", 108, 57)
    oled.show()


# ── TINY HTTP SERVER ──────────────────────────────────────────────────────────
last_reading = {"co2": 0, "temp": 0.0, "hum": 0.0}

def http_serve_once():
    """Answer one HTTP request then return (non-blocking via settimeout)."""
    srv = socket.socket()
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind(("0.0.0.0", 80))
    srv.listen(1)
    srv.settimeout(0.05)
    try:
        conn, _ = srv.accept()
        conn.recv(512)   # discard request
        body = ujson.dumps(last_reading).encode()
        conn.send(
            b"HTTP/1.0 200 OK\r\nContent-Type: application/json\r\n"
            b"Access-Control-Allow-Origin: *\r\n\r\n" + body
        )
        conn.close()
    except OSError:
        pass
    srv.close()


# ── MAIN LOOP ─────────────────────────────────────────────────────────────────
print("DevNode Pico W Air-Quality Monitor — starting")
webhook_cooldown = 0   # seconds until next webhook is allowed

while True:
    if sensor.data_ready:
        co2  = sensor.CO2
        temp = sensor.temperature
        hum  = sensor.relative_humidity
        last_reading.update({"co2": co2, "temp": round(temp, 1), "hum": round(hum, 1)})

        history.append((co2, 0))
        if len(history) > OLED_COLS * 2:
            history.pop(0)

        render_oled(co2, temp, hum)

        if wifi_ok:
            payload = ujson.dumps(last_reading).encode()
            mqtt_publish(payload)

            if co2 > CO2_WARN_PPM and webhook_cooldown <= 0:
                led.on()
                send_webhook(co2, temp, hum)
                webhook_cooldown = 300   # 5-min silence between alerts
            else:
                led.off()

        print(f"CO2={co2} ppm  T={temp:.1f}°C  RH={hum:.1f}%")

    if wifi_ok:
        http_serve_once()

    if webhook_cooldown > 0:
        webhook_cooldown -= SAMPLE_INTERVAL_S

    time.sleep(SAMPLE_INTERVAL_S)
