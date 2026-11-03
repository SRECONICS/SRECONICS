# ASL Sign Language to Speech Translator — Pi 5 Edition

Real-time American Sign Language (ASL) interpreter running entirely on a
Raspberry Pi 5 with no cloud dependency.

## Hardware
| Part | Notes |
|------|-------|
| Raspberry Pi 5 (4/8 GB) | Main compute |
| USB 3.0 webcam (Logitech C920) | 640×480 @ 30 fps |
| 3.5 mm speaker / headset | TTS audio output |
| 7-inch HDMI touchscreen *(optional)* | Live landmark overlay |
| 10 000 mAh USB-C bank *(optional)* | Portable power |

## Quick start
```bash
git clone https://github.com/sreconics/sreconics
cd sreconics/showcase/2026-11-03
bash setup.sh
source .venv/bin/activate
python gesture_classifier.py
```

## Files
| File | Purpose |
|------|---------|
| `gesture_classifier.py` | Main real-time inference loop |
| `train_model.py` | MobileNetV2 → INT8 TFLite training |
| `tts_output.py` | pyttsx3 TTS helper |
| `requirements.txt` | Python dependencies |
| `setup.sh` | One-shot Pi 5 setup script |
