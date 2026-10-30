"""
Indoor Air Quality Monitor — Pico W Edition
============================================
Hardware:  Raspberry Pi Pico W
Sensors:   SCD40 (CO₂/Temp/RH), SGP30 (TVOC/eCO₂), PMS5003 (PM2.5)
Display:   SSD1306 128×64 OLED (I²C)
Alerts:    Telegram Bot + MQTT broker (configurable)
Dashboard: ThingSpeak channel

Requirements (upload via mpremote):
  lib/scd40.py   lib/sgp30.py   lib/pms5003.py
  lib/ssd1306.py lib/mqtt.py    lib/telegram.py
  config.py

MicroPython ≥ 1.23
"""

import time
import json
import network
import urequests
import uasyncio as asyncio
from machine import I2C, UART, Pin, SoftI2C

from config import (
    WIFI_SSID, WIFI_PASS,
    TELEGRAM_TOKEN, TELEGRAM_CHAT_ID,
    MQTT_BROKER, MQTT_USER, MQTT_PASS, MQTT_TOPIC,
    THINGSPEAK_WRITE_KEY,
)
from lib.scd40    import SCD40
from lib.sgp30    import SGP30
from lib.pms5003  import PMS5003
from lib.ssd1306  import SSD1306_I2C
from lib.mqtt     import MQTTClient

# ── GPIO pinout ────────────────────────────────────────────────
I2C_SDA   = 4      # GP4
I2C_SCL   = 5      # GP5
UART_TX   = 0      # GP0  → PMS5003 RX
UART_RX   = 1      # GP1  ← PMS5003 TX
BUZZER    = 15     # GP15 (PWM capable)
LED_R     = 13     # GP13
LED_G     = 14     # GP14
LED_B     = 12     # GP12

# ── thresholds ────────────────────────────────────────────────
CO2_WARN  = 1000   # ppm
CO2_ALARM = 2000
TVOC_WARN = 400    # ppb
PM25_WARN = 35     # µg/m³ (EPA 24-h standard)

# ── Globals ───────────────────────────────────────────────────
readings = {}
alert_cooldown = {}   # key → last alert epoch

# ──────────────────────────────────────────────────────────────
def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        print("Connecting to WiFi …")
        wlan.connect(WIFI_SSID, WIFI_PASS)
        for _ in range(20):
            if wlan.isconnected():
                break
            time.sleep(0.5)
    print("WiFi:", wlan.ifconfig())
    return wlan.isconnected()


def rgb_set(r, g, b):
    Pin(LED_R, Pin.OUT).value(r)
    Pin(LED_G, Pin.OUT).value(g)
    Pin(LED_B, Pin.OUT).value(b)


def status_led(co2, tvoc, pm25):
    if co2 > CO2_ALARM or pm25 > PM25_WARN * 2:
        rgb_set(1, 0, 0)   # RED — dangerous
    elif co2 > CO2_WARN or tvoc > TVOC_WARN or pm25 > PM25_WARN:
        rgb_set(1, 1, 0)   # YELLOW — warning
    else:
        rgb_set(0, 1, 0)   # GREEN — good


async def send_telegram(msg: str):
    cooldown_key = msg[:30]
    now = time.time()
    if now - alert_cooldown.get(cooldown_key, 0) < 600:   # 10-min cooldown
        return
    alert_cooldown[cooldown_key] = now
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try:
        urequests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": msg}).close()
    except Exception as e:
        print("Telegram err:", e)


async def push_mqtt(data: dict):
    try:
        c = MQTTClient("picow_aqm", MQTT_BROKER,
                       user=MQTT_USER, password=MQTT_PASS, keepalive=30)
        c.connect()
        c.publish(MQTT_TOPIC, json.dumps(data))
        c.disconnect()
    except Exception as e:
        print("MQTT err:", e)


