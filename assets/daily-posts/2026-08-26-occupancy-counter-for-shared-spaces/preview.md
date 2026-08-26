# Occupancy Counter for Shared Spaces — Offline-First Edition

## Occupancy Counter for Shared Spaces — Offline-First Edition

**Board:** Raspberry Pi Pico W — Microcontroller (RP2040, dual-core Cortex-M0+, WiFi + BLE)
**Date:** 2026-08-26

### Overview
Paired PIR and ultrasonic sensors at a doorway distinguish entry from exit direction, letting the Pico W maintain a live occupancy count for a meeting room or makerspace. The count is exposed over WiFi as a small JSON endpoint any dashboard can poll. It solves the very real 'is this room actually free' problem cheaply. All logic runs locally with no cloud dependency, so it keeps working through internet outages or in network-dead zones.

### Key Components / Peripherals
- 2x PIR motion sensors
- Ultrasonic distance sensor
- Local storage (SD card / flash)

![Occupancy Counter for Shared Spaces — Offline-First Edition](https://raw.githubusercontent.com/SRECONICS/SRECONICS/main/assets/daily-posts/2026-08-26-occupancy-counter-for-shared-spaces/banner.png)

![Occupancy Counter for Shared Spaces — Offline-First Edition](https://raw.githubusercontent.com/SRECONICS/SRECONICS/main/assets/daily-posts/2026-08-26-occupancy-counter-for-shared-spaces/diagram.png)

### Tags
`IoT` `home automation` `edge computing`

---
*Posted automatically as part of DevNode Technologies' daily project showcase rotation (Pico W → Zero 2 W → Pi 3 → Pi 4 → Pi 5 → PYNQ-Z2).*
