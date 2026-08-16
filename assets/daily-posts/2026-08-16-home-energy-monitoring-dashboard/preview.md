# Home Energy Monitoring Dashboard — Offline-First Edition

## Home Energy Monitoring Dashboard — Offline-First Edition

**Board:** Raspberry Pi 3 — Quad-core Linux SBC (WiFi + Bluetooth, general-purpose home automation / robotics hub)
**Date:** 2026-08-16

### Overview
Non-invasive CT clamp sensors around the main incoming lines let the Pi 3 measure whole-home power draw without touching any wiring, feeding a local dashboard that breaks usage into rough per-circuit estimates. Because it's completely local, there's no per-device subscription like commercial energy monitors charge. Seeing where power actually goes tends to change behavior fast, which is the whole point. All logic runs locally with no cloud dependency, so it keeps working through internet outages or in network-dead zones.

### Key Components / Peripherals
- CT clamp current sensors
- ADC breakout (ADS1115)
- Local storage (SD card / flash)

![Home Energy Monitoring Dashboard — Offline-First Edition](https://raw.githubusercontent.com/SRECONICS/SRECONICS/main/assets/daily-posts/2026-08-16-home-energy-monitoring-dashboard/banner.png)

![Home Energy Monitoring Dashboard — Offline-First Edition](https://raw.githubusercontent.com/SRECONICS/SRECONICS/main/assets/daily-posts/2026-08-16-home-energy-monitoring-dashboard/diagram.png)

### Tags
`IoT` `home automation` `edge computing`

---
*Posted automatically as part of DevNode Technologies' daily project showcase rotation (Pico W → Zero 2 W → Pi 3 → Pi 4 → Pi 5 → PYNQ-Z2).*
