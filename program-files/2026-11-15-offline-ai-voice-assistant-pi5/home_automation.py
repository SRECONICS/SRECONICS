#!/usr/bin/env python3
"""
home_automation.py — MQTT & GPIO Home Automation Dispatcher
===========================================================
Dispatches action commands from the LLM to real-world devices via
MQTT (for smart-home hubs like Home Assistant / Mosquitto) and
direct GPIO relay control.

Install:
  pip install paho-mqtt RPi.GPIO

Usage (from main.py):
  ha = HomeAutomation(mqtt_host="192.168.1.10")
  ha.dispatch({"action": "turn_on", "target": "living_room_light"})
"""

import json
import logging
import threading
import time
from typing import Optional, Dict, Any

log = logging.getLogger(__name__)

try:
    import paho.mqtt.client as mqtt
    _HAVE_MQTT = True
except ImportError:
    log.warning("paho-mqtt not installed — MQTT disabled")
    _HAVE_MQTT = False

try:
    import RPi.GPIO as GPIO
    _HAVE_GPIO = True
except (ImportError, RuntimeError):
    log.warning("RPi.GPIO not available — GPIO control disabled")
    _HAVE_GPIO = False

# ── GPIO relay map: logical name → BCM pin ────────────────────────────────────
RELAY_MAP: Dict[str, int] = {
    "fan":          17,
    "desk_lamp":    27,
    "room_light":   22,
    "power_strip":  23,
}


class HomeAutomation:
    """
    Routes LLM action commands to MQTT topics or GPIO relay pins.

    Parameters
    ----------
    mqtt_host : str
        IP / hostname of the MQTT broker. None disables MQTT.
    mqtt_port : int
        MQTT broker port (default 1883).
    base_topic : str
        MQTT topic prefix, e.g. "home/assistant".
    """

    def __init__(
        self,
        mqtt_host: Optional[str] = None,
        mqtt_port: int = 1883,
        base_topic: str = "home/assistant",
    ):
        self._topic  = base_topic
        self._client = None

        if _HAVE_GPIO:
            GPIO.setmode(GPIO.BCM)
            GPIO.setwarnings(False)
            for pin in RELAY_MAP.values():
                GPIO.setup(pin, GPIO.OUT, initial=GPIO.HIGH)   # HIGH = relay off
            log.info("GPIO relays initialised: %s", list(RELAY_MAP.keys()))

        if _HAVE_MQTT and mqtt_host:
            self._client = mqtt.Client(client_id="pi5-voice-assistant", protocol=mqtt.MQTTv5)
            self._client.on_connect    = self._on_connect
            self._client.on_disconnect = self._on_disconnect
            try:
                self._client.connect(mqtt_host, mqtt_port, keepalive=60)
                self._client.loop_start()
                log.info("MQTT connected to %s:%d", mqtt_host, mqtt_port)
            except Exception as exc:
                log.error("MQTT connect failed: %s", exc)
                self._client = None

    # ── Public ────────────────────────────────────────────────────────────────

    def dispatch(self, cmd: Dict[str, Any]) -> bool:
        """
        Dispatch a command dict from the LLM.

        Expected keys:
          action  : "turn_on" | "turn_off" | "toggle" | "scene" | "query"
          target  : device name matching RELAY_MAP or MQTT topic suffix
          value   : optional numeric value (e.g. brightness 0–255)

        Returns True if at least one backend handled the command.
        """
        action = cmd.get("action", "").lower()
        target = cmd.get("target", "").lower().replace(" ", "_")
        value  = cmd.get("value")

        log.info("Dispatching: action=%s target=%s value=%s", action, target, value)
        handled = False

        # GPIO relay dispatch
        if _HAVE_GPIO and target in RELAY_MAP:
            pin = RELAY_MAP[target]
            if action == "turn_on":
                GPIO.output(pin, GPIO.LOW)   # LOW = relay on
                handled = True
            elif action == "turn_off":
                GPIO.output(pin, GPIO.HIGH)
                handled = True
            elif action == "toggle":
                state = GPIO.input(pin)
                GPIO.output(pin, not state)
                handled = True

        # MQTT dispatch
        if self._client and self._client.is_connected():
            topic   = f"{self._topic}/{target}"
            payload = json.dumps({"action": action, "value": value})
            self._client.publish(topic, payload, qos=1)
            handled = True
            log.debug("MQTT publish → %s : %s", topic, payload)

        if not handled:
            log.warning("No handler for command: %s", cmd)
        return handled

    def cleanup(self):
        """Release GPIO and disconnect MQTT."""
        if _HAVE_GPIO:
            # Turn off all relays safely
            for pin in RELAY_MAP.values():
                GPIO.output(pin, GPIO.HIGH)
            GPIO.cleanup()
        if self._client:
            self._client.loop_stop()
            self._client.disconnect()

    # ── MQTT callbacks ────────────────────────────────────────────────────────

    def _on_connect(self, client, userdata, flags, rc, props=None):
        log.info("MQTT broker connected (rc=%s)", rc)

    def _on_disconnect(self, client, userdata, rc, props=None):
        log.warning("MQTT broker disconnected (rc=%s)", rc)
