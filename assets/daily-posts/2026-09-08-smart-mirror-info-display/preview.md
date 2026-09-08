# Smart Mirror Info Display — Predictive Maintenance Edition

## Smart Mirror Info Display — Predictive Maintenance Edition

**Board:** Raspberry Pi Zero 2 W — Quad-core Linux SBC (WiFi + BT, camera connector, small form factor)
**Date:** 2026-09-08

### Overview
A two-way mirror sits over a small display driven by the Zero 2 W, showing time, weather, and calendar info pulled over WiFi, while the camera module can detect 'someone standing in front of the mirror' to wake the display from a blank/idle state. It's a classic hobbyist build, but the Zero 2 W's small footprint makes it much easier to fit behind a thin mirror frame than a full-size Pi. A lightweight trend check on recent readings flags drift before it becomes a failure, instead of only reacting after something breaks.

### Key Components / Peripherals
- Small HDMI display
- Two-way acrylic mirror
- Raspberry Pi Camera Module
- Rolling-average / threshold trend logic

![Smart Mirror Info Display — Predictive Maintenance Edition](https://raw.githubusercontent.com/SRECONICS/SRECONICS/main/assets/daily-posts/2026-09-08-smart-mirror-info-display/banner.png)

![Smart Mirror Info Display — Predictive Maintenance Edition](https://raw.githubusercontent.com/SRECONICS/SRECONICS/main/assets/daily-posts/2026-09-08-smart-mirror-info-display/diagram.png)

### Tags
`home automation` `computer vision` `predictive maintenance`

---
*Posted automatically as part of DevNode Technologies' daily project showcase rotation (Pico W → Zero 2 W → Pi 3 → Pi 4 → Pi 5 → PYNQ-Z2).*
