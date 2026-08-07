# Hardware Sort/Search Accelerator for Embedded Queries — Offline-First Edition

## Hardware Sort/Search Accelerator for Embedded Queries — Offline-First Edition

**Board:** PYNQ-Z2 (FPGA) — Zynq-7020 SoC (ARM Cortex-A9 + programmable logic, HLS-friendly, PYNQ/Python overlay flow)
**Date:** 2026-08-07

### Overview
A pipelined hardware sorting network and binary-search core built in programmable logic accelerates lookups over a fixed embedded dataset (a lookup table, sensor calibration set, or small local database) far faster than a software search loop competing for ARM cycles. It's a clean, teachable example of applying classic hardware-acceleration principles (parallelism, pipelining) to a problem that isn't signal processing or vision, which broadens the FPGA-acceleration story. Good for a portfolio that wants to show FPGA use beyond the usual DSP/vision demos. All logic runs locally with no cloud dependency, so it keeps working through internet outages or in network-dead zones.

### Key Components / Peripherals
- Sorting-network HLS core
- Binary-search HLS core
- Local storage (SD card / flash)

![Hardware Sort/Search Accelerator for Embedded Queries — Offline-First Edition](https://raw.githubusercontent.com/SRECONICS/SRECONICS/main/assets/daily-posts/2026-08-07-hardware-sort-search-accelerator-for-embedded-queries/banner.png)

![Hardware Sort/Search Accelerator for Embedded Queries — Offline-First Edition](https://raw.githubusercontent.com/SRECONICS/SRECONICS/main/assets/daily-posts/2026-08-07-hardware-sort-search-accelerator-for-embedded-queries/diagram.png)

### Tags
`FPGA acceleration` `edge computing`

---
*Posted automatically as part of DevNode Technologies' daily project showcase rotation (Pico W → Zero 2 W → Pi 3 → Pi 4 → Pi 5 → PYNQ-Z2).*
