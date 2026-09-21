#!/usr/bin/env micropython
"""
LoRa Sensor Node — MicroPython (RP2040 / ESP32)
Reads BME280 (temp/hum/pressure) and transmits JSON over LoRa.

Wiring (SX1276 / RFM95W):
  MISO -> GP16   MOSI -> GP19
  SCK  -> GP18   CS   -> GP17
  RST  -> GP20   IRQ  -> GP21

Install: mip.install("micropython-bme280")
"""
import time
import json
import struct
from machine import SPI, Pin
import bme280  # micropython-bme280

# ─── CONFIG ───────────────────────────────────────────────────────────────
NODE_ID    = "A"          # change per node: A, B, C …
LORA_FREQ  = 915_000_000  # 915 MHz
TX_INTERVAL_S = 30        # seconds between readings

# ─── SIMPLE RFM9x LoRa DRIVER (bit-bang) ──────────────────────────────────
REG_FIFO           = 0x00
REG_OP_MODE        = 0x01
REG_FRF_MSB        = 0x06
REG_FRF_MID        = 0x07
REG_FRF_LSB        = 0x08
REG_PA_CONFIG      = 0x09
REG_LNA            = 0x0C
REG_FIFO_ADDR_PTR  = 0x0D
REG_FIFO_TX_BASE   = 0x0E
REG_FIFO_RX_BASE   = 0x0F
REG_IRQ_FLAGS      = 0x12
REG_PAYLOAD_LENGTH = 0x22
REG_MODEM_CONFIG_1 = 0x1D
REG_MODEM_CONFIG_2 = 0x1E
REG_MODEM_CONFIG_3 = 0x26
REG_DIO_MAPPING_1  = 0x40
REG_VERSION        = 0x42

MODE_SLEEP   = 0x80
MODE_STDBY   = 0x81
MODE_TX      = 0x83
MODE_RXCONT  = 0x85
LONG_RANGE   = 0x80


class LoRa:
    def __init__(self, spi, cs, rst, freq):
        self._spi = spi
        self._cs  = cs
        self._rst = rst
        self._reset()
        assert self._read(REG_VERSION) == 0x12, "RFM95 not found"
        self._write(REG_OP_MODE, MODE_SLEEP)
        self._set_freq(freq)
        self._write(REG_FIFO_TX_BASE, 0x00)
        self._write(REG_FIFO_RX_BASE, 0x00)
        self._write(REG_LNA, 0x23)          # max gain
        self._write(REG_MODEM_CONFIG_1, 0x72)
        self._write(REG_MODEM_CONFIG_2, 0x74)
        self._write(REG_MODEM_CONFIG_3, 0x04)
        self._write(REG_PA_CONFIG, 0x8F)    # +17 dBm
        self._write(REG_OP_MODE, MODE_STDBY)

    def _reset(self):
        self._rst.value(0); time.sleep_ms(10)
        self._rst.value(1); time.sleep_ms(10)

    def _read(self, reg):
        self._cs.value(0)
        self._spi.write(bytes([reg & 0x7F]))
        val = self._spi.read(1)
        self._cs.value(1)
        return val[0]

    def _write(self, reg, val):
        self._cs.value(0)
        self._spi.write(bytes([reg | 0x80, val]))
        self._cs.value(1)

    def _set_freq(self, freq):
        frf = int((freq << 19) // 32_000_000)
        self._write(REG_FRF_MSB, (frf >> 16) & 0xFF)
        self._write(REG_FRF_MID, (frf >>  8) & 0xFF)
        self._write(REG_FRF_LSB,  frf        & 0xFF)

    def send(self, payload: bytes):
        self._write(REG_OP_MODE, MODE_STDBY)
        self._write(REG_FIFO_ADDR_PTR, 0x00)
        for b in payload:
            self._write(REG_FIFO, b)
        self._write(REG_PAYLOAD_LENGTH, len(payload))
        self._write(REG_OP_MODE, MODE_TX)
        # wait TX done (IRQ bit 3)
        for _ in range(200):
            if self._read(REG_IRQ_FLAGS) & 0x08:
                break
            time.sleep_ms(10)
        self._write(REG_IRQ_FLAGS, 0xFF)  # clear flags
        self._write(REG_OP_MODE, MODE_STDBY)


# ─── HARDWARE INIT ────────────────────────────────────────────────────────
spi = SPI(0, baudrate=1_000_000, polarity=0, phase=0,
          sck=Pin(18), mosi=Pin(19), miso=Pin(16))
cs  = Pin(17, Pin.OUT, value=1)
rst = Pin(20, Pin.OUT, value=1)

from machine import I2C
i2c   = I2C(1, scl=Pin(27), sda=Pin(26), freq=400_000)
bme   = bme280.BME280(i2c=i2c)
lora  = LoRa(spi, cs, rst, LORA_FREQ)

print(f"Node {NODE_ID} ready — transmitting every {TX_INTERVAL_S}s")

# ─── MAIN LOOP ────────────────────────────────────────────────────────────
while True:
    temp, pres, hum = bme.read_compensated_data()
    temp /= 100.0
    pres /= 25600.0  # Pa -> hPa
    hum  /= 1024.0

    for sensor, value, unit in [
        ("temp", temp, "C"),
        ("hum",  hum,  "%"),
        ("pres", pres, "hPa"),
    ]:
        packet = json.dumps({"id": NODE_ID, "s": sensor,
                             "v": round(value, 2), "u": unit})
        lora.send(packet.encode())
        print(f"TX  node={NODE_ID}  {sensor}={value:.2f}{unit}")
        time.sleep_ms(200)

    time.sleep(TX_INTERVAL_S)
