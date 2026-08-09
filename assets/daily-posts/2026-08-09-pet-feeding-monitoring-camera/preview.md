# Pet Feeding & Monitoring Camera — Predictive Maintenance Edition

## Pet Feeding & Monitoring Camera — Predictive Maintenance Edition

**Board:** Raspberry Pi Zero 2 W — Quad-core Linux SBC (WiFi + BT, camera connector, small form factor)
**Date:** 2026-08-09

### Overview
A camera module streams live video to a small web dashboard while a servo-driven hopper dispenses a measured portion of food on a schedule or on remote trigger. Because the Zero 2 W has enough headroom to run a lightweight web server and encode a video stream simultaneously, the whole feeder plus monitor fits on one board. It's a practical build for checking on a pet during a long day at work. A lightweight trend check on recent readings flags drift before it becomes a failure, instead of only reacting after something breaks.

### Key Components / Peripherals
- Raspberry Pi Camera Module
- Servo-driven food hopper
- Rolling-average / threshold trend logic

![Pet Feeding & Monitoring Camera — Predictive Maintenance Edition](https://raw.githubusercontent.com/SRECONICS/SRECONICS/main/assets/daily-posts/2026-08-09-pet-feeding-monitoring-camera/banner.png)

![Pet Feeding & Monitoring Camera — Predictive Maintenance Edition](https://raw.githubusercontent.com/SRECONICS/SRECONICS/main/assets/daily-posts/2026-08-09-pet-feeding-monitoring-camera/diagram.png)

### Tags
`IoT` `computer vision` `predictive maintenance`

---
*Posted automatically as part of DevNode Technologies' daily project showcase rotation (Pico W → Zero 2 W → Pi 3 → Pi 4 → Pi 5 → PYNQ-Z2).*
