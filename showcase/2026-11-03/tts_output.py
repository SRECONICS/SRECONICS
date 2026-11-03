"""
Text-to-speech helper using pyttsx3 / espeak-ng backend.
"""

import pyttsx3, threading

_engine = None
_lock   = threading.Lock()


def _get_engine():
    global _engine
    if _engine is None:
        _engine = pyttsx3.init(driverName="espeak")
        _engine.setProperty("rate",   145)
        _engine.setProperty("volume", 0.95)
        for v in _engine.getProperty("voices"):
            if "en_GB" in v.id or "english" in v.name.lower():
                _engine.setProperty("voice", v.id)
                break
    return _engine


def speak(text: str):
    """Speak *text* in a daemon thread so the main loop is never blocked."""
    def _run():
        with _lock:
            eng = _get_engine()
            eng.say(text)
            eng.runAndWait()
    threading.Thread(target=_run, daemon=True).start()
