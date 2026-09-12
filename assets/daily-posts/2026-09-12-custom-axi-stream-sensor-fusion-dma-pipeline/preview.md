# Custom AXI-Stream Sensor-Fusion DMA Pipeline — Offline-First Edition

## Custom AXI-Stream Sensor-Fusion DMA Pipeline — Offline-First Edition

**Board:** PYNQ-Z2 (FPGA) — Zynq-7020 SoC (ARM Cortex-A9 + programmable logic, HLS-friendly, PYNQ/Python overlay flow)
**Date:** 2026-09-12

### Overview
Multiple sensor streams (say, an IMU and an ADC) are merged through a custom AXI-Stream DMA pipeline in programmable logic that timestamp-aligns and interleaves the data before handing a single clean stream to the ARM side, instead of software having to poll and merge each source separately. This offloads a genuinely fiddly synchronization problem onto hardware where it belongs. A great project for understanding how real sensor-fusion systems handle multi-rate data at the hardware level. All logic runs locally with no cloud dependency, so it keeps working through internet outages or in network-dead zones.

### Key Components / Peripherals
- IMU sensor
- ADC input
- Custom AXI-Stream DMA IP
- Local storage (SD card / flash)

![Custom AXI-Stream Sensor-Fusion DMA Pipeline — Offline-First Edition](https://raw.githubusercontent.com/SRECONICS/SRECONICS/main/assets/daily-posts/2026-09-12-custom-axi-stream-sensor-fusion-dma-pipeline/banner.png)

![Custom AXI-Stream Sensor-Fusion DMA Pipeline — Offline-First Edition](https://raw.githubusercontent.com/SRECONICS/SRECONICS/main/assets/daily-posts/2026-09-12-custom-axi-stream-sensor-fusion-dma-pipeline/diagram.png)

### Tags
`FPGA acceleration` `sensor fusion` `edge computing`

---
*Posted automatically as part of DevNode Technologies' daily project showcase rotation (Pico W → Zero 2 W → Pi 3 → Pi 4 → Pi 5 → PYNQ-Z2).*
