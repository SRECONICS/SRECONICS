# Room Sound-Level & Baby Monitor — Data Logger Edition

## Room Sound-Level & Baby Monitor — Data Logger Edition

**Board:** Raspberry Pi Zero 2 W — Quad-core Linux SBC (WiFi + BT, camera connector, small form factor)
**Date:** 2026-07-29

### Overview
A microphone module continuously measures ambient sound level, and the Zero 2 W streams audio (and optionally video) only when the level crosses a threshold, notifying a parent's phone. Streaming on-demand rather than continuously saves both bandwidth and battery if running off a power bank. It's a privacy-respecting alternative to always-on commercial baby monitors since nothing leaves the house. Every reading is timestamped and logged locally, giving a historical trend view instead of just a live snapshot.

### Key Components / Peripherals
- I2S/USB microphone module
- Raspberry Pi Camera Module (optional)
- Real-time clock (RTC) + logging storage

![Room Sound-Level & Baby Monitor — Data Logger Edition](https://raw.githubusercontent.com/sreconics/sreconics/main/assets/daily-posts/2026-07-29-room-sound-level-baby-monitor/banner.png)

![Room Sound-Level & Baby Monitor — Data Logger Edition](https://raw.githubusercontent.com/sreconics/sreconics/main/assets/daily-posts/2026-07-29-room-sound-level-baby-monitor/diagram.png)

### Tags
`IoT` `home automation` `data logging`

---
*Posted automatically as part of DevNode Technologies' daily project showcase rotation (Pico W → Zero 2 W → Pi 3 → Pi 4 → Pi 5 → PYNQ-Z2).*
