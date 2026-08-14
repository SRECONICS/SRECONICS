# Line-Following Robot Base Controller — Solar-Powered Edition

## Line-Following Robot Base Controller — Solar-Powered Edition

**Board:** Raspberry Pi Pico W — Microcontroller (RP2040, dual-core Cortex-M0+, WiFi + BLE)
**Date:** 2026-08-14

### Overview
A 5-channel IR reflectance array feeds a simple PID loop running on one Pico W core while the other handles WiFi telemetry, driving a two-motor chassis through an H-bridge driver. Splitting control and networking across the two RP2040 cores keeps the motor loop jitter-free even while streaming status. It's a solid, well-instrumented base for a robotics club's first line-follower. A small solar panel and LiPo charge controller keep it running unattended for weeks, which matters for anything mounted outdoors.

### Key Components / Peripherals
- 5-channel IR reflectance array
- Dual-motor H-bridge driver
- 2x DC gear motors
- Solar panel + LiPo charge controller

![Line-Following Robot Base Controller — Solar-Powered Edition](https://raw.githubusercontent.com/SRECONICS/SRECONICS/main/assets/daily-posts/2026-08-14-line-following-robot-base-controller/banner.png)

![Line-Following Robot Base Controller — Solar-Powered Edition](https://raw.githubusercontent.com/SRECONICS/SRECONICS/main/assets/daily-posts/2026-08-14-line-following-robot-base-controller/diagram.png)

### Tags
`robotics` `IoT` `sustainable tech`

---
*Posted automatically as part of DevNode Technologies' daily project showcase rotation (Pico W → Zero 2 W → Pi 3 → Pi 4 → Pi 5 → PYNQ-Z2).*
