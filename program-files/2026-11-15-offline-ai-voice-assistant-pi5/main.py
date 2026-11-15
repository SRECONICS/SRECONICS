#!/usr/bin/env python3
"""
main.py — Offline AI Voice Assistant  (Raspberry Pi 5 Edition)
==============================================================
Entry point: orchestrates hotword detection → STT → LLM → TTS → LED feedback.

Requirements:
  pip install -r requirements.txt
  whisper.cpp built in /opt/whisper.cpp
  Ollama running:  ollama serve  (pulls model on first run)
  piper-tts binary in PATH

Usage:
  python main.py [--model mistral] [--led] [--mqtt-host 192.168.1.x]
"""

import argparse
import logging
import threading
import signal
import sys
from pathlib import Path

from hotword_detector import HotwordDetector
from whisper_stt import WhisperSTT
from ollama_chat import OllamaChat
from piper_tts import PiperTTS
from led_controller import LEDController
from home_automation import HomeAutomation

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
log = logging.getLogger("assistant")

SYSTEM_PROMPT = (
    "You are a helpful, concise voice assistant running entirely on a "
    "Raspberry Pi 5. Respond in plain language suitable for speech. "
    "Keep answers under 60 words unless the user asks for detail. "
    "For home automation commands (lights, fan, music), reply with a "
    "JSON action block: {\"action\": \"<cmd>\", \"target\": \"<device>\"}"
)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Offline AI Voice Assistant")
    p.add_argument("--model",       default="mistral",   help="Ollama model name")
    p.add_argument("--whisper-bin", default="/opt/whisper.cpp/main", help="Path to whisper.cpp binary")
    p.add_argument("--whisper-model", default="/opt/whisper.cpp/models/ggml-base.en.bin")
    p.add_argument("--piper-voice", default="/opt/piper/voices/en_US-lessac-medium.onnx")
    p.add_argument("--led",         action="store_true", help="Enable WS2812B LED ring (GPIO 18)")
    p.add_argument("--led-pin",     type=int, default=18)
    p.add_argument("--led-count",   type=int, default=12)
    p.add_argument("--mqtt-host",   default=None,        help="MQTT broker IP for home automation")
    p.add_argument("--mqtt-port",   type=int, default=1883)
    return p.parse_args()


def main():
    args = parse_args()

    # ── Subsystem init ──────────────────────────────────────────────────────
    led  = LEDController(args.led_pin, args.led_count) if args.led else None
    stt  = WhisperSTT(args.whisper_bin, args.whisper_model)
    llm  = OllamaChat(model=args.model, system_prompt=SYSTEM_PROMPT)
    tts  = PiperTTS(voice_model=args.piper_voice)
    ha   = HomeAutomation(mqtt_host=args.mqtt_host, mqtt_port=args.mqtt_port) \
           if args.mqtt_host else None
    hwd  = HotwordDetector()

    if led:
        led.idle()

    # ── Graceful shutdown ───────────────────────────────────────────────────
    def _shutdown(sig, frame):
        log.info("Shutting down…")
        if led:
            led.off()
        hwd.stop()
        sys.exit(0)

    signal.signal(signal.SIGINT,  _shutdown)
    signal.signal(signal.SIGTERM, _shutdown)

    log.info("Assistant ready. Say 'Hey Pi' to wake.")

    # ── Main loop ───────────────────────────────────────────────────────────
    while True:
        log.info("Listening for hotword…")
        hwd.wait_for_hotword()           # blocks until wake-word heard

        if led:
            led.listening()
        log.info("Wake word detected — recording utterance…")

        audio_path = hwd.capture_utterance(max_seconds=8)

        if led:
            led.thinking()
        log.info("Transcribing with Whisper…")
        text = stt.transcribe(audio_path)

        if not text.strip():
            log.warning("No speech detected, back to idle.")
            if led:
                led.idle()
            continue

        log.info("User said: %s", text)
        response = llm.chat(text)
        log.info("LLM response: %s", response)

        # Check for home automation JSON
        if ha and response.strip().startswith("{"):
            try:
                import json
                cmd = json.loads(response)
                ha.dispatch(cmd)
                response = f"Done — {cmd.get('action')} {cmd.get('target', '')}."
            except Exception:
                pass

        if led:
            led.speaking()
        tts.speak(response)

        if led:
            led.idle()


if __name__ == "__main__":
    main()
