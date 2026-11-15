#!/usr/bin/env python3
"""
piper_tts.py — Neural Text-to-Speech via Piper
===============================================
Converts text to speech offline using the Piper TTS binary and plays
it through ALSA (aplay). Zero network dependency.

Install Piper:
  wget https://github.com/rhasspy/piper/releases/latest/download/piper_arm64.tar.gz
  tar xzf piper_arm64.tar.gz -C /opt/piper
  export PATH="$PATH:/opt/piper"

Download a voice:
  cd /opt/piper/voices
  wget https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx
  wget https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx.json
"""

import logging
import os
import subprocess
import tempfile

log = logging.getLogger(__name__)


class PiperTTS:
    """
    Synthesise speech using Piper and play through ALSA.

    Parameters
    ----------
    voice_model : str
        Path to the .onnx voice model file.
    piper_binary : str
        Path to the piper executable.
    sample_rate : int
        Audio sample rate expected by ALSA (default 22050 for Piper output).
    """

    def __init__(
        self,
        voice_model: str = "/opt/piper/voices/en_US-lessac-medium.onnx",
        piper_binary: str = "piper",
        sample_rate: int = 22050,
    ):
        self._voice   = voice_model
        self._piper   = piper_binary
        self._rate    = sample_rate
        log.info("PiperTTS ready (voice=%s)", os.path.basename(voice_model))

    def speak(self, text: str, blocking: bool = True) -> None:
        """
        Synthesise *text* and play it immediately via aplay.

        Parameters
        ----------
        text : str
            Text to synthesise.
        blocking : bool
            If True (default), block until playback finishes.
        """
        if not text.strip():
            return

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            wav_path = f.name

        try:
            # Piper: stdin → WAV file
            piper_cmd = [
                self._piper,
                "--model",       self._voice,
                "--output_file", wav_path,
            ]
            log.debug("Piper cmd: %s", " ".join(piper_cmd))
            subprocess.run(
                piper_cmd,
                input=text.encode(),
                check=True,
                capture_output=True,
                timeout=20,
            )

            # Play via aplay (ALSA)
            play_cmd = ["aplay", "-q", wav_path]
            if blocking:
                subprocess.run(play_cmd, check=True, timeout=60)
            else:
                subprocess.Popen(play_cmd)
        except FileNotFoundError:
            log.error("piper binary not found — is it in PATH?")
        except subprocess.CalledProcessError as exc:
            log.error("TTS error: %s", exc.stderr.decode(errors="replace"))
        except subprocess.TimeoutExpired:
            log.error("TTS / playback timed out")
        finally:
            if os.path.isfile(wav_path):
                os.unlink(wav_path)

    def save(self, text: str, output_path: str) -> bool:
        """Synthesise *text* and save to *output_path* (WAV). Returns True on success."""
        try:
            subprocess.run(
                [self._piper, "--model", self._voice, "--output_file", output_path],
                input=text.encode(),
                check=True,
                capture_output=True,
                timeout=20,
            )
            return True
        except Exception as exc:
            log.error("TTS save error: %s", exc)
            return False


# ── Quick test ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    tts = PiperTTS()
    tts.speak("Hello! I am your offline voice assistant, running entirely on Raspberry Pi 5.")
