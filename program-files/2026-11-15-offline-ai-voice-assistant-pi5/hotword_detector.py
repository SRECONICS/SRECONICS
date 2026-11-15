#!/usr/bin/env python3
"""
hotword_detector.py — Wake-word Detection & Utterance Capture
=============================================================
Uses a simple energy-threshold approach (no external API) to detect speech
and buffer an utterance to WAV. For a production deployment, swap the
threshold detector for Porcupine or openWakeWord for a true hotword trigger.

Requirements:
  pip install pyaudio webrtcvad
"""

import io
import logging
import os
import struct
import tempfile
import threading
import time
import wave
from collections import deque
from typing import Optional

log = logging.getLogger(__name__)

try:
    import pyaudio
    import webrtcvad
    _HAVE_AUDIO = True
except ImportError:
    log.warning("pyaudio / webrtcvad not installed — audio capture disabled")
    _HAVE_AUDIO = False

SAMPLE_RATE    = 16000
FRAME_DURATION = 30     # ms (10, 20, or 30 — required by webrtcvad)
FRAME_SIZE     = int(SAMPLE_RATE * FRAME_DURATION / 1000)   # samples
CHANNELS       = 1
FORMAT         = pyaudio.paInt16 if _HAVE_AUDIO else None


class HotwordDetector:
    """
    Listens for a voice-activity-based trigger and captures an utterance.

    For true hotword ('Hey Pi') detection integrate openWakeWord:
        pip install openwakeword
        from openwakeword.model import Model
        oww = Model(wakeword_models=["hey_mycroft"])  # retrain with 'Hey Pi'
    """

    HOTWORD = "hey pi"       # for openWakeWord / Porcupine integration
    VAD_MODE = 2             # 0–3; 3 = most aggressive filtering

    def __init__(self, device_index: Optional[int] = None):
        self._device  = device_index
        self._running = False
        self._woken   = threading.Event()
        self._pa      = None
        self._vad     = None
        if _HAVE_AUDIO:
            self._pa  = pyaudio.PyAudio()
            self._vad = webrtcvad.Vad(self.VAD_MODE)
        log.info("HotwordDetector initialised (VAD mode %d)", self.VAD_MODE)

    # ── Public API ────────────────────────────────────────────────────────────

    def wait_for_hotword(self):
        """
        Block until a hotword (or loud-enough speech) is detected.
        In energy-threshold mode, any voice activity above the floor triggers.
        Replace _energy_trigger with a real hotword model for production.
        """
        if not _HAVE_AUDIO:
            log.warning("No audio libraries — simulating 2 s hotword delay")
            time.sleep(2)
            return

        self._woken.clear()
        self._running = True
        log.debug("Hotword detector listening…")

        stream = self._pa.open(
            format=FORMAT,
            channels=CHANNELS,
            rate=SAMPLE_RATE,
            input=True,
            input_device_index=self._device,
            frames_per_buffer=FRAME_SIZE,
        )
        try:
            while self._running:
                raw = stream.read(FRAME_SIZE, exception_on_overflow=False)
                if self._vad.is_speech(raw, SAMPLE_RATE):
                    self._woken.set()
                    log.debug("Voice activity detected — triggering")
                    break
        finally:
            stream.stop_stream()
            stream.close()

    def capture_utterance(self, max_seconds: float = 8.0) -> str:
        """
        Capture speech until silence (or max_seconds) and save to a temp WAV.

        Returns
        -------
        str
            Path to the saved WAV file (16-bit 16 kHz mono).
        """
        if not _HAVE_AUDIO:
            log.warning("No audio — returning empty WAV placeholder")
            return self._empty_wav()

        SILENCE_TIMEOUT = 1.5    # stop after 1.5 s silence
        frames          = []
        silent_frames   = 0
        max_frames      = int(max_seconds * 1000 / FRAME_DURATION)
        # silence threshold ~1.5 s
        silence_limit   = int(SILENCE_TIMEOUT * 1000 / FRAME_DURATION)

        stream = self._pa.open(
            format=FORMAT,
            channels=CHANNELS,
            rate=SAMPLE_RATE,
            input=True,
            input_device_index=self._device,
            frames_per_buffer=FRAME_SIZE,
        )
        log.debug("Recording utterance…")
        try:
            for _ in range(max_frames):
                raw = stream.read(FRAME_SIZE, exception_on_overflow=False)
                frames.append(raw)
                if self._vad.is_speech(raw, SAMPLE_RATE):
                    silent_frames = 0
                else:
                    silent_frames += 1
                    if silent_frames >= silence_limit:
                        break
        finally:
            stream.stop_stream()
            stream.close()

        return self._save_wav(frames)

    def stop(self):
        self._running = False
        if self._pa:
            self._pa.terminate()

    # ── Internal ──────────────────────────────────────────────────────────────

    def _save_wav(self, frames: list) -> str:
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            path = f.name
        with wave.open(path, "wb") as wf:
            wf.setnchannels(CHANNELS)
            wf.setsampwidth(2)          # 16-bit
            wf.setframerate(SAMPLE_RATE)
            wf.writeframes(b"".join(frames))
        return path

    def _empty_wav(self) -> str:
        """Return path to a silent 1-second WAV for testing."""
        samples = b"\x00\x00" * SAMPLE_RATE
        return self._save_wav([
            samples[i:i+FRAME_SIZE*2]
            for i in range(0, len(samples), FRAME_SIZE*2)
        ])
