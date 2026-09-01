# BLE Beacon Indoor Asset Tracker — Voice-Alert Edition

## BLE Beacon Indoor Asset Tracker — Voice-Alert Edition

**Board:** Raspberry Pi Pico W — Microcontroller (RP2040, dual-core Cortex-M0+, WiFi + BLE)
**Date:** 2026-09-01

### Overview
The Pico W broadcasts a periodic BLE advertisement carrying an ID and battery level, and a handful of stationary receiver nodes log signal strength to estimate which room the tagged object is in. Deep sleep between broadcasts stretches battery life to months on a coin cell. It's a low-cost alternative to commercial BLE tags for tracking tools, bags, or lab equipment around a building. Status changes trigger a spoken alert through a small speaker, which is a lot harder to miss than a dashboard notification.

### Key Components / Peripherals
- Coin cell battery holder
- BLE receiver nodes (3+)
- Small speaker / audio amp module

![BLE Beacon Indoor Asset Tracker — Voice-Alert Edition](https://raw.githubusercontent.com/SRECONICS/SRECONICS/main/assets/daily-posts/2026-09-01-ble-beacon-indoor-asset-tracker/banner.png)

![BLE Beacon Indoor Asset Tracker — Voice-Alert Edition](https://raw.githubusercontent.com/SRECONICS/SRECONICS/main/assets/daily-posts/2026-09-01-ble-beacon-indoor-asset-tracker/diagram.png)

### Tags
`IoT` `wireless sensing` `accessibility`

---
*Posted automatically as part of DevNode Technologies' daily project showcase rotation (Pico W → Zero 2 W → Pi 3 → Pi 4 → Pi 5 → PYNQ-Z2).*
