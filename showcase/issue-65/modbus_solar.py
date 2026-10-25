#!/usr/bin/env python3
"""
Modbus RTU Solar Charge Controller Reader — Pi 4 Edition
----------------------------------------------------------
Reads live telemetry from an MPPT solar charge controller over RS-485
using the Modbus RTU protocol (common on EPEver, SRNE, Renogy clones).
Publishes panel voltage, battery voltage, charge current, and daily kWh
to MQTT so Node-RED / InfluxDB can store and display them.

Wiring (RS-485 module → Pi 4 UART):
  RS-485 DI  → GPIO14 / TXD (Pin 8)
  RS-485 RO  → GPIO15 / RXD (Pin 10)
  RS-485 DE+RE (shorted) → GPIO18 (Pin 12)  — direction control
  RS-485 A/B → charge controller RS-485 terminals

Enable UART on Pi 4: add  enable_uart=1  to /boot/config.txt and
  disable serial console: sudo raspi-config → Interface → Serial.

Dependencies:
  pip install minimalmodbus paho-mqtt
"""

import time
import json
import minimalmodbus
import paho.mqtt.client as mqtt

# ── Configuration ────────────────────────────────────────────────────────────
SERIAL_PORT     = "/dev/ttyS0"    # or /dev/ttyAMA0 on older Pi builds
BAUD_RATE       = 115200
DEVICE_ADDRESS  = 1               # Modbus slave ID (check controller DIP/menu)

MQTT_BROKER     = "localhost"
MQTT_PORT       = 1883
MQTT_TOPIC      = "home/solar"

POLL_INTERVAL_S = 10

# ── EPEver Tracer register map (common across EPEver/SRNE/many clones) ────────
# Registers at 0x3100 (INPUT, read-only, 16-bit, ×0.01 scaling)
REG_PANEL_V     = 0x3100   # PV array voltage (× 0.01 V)
REG_PANEL_I     = 0x3101   # PV array current (× 0.01 A)
REG_PANEL_P_L   = 0x3102   # PV power low word
REG_BATT_V      = 0x3104   # Battery voltage (× 0.01 V)
REG_CHARGE_I    = 0x3105   # Charging current (× 0.01 A)
REG_DAILY_KWH   = 0x330C   # Today's generated energy (× 0.01 kWh)
REG_TOTAL_KWH_L = 0x3312   # Total generated energy low word

# ── Init ──────────────────────────────────────────────────────────────────────
instrument = minimalmodbus.Instrument(SERIAL_PORT, DEVICE_ADDRESS)
instrument.serial.baudrate     = BAUD_RATE
instrument.serial.timeout      = 1.0
instrument.mode                = minimalmodbus.MODE_RTU
instrument.close_port_after_each_call = False

mqttc = mqtt.Client(client_id="pi4-solar-reader")
mqttc.connect(MQTT_BROKER, MQTT_PORT, keepalive=60)
mqttc.loop_start()


def read_register_scaled(reg: int, scale: float = 0.01) -> float:
    """Read one unsigned 16-bit holding register and apply scale factor."""
    raw = instrument.read_register(reg, functioncode=4)
    return round(raw * scale, 3)


def read_solar_telemetry() -> dict:
    return {
        "panel_V":      read_register_scaled(REG_PANEL_V),
        "panel_I":      read_register_scaled(REG_PANEL_I),
        "panel_W":      round(
            read_register_scaled(REG_PANEL_V) * read_register_scaled(REG_PANEL_I), 1
        ),
        "battery_V":    read_register_scaled(REG_BATT_V),
        "charge_I":     read_register_scaled(REG_CHARGE_I),
        "daily_kWh":    read_register_scaled(REG_DAILY_KWH),
    }


print(f"Solar Modbus reader started — polling {SERIAL_PORT} every {POLL_INTERVAL_S} s")

try:
    while True:
        try:
            data = read_solar_telemetry()
            payload = json.dumps(data)
            mqttc.publish(MQTT_TOPIC, payload, qos=1)
            print(f"[{time.strftime('%H:%M:%S')}] Solar: {payload}")
        except minimalmodbus.ModbusException as e:
            print(f"Modbus error: {e}")
        time.sleep(POLL_INTERVAL_S)

except KeyboardInterrupt:
    print("Solar reader stopped.")
    mqttc.loop_stop()
