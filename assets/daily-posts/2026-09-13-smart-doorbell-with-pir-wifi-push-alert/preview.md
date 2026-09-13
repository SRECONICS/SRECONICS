# Smart Doorbell with PIR + WiFi Push Alert — Cloud Dashboard Edition

## Smart Doorbell with PIR + WiFi Push Alert — Cloud Dashboard Edition

**Board:** Raspberry Pi Pico W — Microcontroller (RP2040, dual-core Cortex-M0+, WiFi + BLE)
**Date:** 2026-09-13

### Overview
A PIR sensor wakes the Pico W from deep sleep when someone approaches the door, a piezo buzzer chimes locally, and an HTTP request fires a push notification via a free notification service. Because the whole thing sleeps between events, it runs comfortably off a small battery pack. It's a cheap way to get doorbell alerts on a phone without buying into a subscription camera ecosystem. Telemetry is pushed to a cloud dashboard (Grafana/ThingSpeak-style) so the system can be monitored and tuned remotely.

### Key Components / Peripherals
- PIR motion sensor
- Piezo buzzer
- LiPo battery + charge circuit
- Cloud MQTT broker / HTTP endpoint

![Smart Doorbell with PIR + WiFi Push Alert — Cloud Dashboard Edition](https://raw.githubusercontent.com/SRECONICS/SRECONICS/main/assets/daily-posts/2026-09-13-smart-doorbell-with-pir-wifi-push-alert/banner.png)

![Smart Doorbell with PIR + WiFi Push Alert — Cloud Dashboard Edition](https://raw.githubusercontent.com/SRECONICS/SRECONICS/main/assets/daily-posts/2026-09-13-smart-doorbell-with-pir-wifi-push-alert/diagram.png)

### Tags
`IoT` `home automation` `cloud`

---
*Posted automatically as part of DevNode Technologies' daily project showcase rotation (Pico W → Zero 2 W → Pi 3 → Pi 4 → Pi 5 → PYNQ-Z2).*
