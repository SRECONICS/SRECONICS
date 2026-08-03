# Pet Feeding & Monitoring Camera — Fail-Safe Edition

## Pet Feeding & Monitoring Camera — Fail-Safe Edition

**Board:** Raspberry Pi Zero 2 W — Quad-core Linux SBC (WiFi + BT, camera connector, small form factor)
**Date:** 2026-08-03

### Overview
A camera module streams live video to a small web dashboard while a servo-driven hopper dispenses a measured portion of food on a schedule or on remote trigger. Because the Zero 2 W has enough headroom to run a lightweight web server and encode a video stream simultaneously, the whole feeder plus monitor fits on one board. It's a practical build for checking on a pet during a long day at work. A watchdog timer and a defined power-loss behavior make sure the system fails to a safe state instead of hanging silently.

### Key Components / Peripherals
- Raspberry Pi Camera Module
- Servo-driven food hopper
- Watchdog timer / backup power path

![Pet Feeding & Monitoring Camera — Fail-Safe Edition](https://raw.githubusercontent.com/SRECONICS/SRECONICS/main/assets/daily-posts/2026-08-03-pet-feeding-monitoring-camera/banner.png)

![Pet Feeding & Monitoring Camera — Fail-Safe Edition](https://raw.githubusercontent.com/SRECONICS/SRECONICS/main/assets/daily-posts/2026-08-03-pet-feeding-monitoring-camera/diagram.png)

### Tags
`IoT` `computer vision` `reliability engineering`

---
*Posted automatically as part of DevNode Technologies' daily project showcase rotation (Pico W → Zero 2 W → Pi 3 → Pi 4 → Pi 5 → PYNQ-Z2).*
