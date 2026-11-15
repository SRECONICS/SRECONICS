#!/usr/bin/env python3
"""
whisper_stt.py — Speech-to-Text via whisper.cpp
================================================
Wraps the whisper.cpp CLI binary to transcribe WAV audio files locally.
No network required. Supports any model size (tiny → large-v3).

Models directory: /opt/whisper.cpp/models/
  Download: bash /opt/whisper.cpp/models/download-ggml-model.sh base.en
"""

import logging
import os
import subprocess
import tempfile

log = logging.getLogger(__name__)


class WhisperSTT:
    """Transcribes audio using the whisper.cpp main binary."""

    def __init__(
        self,
        binary: str = "/opt/whisper.cpp/main",
        model: str = "/opt/whisper.cpp/models/ggml-base.en.bin",
        language: str = "en",
        threads: int = 4,
    ):
        if not os.path.isfile(binary):
            raise FileNotFoundError(
                f"whisper.cpp binary not found: {binary}\n"
                "Build it: cd /opt/whisper.cpp && make -j4"
            )
        if not os.path.isfile(model):
            raise FileNotFoundError(
                f"Whisper model not found: {model}\n"
                "Download: bash /opt/whisper.cpp/models/download-ggml-model.sh base.en"
            )
        self._bin      = binary
        self._model    = model
        self._language = language
        self._threads  = threads
        log.info("WhisperSTT ready (model=%s)", os.path.basename(model))

    def transcribe(self, audio_path: str) -> str:
        """
        Transcribe a WAV file and return the text.

        Parameters
        ----------
        audio_path : str
            Path to a 16-bit 16 kHz mono WAV file.

        Returns
        -------
        str
            Transcribed text, stripped of leading/trailing whitespace.
        """
        # whisper.cpp outputs to stdout with -otxt flag; redirect to temp file
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as tmp:
            out_stem = tmp.name.replace(".txt", "")

        cmd = [
            self._bin,
            "-m",  self._model,
            "-f",  audio_path,
            "-l",  self._language,
            "-t",  str(self._threads),
            "--no-timestamps",
            "--output-txt",
            "--output-file", out_stem,
        ]

        log.debug("Running: %s", " ".join(cmd))
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30,
            )
            if result.returncode != 0:
                log.error("Whisper stderr: %s", result.stderr)
                return ""

            txt_path = out_stem + ".txt"
            if os.path.isfile(txt_path):
                with open(txt_path) as f:
                    text = f.read().strip()
                os.unlink(txt_path)
                return text
            # Fallback: parse stdout
            return result.stdout.strip()
        except subprocess.TimeoutExpired:
            log.error("Whisper transcription timed out")
            return ""
        except Exception as exc:
            log.error("Transcription error: %s", exc)
            return ""


# ── Quick test ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python whisper_stt.py <audio.wav>")
        sys.exit(1)
    stt = WhisperSTT()
    print(stt.transcribe(sys.argv[1]))
