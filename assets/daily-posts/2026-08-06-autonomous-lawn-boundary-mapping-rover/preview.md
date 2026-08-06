# Autonomous Lawn-Boundary Mapping Rover — Mobile App Edition

## Autonomous Lawn-Boundary Mapping Rover — Mobile App Edition

**Board:** Raspberry Pi 5 — Highest-compute Linux SBC (PCIe, fastest CPU, best fit for edge AI / vision / robotics)
**Date:** 2026-08-06

### Overview
A small rover combines a downward camera, wheel encoders, and a basic GPS module to trace and record a lawn's boundary on a first manual lap, then plans coverage paths for future autonomous mowing runs (the mowing blade itself is left out of scope for safety). The mapping and path-planning math genuinely needs the Pi 5's compute margin to run in real time on a moving platform. A strong, safety-conscious entry point into autonomous ground-vehicle robotics. A companion phone app talks to the board over BLE/WiFi for live status and manual override, no laptop required.

### Key Components / Peripherals
- GPS module
- Wheel encoders
- Downward-facing camera
- BLE/WiFi companion app link

![Autonomous Lawn-Boundary Mapping Rover — Mobile App Edition](https://raw.githubusercontent.com/SRECONICS/SRECONICS/main/assets/daily-posts/2026-08-06-autonomous-lawn-boundary-mapping-rover/banner.png)

![Autonomous Lawn-Boundary Mapping Rover — Mobile App Edition](https://raw.githubusercontent.com/SRECONICS/SRECONICS/main/assets/daily-posts/2026-08-06-autonomous-lawn-boundary-mapping-rover/diagram.png)

### Tags
`robotics` `computer vision` `mobile integration`

---
*Posted automatically as part of DevNode Technologies' daily project showcase rotation (Pico W → Zero 2 W → Pi 3 → Pi 4 → Pi 5 → PYNQ-Z2).*
