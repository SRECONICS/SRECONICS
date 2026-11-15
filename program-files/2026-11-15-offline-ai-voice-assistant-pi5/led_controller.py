#!/usr/bin/env python3
"""
led_controller.py — WS2812B LED Ring Feedback
=============================================
Visual state feedback via a NeoPixel (WS2812B) LED ring on GPIO 18.
Requires the rpi_ws281x library and root (or sudo) to access hardware PWM.

Install:
  sudo pip install rpi_ws281x adafruit-circuitpython-neopixel
  sudo pip install adafruit-blinka

Wiring:
  WS2812B DIN → GPIO 18 (Pin 12)
  5 V         → 5 V rail
  GND         → GND
"""

import logging
import time
from typing import Optional

log = logging.getLogger(__name__)

try:
    import board
    import neopixel
    _HW = True
except ImportError:
    log.warning("neopixel not installed or not on Pi — LED control simulated")
    _HW = False


# ── Colour presets ────────────────────────────────────────────────────────────
IDLE_COLOR      = (0,   16,  32)    # dim blue
LISTEN_COLOR    = (0,   64,  200)   # bright blue — listening
THINK_COLOR     = (200, 140, 0)     # amber — processing
SPEAK_COLOR     = (0,   180, 60)    # green — speaking
ERROR_COLOR     = (180, 0,   0)     # red — error
OFF_COLOR       = (0,   0,   0)


class LEDController:
    """
    Controls a WS2812B NeoPixel ring to reflect assistant state.

    Parameters
    ----------
    pin : int
        GPIO BCM pin number (default 18 — hardware PWM capable).
    count : int
        Number of LEDs in the ring.
    brightness : float
        Global brightness 0.0–1.0.
    """

    def __init__(self, pin: int = 18, count: int = 12, brightness: float = 0.4):
        self._count      = count
        self._brightness = brightness
        self._pixels     = None

        if _HW:
            import board as _board
            pin_map = {
                18: _board.D18,
                12: _board.D12,
                21: _board.D21,
            }
            hw_pin = pin_map.get(pin, _board.D18)
            self._pixels = neopixel.NeoPixel(
                hw_pin, count, brightness=brightness,
                auto_write=False, pixel_order=neopixel.GRB
            )
            log.info("LEDController: %d LEDs on GPIO %d", count, pin)
        else:
            log.info("LEDController: simulation mode (%d LEDs)", count)

    # ── State methods ─────────────────────────────────────────────────────────

    def idle(self):
        """Dim blue pulse — waiting for hotword."""
        self._fill(IDLE_COLOR)

    def listening(self):
        """Bright blue spin — actively capturing speech."""
        self._spin(LISTEN_COLOR, steps=12, delay=0.04)

    def thinking(self):
        """Amber breathing — LLM inference in progress."""
        self._breathe(THINK_COLOR, cycles=2)

    def speaking(self):
        """Green fill — TTS playback."""
        self._fill(SPEAK_COLOR)

    def error(self, duration: float = 2.0):
        """Red flash — something went wrong."""
        self._flash(ERROR_COLOR, times=3, duration=duration)

    def off(self):
        """Turn all LEDs off."""
        self._fill(OFF_COLOR)

    # ── Animations ────────────────────────────────────────────────────────────

    def _fill(self, color):
        if self._pixels:
            self._pixels.fill(color)
            self._pixels.show()
        else:
            log.debug("LED fill: %s", color)

    def _spin(self, color, steps: int = 12, delay: float = 0.05):
        if self._pixels:
            for i in range(steps):
                self._pixels.fill(OFF_COLOR)
                self._pixels[i % self._count] = color
                self._pixels.show()
                time.sleep(delay)
        else:
            log.debug("LED spin: %s", color)

    def _breathe(self, color, cycles: int = 2, steps: int = 20):
        if self._pixels:
            r, g, b = color
            for _ in range(cycles):
                for step in range(steps):
                    t  = step / steps
                    br = 0.5 * (1 - __import__("math").cos(__import__("math").pi * t))
                    self._pixels.fill((int(r*br), int(g*br), int(b*br)))
                    self._pixels.show()
                    time.sleep(0.04)
                for step in range(steps, 0, -1):
                    t  = step / steps
                    br = 0.5 * (1 - __import__("math").cos(__import__("math").pi * t))
                    self._pixels.fill((int(r*br), int(g*br), int(b*br)))
                    self._pixels.show()
                    time.sleep(0.04)
        else:
            log.debug("LED breathe: %s x%d", color, cycles)

    def _flash(self, color, times: int = 3, duration: float = 2.0):
        delay = duration / (times * 2)
        for _ in range(times):
            self._fill(color)
            time.sleep(delay)
            self._fill(OFF_COLOR)
            time.sleep(delay)
