#!/usr/bin/env bash
# One-shot setup for Raspberry Pi 5 (64-bit Bookworm)
set -euo pipefail
sudo apt-get update -y
sudo apt-get install -y python3-pip python3-venv espeak-ng libespeak1 python3-opencv libcamera-apps
python3 -m venv .venv --system-site-packages
source .venv/bin/activate
pip install --upgrade pip
pip install mediapipe tflite-runtime pyttsx3
mkdir -p models
echo "Setup done. Run: python gesture_classifier.py"
