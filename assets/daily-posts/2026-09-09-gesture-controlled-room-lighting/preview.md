# Gesture-Controlled Room Lighting — Cloud Dashboard Edition

## Gesture-Controlled Room Lighting — Cloud Dashboard Edition

**Board:** Raspberry Pi 3 — Quad-core Linux SBC (WiFi + Bluetooth, general-purpose home automation / robotics hub)
**Date:** 2026-09-09

### Overview
An IR gesture sensor near a light switch recognizes a handful of swipe gestures (up, down, left, right) and maps them to relay-controlled lighting scenes, giving touchless control without any voice assistant in the loop. It's aimed at kitchens or workshops where hands are often full or dirty. The gesture sensor's onboard proximity detection also acts as a simple occupancy cue for auto-off. Telemetry is pushed to a cloud dashboard (Grafana/ThingSpeak-style) so the system can be monitored and tuned remotely.

### Key Components / Peripherals
- IR gesture sensor (APDS-9960)
- Relay module
- Cloud MQTT broker / HTTP endpoint

![Gesture-Controlled Room Lighting — Cloud Dashboard Edition](https://raw.githubusercontent.com/SRECONICS/SRECONICS/main/assets/daily-posts/2026-09-09-gesture-controlled-room-lighting/banner.png)

![Gesture-Controlled Room Lighting — Cloud Dashboard Edition](https://raw.githubusercontent.com/SRECONICS/SRECONICS/main/assets/daily-posts/2026-09-09-gesture-controlled-room-lighting/diagram.png)

### Tags
`home automation` `cloud`

---
*Posted automatically as part of DevNode Technologies' daily project showcase rotation (Pico W → Zero 2 W → Pi 3 → Pi 4 → Pi 5 → PYNQ-Z2).*
