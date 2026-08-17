# Pose-Controlled Smart TV Remote — Offline-First Edition

## Pose-Controlled Smart TV Remote — Offline-First Edition

**Board:** Raspberry Pi 4 — Quad-core Linux SBC (USB3, dual display, more compute headroom for local servers / light vision)
**Date:** 2026-08-17

### Overview
A webcam and a lightweight pose-estimation model translate hand gestures (swipe, palm-up, fist) into media-control commands sent to a TV or media center over the network, so 'turn up the volume' doesn't require finding a remote. Pose estimation is squarely in the compute range the Pi 4 can handle without a dedicated accelerator. A genuinely fun demo project that also teaches real applied computer vision. All logic runs locally with no cloud dependency, so it keeps working through internet outages or in network-dead zones.

### Key Components / Peripherals
- USB webcam
- Pose-estimation model (MediaPipe-style)
- Local storage (SD card / flash)

![Pose-Controlled Smart TV Remote — Offline-First Edition](https://raw.githubusercontent.com/SRECONICS/SRECONICS/main/assets/daily-posts/2026-08-17-pose-controlled-smart-tv-remote/banner.png)

![Pose-Controlled Smart TV Remote — Offline-First Edition](https://raw.githubusercontent.com/SRECONICS/SRECONICS/main/assets/daily-posts/2026-08-17-pose-controlled-smart-tv-remote/diagram.png)

### Tags
`computer vision` `home automation` `edge computing`

---
*Posted automatically as part of DevNode Technologies' daily project showcase rotation (Pico W → Zero 2 W → Pi 3 → Pi 4 → Pi 5 → PYNQ-Z2).*
