# Hardware AES Core for Secure IoT Gateway — Data Logger Edition

## Hardware AES Core for Secure IoT Gateway — Data Logger Edition

**Board:** PYNQ-Z2 (FPGA) — Zynq-7020 SoC (ARM Cortex-A9 + programmable logic, HLS-friendly, PYNQ/Python overlay flow)
**Date:** 2026-08-25

### Overview
An AES-128/256 encryption/decryption core implemented directly in programmable logic handles line-rate encryption for data passing through a small IoT gateway running on the PYNQ-Z2's ARM side, freeing the processor entirely from crypto overhead. Doing encryption in fixed hardware also sidesteps a whole category of timing-based software side-channel concerns that software AES implementations have to work around. A strong project for anyone interested in applied hardware security. Every reading is timestamped and logged locally, giving a historical trend view instead of just a live snapshot.

### Key Components / Peripherals
- AES HLS/RTL core
- AXI-Lite control interface
- Real-time clock (RTC) + logging storage

![Hardware AES Core for Secure IoT Gateway — Data Logger Edition](https://raw.githubusercontent.com/SRECONICS/SRECONICS/main/assets/daily-posts/2026-08-25-hardware-aes-core-for-secure-iot-gateway/banner.png)

![Hardware AES Core for Secure IoT Gateway — Data Logger Edition](https://raw.githubusercontent.com/SRECONICS/SRECONICS/main/assets/daily-posts/2026-08-25-hardware-aes-core-for-secure-iot-gateway/diagram.png)

### Tags
`FPGA acceleration` `data logging`

---
*Posted automatically as part of DevNode Technologies' daily project showcase rotation (Pico W → Zero 2 W → Pi 3 → Pi 4 → Pi 5 → PYNQ-Z2).*
