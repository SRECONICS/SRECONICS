# Smart Doorbell with PIR + WiFi Push Alert — Data Logger Edition

## Smart Doorbell with PIR + WiFi Push Alert — Data Logger Edition

**Board:** Raspberry Pi Pico W — Microcontroller (RP2040, dual-core Cortex-M0+, WiFi + BLE)
**Date:** 2026-08-20

### Overview
A PIR sensor wakes the Pico W from deep sleep when someone approaches the door, a piezo buzzer chimes locally, and an HTTP request fires a push notification via a free notification service. Because the whole thing sleeps between events, it runs comfortably off a small battery pack. It's a cheap way to get doorbell alerts on a phone without buying into a subscription camera ecosystem. Every reading is timestamped and logged locally, giving a historical trend view instead of just a live snapshot.

### Key Components / Peripherals
- PIR motion sensor
- Piezo buzzer
- LiPo battery + charge circuit
- Real-time clock (RTC) + logging storage

![Smart Doorbell with PIR + WiFi Push Alert — Data Logger Edition](https://raw.githubusercontent.com/SRECONICS/SRECONICS/main/assets/daily-posts/2026-08-20-smart-doorbell-with-pir-wifi-push-alert/banner.png)

![Smart Doorbell with PIR + WiFi Push Alert — Data Logger Edition](https://raw.githubusercontent.com/SRECONICS/SRECONICS/main/assets/daily-posts/2026-08-20-smart-doorbell-with-pir-wifi-push-alert/diagram.png)

### Tags
`IoT` `home automation` `data logging`

---
*Posted automatically as part of DevNode Technologies' daily project showcase rotation (Pico W → Zero 2 W → Pi 3 → Pi 4 → Pi 5 → PYNQ-Z2).*
