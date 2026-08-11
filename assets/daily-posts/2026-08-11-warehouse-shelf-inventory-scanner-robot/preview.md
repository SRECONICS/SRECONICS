# Warehouse/Shelf Inventory Scanner Robot — Data Logger Edition

## Warehouse/Shelf Inventory Scanner Robot — Data Logger Edition

**Board:** Raspberry Pi 4 — Quad-core Linux SBC (USB3, dual display, more compute headroom for local servers / light vision)
**Date:** 2026-08-11

### Overview
A camera-equipped rover reads barcodes/QR codes off shelf labels while driving a preset route, cross-checking against an expected inventory list and flagging missing or misplaced items. It's a scaled-down version of the kind of inventory robot warehouses actually deploy, and a great applied-vision project for a robotics club with retail/logistics interests. The Pi 4's compute is what makes real-time barcode decoding while moving practical. Every reading is timestamped and logged locally, giving a historical trend view instead of just a live snapshot.

### Key Components / Peripherals
- Raspberry Pi Camera Module
- Barcode/QR decoding library
- Motor driver + chassis
- Real-time clock (RTC) + logging storage

![Warehouse/Shelf Inventory Scanner Robot — Data Logger Edition](https://raw.githubusercontent.com/SRECONICS/SRECONICS/main/assets/daily-posts/2026-08-11-warehouse-shelf-inventory-scanner-robot/banner.png)

![Warehouse/Shelf Inventory Scanner Robot — Data Logger Edition](https://raw.githubusercontent.com/SRECONICS/SRECONICS/main/assets/daily-posts/2026-08-11-warehouse-shelf-inventory-scanner-robot/diagram.png)

### Tags
`robotics` `computer vision` `data logging`

---
*Posted automatically as part of DevNode Technologies' daily project showcase rotation (Pico W → Zero 2 W → Pi 3 → Pi 4 → Pi 5 → PYNQ-Z2).*
