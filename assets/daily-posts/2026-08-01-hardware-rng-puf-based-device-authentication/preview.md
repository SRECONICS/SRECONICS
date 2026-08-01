# Hardware RNG & PUF-Based Device Authentication — Predictive Maintenance Edition

## Hardware RNG & PUF-Based Device Authentication — Predictive Maintenance Edition

**Board:** PYNQ-Z2 (FPGA) — Zynq-7020 SoC (ARM Cortex-A9 + programmable logic, HLS-friendly, PYNQ/Python overlay flow)
**Date:** 2026-08-01

### Overview
A ring-oscillator-based physical unclonable function (PUF) implemented in programmable logic derives a device-unique fingerprint from tiny manufacturing variations in the FPGA fabric itself, paired with a hardware random-number generator for challenge-response authentication that doesn't depend on storing a secret key anywhere. It's a genuinely elegant hardware-security concept: identity derived from physical imperfection rather than a stored value that can be extracted. A strong, discussion-worthy security-focused FPGA project. A lightweight trend check on recent readings flags drift before it becomes a failure, instead of only reacting after something breaks.

### Key Components / Peripherals
- Ring-oscillator PUF core
- Hardware RNG core
- Rolling-average / threshold trend logic

![Hardware RNG & PUF-Based Device Authentication — Predictive Maintenance Edition](https://raw.githubusercontent.com/SRECONICS/SRECONICS/main/assets/daily-posts/2026-08-01-hardware-rng-puf-based-device-authentication/banner.png)

![Hardware RNG & PUF-Based Device Authentication — Predictive Maintenance Edition](https://raw.githubusercontent.com/SRECONICS/SRECONICS/main/assets/daily-posts/2026-08-01-hardware-rng-puf-based-device-authentication/diagram.png)

### Tags
`FPGA acceleration` `predictive maintenance`

---
*Posted automatically as part of DevNode Technologies' daily project showcase rotation (Pico W → Zero 2 W → Pi 3 → Pi 4 → Pi 5 → PYNQ-Z2).*
