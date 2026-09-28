## Wireless CO₂ & Air-Quality Monitor with OLED Heatmap — Embedded Web Server Edition

**Board:** Raspberry Pi Pico W — RP2040 dual-core @ 133 MHz, 264 KB SRAM, 2 MB flash, 802.11n WiFi (CYW43439)
**Date:** 2026-09-28

### Overview
This project turns a Raspberry Pi Pico W into a standalone indoor air-quality sentinel that reads CO₂ concentration (ppm), temperature, and relative humidity from a Sensirion SCD41 sensor every five seconds and renders a live scrolling heatmap directly on a 128×64 SSD1306 OLED — no host computer required once flashed. The Pico W simultaneously acts as a minimal HTTP JSON server on port 80 (`http://pico.local/`) so any browser or `curl` command on the local network can pull the latest readings in real time, while a bare-metal MQTT PUBLISH loop streams every sample to a Mosquitto broker for long-term logging or Home Assistant integration. When CO₂ rises above a configurable threshold (default 1 000 ppm — the level at which cognitive performance visibly degrades) the firmware fires a webhook POST to an alert endpoint and blinks a GPIO LED, with a five-minute cooldown to prevent alert flooding. Because the entire stack runs in MicroPython on the RP2040 with no Linux OS, boot-to-first-reading takes under eight seconds even after a power cut, making it reliable for unattended room monitoring.

### Key Components / Peripherals
- Raspberry Pi Pico W (RP2040 + CYW43439 WiFi module)
- Sensirion SCD41 (True CO₂ / temperature / humidity, I²C)
- SSD1306 128×64 OLED display (I²C, scrolling heatmap)
- DS3231 RTC module (optional — I²C, for timestamped CSV export)
- GPIO15 LED (alert indicator)
- Mosquitto MQTT broker on LAN (publish-only, no external library)
- Webhook endpoint for CO₂ overshoot notifications

### Program Files
| File | Purpose |
|---|---|
| `main.py` | Full MicroPython firmware — sensor polling, OLED render, MQTT publish, HTTP server, webhook |
| `boot.py` | Sets RP2040 to 133 MHz max clock before main.py runs |

```python
# Quickstart: install drivers once
import mip
mip.install("scd4x")
mip.install("micropython-ssd1306")
# Then copy boot.py and main.py to the Pico W root via Thonny or mpremote
```

![Wireless CO₂ & Air-Quality Monitor with OLED Heatmap — Embedded Web Server Edition](https://raw.githubusercontent.com/SRECONICS/SRECONICS/main/assets/daily-posts/2026-09-28-wireless-co2-air-quality-monitor-oled-heatmap/banner.png)

![Wireless CO₂ & Air-Quality Monitor with OLED Heatmap — Embedded Web Server Edition](https://raw.githubusercontent.com/SRECONICS/SRECONICS/main/assets/daily-posts/2026-09-28-wireless-co2-air-quality-monitor-oled-heatmap/diagram.png)

### Tags
`micropython` `air-quality` `iot`

---
*Posted automatically as part of DevNode Technologies' daily project showcase rotation (Pico W → Zero 2 W → Pi 3 → Pi 4 → Pi 5 → PYNQ-Z2).*
