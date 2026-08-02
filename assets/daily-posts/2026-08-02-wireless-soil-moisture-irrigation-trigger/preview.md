# Wireless Soil Moisture & Irrigation Trigger — Data Logger Edition

## Wireless Soil Moisture & Irrigation Trigger — Data Logger Edition

**Board:** Raspberry Pi Pico W — Microcontroller (RP2040, dual-core Cortex-M0+, WiFi + BLE)
**Date:** 2026-08-02

### Overview
A capacitive soil moisture probe feeds the Pico W's ADC, and once readings drop below a calibrated threshold it fires a relay-driven pump for a set duration. Readings are pushed to an MQTT topic every few minutes over the built-in WiFi radio. It's useful for anyone tired of either overwatering potted plants or forgetting them entirely, especially over a long weekend. Every reading is timestamped and logged locally, giving a historical trend view instead of just a live snapshot.

### Key Components / Peripherals
- Capacitive soil moisture sensor
- 5V relay module
- Small DC water pump
- Real-time clock (RTC) + logging storage

![Wireless Soil Moisture & Irrigation Trigger — Data Logger Edition](https://raw.githubusercontent.com/SRECONICS/SRECONICS/main/assets/daily-posts/2026-08-02-wireless-soil-moisture-irrigation-trigger/banner.png)

![Wireless Soil Moisture & Irrigation Trigger — Data Logger Edition](https://raw.githubusercontent.com/SRECONICS/SRECONICS/main/assets/daily-posts/2026-08-02-wireless-soil-moisture-irrigation-trigger/diagram.png)

### Tags
`IoT` `home automation` `data logging`

---
*Posted automatically as part of DevNode Technologies' daily project showcase rotation (Pico W → Zero 2 W → Pi 3 → Pi 4 → Pi 5 → PYNQ-Z2).*
