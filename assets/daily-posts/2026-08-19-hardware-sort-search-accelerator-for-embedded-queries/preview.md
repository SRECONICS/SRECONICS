# Hardware Sort/Search Accelerator for Embedded Queries — Mobile App Edition

## Hardware Sort/Search Accelerator for Embedded Queries — Mobile App Edition

**Board:** PYNQ-Z2 (FPGA) — Zynq-7020 SoC (ARM Cortex-A9 + programmable logic, HLS-friendly, PYNQ/Python overlay flow)
**Date:** 2026-08-19

### Overview
A pipelined hardware sorting network and binary-search core built in programmable logic accelerates lookups over a fixed embedded dataset (a lookup table, sensor calibration set, or small local database) far faster than a software search loop competing for ARM cycles. It's a clean, teachable example of applying classic hardware-acceleration principles (parallelism, pipelining) to a problem that isn't signal processing or vision, which broadens the FPGA-acceleration story. Good for a portfolio that wants to show FPGA use beyond the usual DSP/vision demos. A companion phone app talks to the board over BLE/WiFi for live status and manual override, no laptop required.

### Key Components / Peripherals
- Sorting-network HLS core
- Binary-search HLS core
- BLE/WiFi companion app link

![Hardware Sort/Search Accelerator for Embedded Queries — Mobile App Edition](https://raw.githubusercontent.com/SRECONICS/SRECONICS/main/assets/daily-posts/2026-08-19-hardware-sort-search-accelerator-for-embedded-queries/banner.png)

![Hardware Sort/Search Accelerator for Embedded Queries — Mobile App Edition](https://raw.githubusercontent.com/SRECONICS/SRECONICS/main/assets/daily-posts/2026-08-19-hardware-sort-search-accelerator-for-embedded-queries/diagram.png)

### Tags
`FPGA acceleration` `mobile integration`

---
*Posted automatically as part of DevNode Technologies' daily project showcase rotation (Pico W → Zero 2 W → Pi 3 → Pi 4 → Pi 5 → PYNQ-Z2).*
