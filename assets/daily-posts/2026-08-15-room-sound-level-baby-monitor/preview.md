# Room Sound-Level & Baby Monitor — Cloud Dashboard Edition

## Room Sound-Level & Baby Monitor — Cloud Dashboard Edition

**Board:** Raspberry Pi Zero 2 W — Quad-core Linux SBC (WiFi + BT, camera connector, small form factor)
**Date:** 2026-08-15

### Overview
A microphone module continuously measures ambient sound level, and the Zero 2 W streams audio (and optionally video) only when the level crosses a threshold, notifying a parent's phone. Streaming on-demand rather than continuously saves both bandwidth and battery if running off a power bank. It's a privacy-respecting alternative to always-on commercial baby monitors since nothing leaves the house. Telemetry is pushed to a cloud dashboard (Grafana/ThingSpeak-style) so the system can be monitored and tuned remotely.

### Key Components / Peripherals
- I2S/USB microphone module
- Raspberry Pi Camera Module (optional)
- Cloud MQTT broker / HTTP endpoint

![Room Sound-Level & Baby Monitor — Cloud Dashboard Edition](https://raw.githubusercontent.com/SRECONICS/SRECONICS/main/assets/daily-posts/2026-08-15-room-sound-level-baby-monitor/banner.png)

![Room Sound-Level & Baby Monitor — Cloud Dashboard Edition](https://raw.githubusercontent.com/SRECONICS/SRECONICS/main/assets/daily-posts/2026-08-15-room-sound-level-baby-monitor/diagram.png)

### Tags
`IoT` `home automation` `cloud`

---
*Posted automatically as part of DevNode Technologies' daily project showcase rotation (Pico W → Zero 2 W → Pi 3 → Pi 4 → Pi 5 → PYNQ-Z2).*
