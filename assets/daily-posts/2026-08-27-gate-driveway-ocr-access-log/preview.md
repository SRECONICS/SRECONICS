# Gate/Driveway OCR Access Log — Fail-Safe Edition

## Gate/Driveway OCR Access Log — Fail-Safe Edition

**Board:** Raspberry Pi Zero 2 W — Quad-core Linux SBC (WiFi + BT, camera connector, small form factor)
**Date:** 2026-08-27

### Overview
The camera captures a frame when a vehicle triggers a driveway sensor, and an OCR pass extracts the plate text to check against a small allow-list before logging the event with a timestamp. It's built as a personal access log/notifier rather than a security gate, since OCR accuracy varies with lighting. Still a genuinely fun way to combine a camera, a sensor, and text recognition into a single working pipeline. A watchdog timer and a defined power-loss behavior make sure the system fails to a safe state instead of hanging silently.

### Key Components / Peripherals
- Raspberry Pi Camera Module
- Driveway motion/pressure sensor
- Watchdog timer / backup power path

![Gate/Driveway OCR Access Log — Fail-Safe Edition](https://raw.githubusercontent.com/SRECONICS/SRECONICS/main/assets/daily-posts/2026-08-27-gate-driveway-ocr-access-log/banner.png)

![Gate/Driveway OCR Access Log — Fail-Safe Edition](https://raw.githubusercontent.com/SRECONICS/SRECONICS/main/assets/daily-posts/2026-08-27-gate-driveway-ocr-access-log/diagram.png)

### Tags
`computer vision` `home automation` `reliability engineering`

---
*Posted automatically as part of DevNode Technologies' daily project showcase rotation (Pico W → Zero 2 W → Pi 3 → Pi 4 → Pi 5 → PYNQ-Z2).*
