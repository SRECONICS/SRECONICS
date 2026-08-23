# Vision-Guided Line-Maze Solving Robot — Cloud Dashboard Edition

## Vision-Guided Line-Maze Solving Robot — Cloud Dashboard Edition

**Board:** Raspberry Pi 4 — Quad-core Linux SBC (USB3, dual display, more compute headroom for local servers / light vision)
**Date:** 2026-08-23

### Overview
Instead of a plain IR reflectance array, the Pi 4 uses a downward-facing camera and a lightweight image-processing pipeline (thresholding + centroid tracking) to follow a line and detect junctions, letting it make maze-solving decisions a fixed sensor array can't. The extra compute over a Pi 3 is what keeps the vision loop fast enough for real-time steering. It's a strong step from 'follows a line' to 'actually reasons about the maze'. Telemetry is pushed to a cloud dashboard (Grafana/ThingSpeak-style) so the system can be monitored and tuned remotely.

### Key Components / Peripherals
- Raspberry Pi Camera Module
- Motor driver + DC motors
- Chassis
- Cloud MQTT broker / HTTP endpoint

![Vision-Guided Line-Maze Solving Robot — Cloud Dashboard Edition](https://raw.githubusercontent.com/SRECONICS/SRECONICS/main/assets/daily-posts/2026-08-23-vision-guided-line-maze-solving-robot/banner.png)

![Vision-Guided Line-Maze Solving Robot — Cloud Dashboard Edition](https://raw.githubusercontent.com/SRECONICS/SRECONICS/main/assets/daily-posts/2026-08-23-vision-guided-line-maze-solving-robot/diagram.png)

### Tags
`robotics` `computer vision` `cloud`

---
*Posted automatically as part of DevNode Technologies' daily project showcase rotation (Pico W → Zero 2 W → Pi 3 → Pi 4 → Pi 5 → PYNQ-Z2).*