async def push_thingspeak(data: dict):
    url = (f"https://api.thingspeak.com/update?api_key={THINGSPEAK_WRITE_KEY}"
           f"&field1={data.get('co2',0)}&field2={data.get('tvoc',0)}"
           f"&field3={data.get('pm25',0)}&field4={data.get('temp',0)}"
           f"&field5={data.get('rh',0)}")
    try:
        urequests.get(url).close()
    except Exception as e:
        print("ThingSpeak err:", e)


def update_oled(oled, data):
    oled.fill(0)
    oled.text(f"CO2 {data.get('co2','--'):>5} ppm",  0,  0)
    oled.text(f"VOC {data.get('tvoc','--'):>5} ppb",  0, 12)
    oled.text(f"PM2 {data.get('pm25','--'):>5} ug",   0, 24)
    oled.text(f"T:{data.get('temp','--')}  RH:{data.get('rh','--')}%", 0, 36)
    quality = "GOOD"
    if (data.get('co2', 0) > CO2_ALARM or
            data.get('pm25', 0) > PM25_WARN * 2):
        quality = "DANGER"
    elif (data.get('co2', 0) > CO2_WARN or
            data.get('tvoc', 0) > TVOC_WARN or
            data.get('pm25', 0) > PM25_WARN):
        quality = "WARN"
    oled.text(f"AQI: {quality}", 0, 50)
    oled.show()


async def sensor_loop(scd, sgp, pms, oled):
    """Read sensors every 10 s; publish every 60 s."""
    publish_counter = 0
    while True:
        # SCD40 — CO₂, temperature, relative humidity
        if scd.data_ready():
            co2, temp, rh = scd.read()
            readings['co2']  = co2
            readings['temp'] = round(temp, 1)
            readings['rh']   = round(rh,   1)

        # SGP30 — TVOC, eCO₂
        tvoc, eco2 = sgp.measure_air_quality()
        readings['tvoc'] = tvoc
        readings['eco2'] = eco2

        # PMS5003 — PM1.0, PM2.5, PM10
        pm = pms.read()
        if pm:
            readings['pm25'] = pm['pm25_std']
            readings['pm10'] = pm['pm10_std']

        # Display
        update_oled(oled, readings)

        # LED
        status_led(readings.get('co2', 0),
                   readings.get('tvoc', 0),
                   readings.get('pm25', 0))

        # Alerts
        if readings.get('co2', 0) > CO2_ALARM:
            asyncio.create_task(send_telegram(
                f"⚠️ CO₂ ALARM! {readings['co2']} ppm — ventilate NOW!"))
        elif readings.get('co2', 0) > CO2_WARN:
            asyncio.create_task(send_telegram(
                f"⚠️ CO₂ warning: {readings['co2']} ppm (open a window)"))
        if readings.get('pm25', 0) > PM25_WARN:
            asyncio.create_task(send_telegram(
                f"⚠️ PM2.5 = {readings['pm25']} µg/m³  (EPA limit exceeded)"))

        # Publish every 60 s
        publish_counter += 1
        if publish_counter >= 6:
            publish_counter = 0
            asyncio.create_task(push_mqtt(dict(readings)))
            asyncio.create_task(push_thingspeak(dict(readings)))

        await asyncio.sleep(10)


async def main():
    # Peripherals
    i2c  = SoftI2C(sda=Pin(I2C_SDA), scl=Pin(I2C_SCL), freq=400_000)
    uart = UART(0, baudrate=9600, tx=Pin(UART_TX), rx=Pin(UART_RX))
    oled = SSD1306_I2C(128, 64, i2c)

    scd  = SCD40(i2c)
    sgp  = SGP30(i2c)
    pms  = PMS5003(uart)

    scd.start_periodic_measurement()
    sgp.iaq_init()
    await asyncio.sleep(2)

    # WiFi
    if connect_wifi():
        oled.fill(0); oled.text("WiFi OK", 0, 28); oled.show()
    else:
        oled.fill(0); oled.text("WiFi FAIL", 0, 28); oled.show()

    await asyncio.sleep(1)
    await sensor_loop(scd, sgp, pms, oled)


asyncio.run(main())
