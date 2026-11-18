#!/usr/bin/env python3
"""
sensor_node.py — Main daemon for Solar-Powered LoRaWAN Environmental Sensor Node
Zero 2 W Edition — Deep-sleep loop, sensor read, LoRa uplink, watchdog
"""

import time
import json
import signal
import sys
from pathlib import Path

# Local modules
from bme680_driver import BME680
from lorawan_stack import LoRaWANStack
from power_mgmt import PowerManager

CONFIG_PATH = Path(__file__).parent / "config.json"

class SensorNode:
    def __init__(self):
        with open(CONFIG_PATH) as f:
            self.config = json.load(f)
        
        self.sensor = BME680(i2c_bus=1, address=0x77)
        self.lorawan = LoRaWANStack(
            dev_eui=self.config["dev_eui"],
            app_eui=self.config["app_eui"],
            app_key=self.config["app_key"],
            region=self.config.get("region", "EU868")
        )
        self.power = PowerManager(rtc_bus=1, rtc_addr=0x68, wake_gpio=4)
        
        self.sleep_interval = self.config.get("sleep_interval_sec", 900)  # 15 min
        self.running = True
        
        signal.signal(signal.SIGTERM, self._shutdown)
        signal.signal(signal.SIGINT, self._shutdown)

    def _shutdown(self, signum, frame):
        print("Shutdown signal received")
        self.running = False

    def run(self):
        print(f"Starting sensor node: {self.config['device_name']}")
        
        # Initial OTAA join
        if not self.lorawan.join_otaa():
            print("ERROR: Failed to join LoRaWAN network")
            return 1
        
        print("Joined network successfully")
        
        while self.running:
            cycle_start = time.time()
            
            # 1. Read sensors
            try:
                readings = self.sensor.read_all()
                print(f"Readings: {readings}")
            except Exception as e:
                print(f"Sensor read failed: {e}")
                readings = {}
            
            # 2. Prepare payload (Cayenne LPP format)
            payload = self._encode_payload(readings)
            
            # 3. Transmit via LoRaWAN
            try:
                confirmed = self.config.get("confirmed_uplinks", True)
                self.lorawan.send(payload, confirmed=confirmed, port=1)
                print(f"Uplink sent ({len(payload)} bytes)")
            except Exception as e:
                print(f"Uplink failed: {e}")
            
            # 4. Battery voltage check
            vbat = self.power.read_battery_voltage()
            print(f"Battery: {vbat:.2f} V")
            if vbat < 3.3:
                print("WARNING: Low battery!")
            
            # 5. Schedule next wake
            elapsed = time.time() - cycle_start
            sleep_for = max(1, self.sleep_interval - elapsed)
            
            print(f"Sleeping for {sleep_for:.0f} seconds...")
            self.power.deep_sleep(sleep_for)
        
        return 0

    def _encode_payload(self, readings):
        """Encode readings as Cayenne LPP payload."""
        payload = bytearray()
        
        # Temperature (channel 1, type 0x67 = 2 bytes, 0.1°C resolution)
        if "temperature" in readings:
            payload.extend([0x01, 0x67])
            temp_val = int(readings["temperature"] * 10)
            payload.extend(temp_val.to_bytes(2, 'big', signed=True))
        
        # Humidity (channel 2, type 0x68 = 1 byte, 0.5% resolution)
        if "humidity" in readings:
            payload.extend([0x02, 0x68])
            hum_val = int(readings["humidity"] * 2)
            payload.append(min(255, hum_val))
        
        # Pressure (channel 3, type 0x73 = 2 bytes, 0.1 hPa resolution)
        if "pressure" in readings:
            payload.extend([0x03, 0x73])
            pres_val = int(readings["pressure"] * 10)
            payload.extend(pres_val.to_bytes(2, 'big'))
        
        # Gas/VOC (channel 4, custom type 0x01 = 2 bytes, raw resistance kΩ)
        if "gas_resistance" in readings:
            payload.extend([0x04, 0x01])
            gas_val = int(readings["gas_resistance"] / 1000)  # kΩ
            payload.extend(gas_val.to_bytes(2, 'big'))
        
        # Battery (channel 5, type 0x02 = 2 bytes, mV)
        if "battery_mv" in readings:
            payload.extend([0x05, 0x02])
            payload.extend(readings["battery_mv"].to_bytes(2, 'big'))
        
        return bytes(payload)


if __name__ == "__main__":
    node = SensorNode()
    sys.exit(node.run())