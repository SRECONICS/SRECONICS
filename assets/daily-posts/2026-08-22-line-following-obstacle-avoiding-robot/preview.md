# Line-Following & Obstacle-Avoiding Robot — Mobile App Edition

## Line-Following & Obstacle-Avoiding Robot — Mobile App Edition

**Board:** Raspberry Pi 3 — Quad-core Linux SBC (WiFi + Bluetooth, general-purpose home automation / robotics hub)
**Date:** 2026-08-22

### Overview
An IR reflectance array handles line-following while an ultrasonic sensor overrides steering to dodge unexpected obstacles, with the Pi 3's extra headroom (versus a bare microcontroller) leaving room to log runs and stream a status feed over WiFi. It's a step up from a Pico-based line follower because the Pi 3 can run real logging and even a lightweight camera-based check alongside the core control loop. A strong club-level robotics platform. A companion phone app talks to the board over BLE/WiFi for live status and manual override, no laptop required.

### Key Components / Peripherals
- IR reflectance array
- Ultrasonic distance sensor
- Motor driver + DC motors
- BLE/WiFi companion app link

![Line-Following & Obstacle-Avoiding Robot — Mobile App Edition](https://raw.githubusercontent.com/SRECONICS/SRECONICS/main/assets/daily-posts/2026-08-22-line-following-obstacle-avoiding-robot/banner.png)

![Line-Following & Obstacle-Avoiding Robot — Mobile App Edition](https://raw.githubusercontent.com/SRECONICS/SRECONICS/main/assets/daily-posts/2026-08-22-line-following-obstacle-avoiding-robot/diagram.png)

### Tags
`robotics` `mobile integration`

---
*Posted automatically as part of DevNode Technologies' daily project showcase rotation (Pico W → Zero 2 W → Pi 3 → Pi 4 → Pi 5 → PYNQ-Z2).*
