"""
boot.py — runs before main.py on power-up
Sets the CPU to max speed and configures the onboard LED as a heartbeat.
"""
import machine
machine.freq(133_000_000)   # RP2040 max clock
print("Pico W booted at", machine.freq() // 1_000_000, "MHz")
