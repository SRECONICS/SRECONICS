#!/usr/bin/env python3
"""
alert.py — Telegram bot notification sender
Issue #64 · sreconics/sreconics · Board: Raspberry Pi 3

Sends a Telegram message + photo when detect.py saves a detection event.
Configure TELEGRAM_TOKEN and TELEGRAM_CHAT_ID via environment variables
or a .env file in the same directory.

Requirements:
    pip install requests python-dotenv

Usage (standalone test):
    TELEGRAM_TOKEN=xxx TELEGRAM_CHAT_ID=yyy python alert.py --test
"""

import argparse
import os
import time

import requests
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

TELEGRAM_TOKEN   = os.getenv("TELEGRAM_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")
API_BASE         = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"

# Simple rate-limiter: max 1 alert / 10 s per class
_last_sent: dict[str, float] = {}
RATE_LIMIT_S = 10


def send_detection_alert(event: dict) -> bool:
    """
    Send a Telegram photo alert for a detection event.

    Args:
        event: dict with keys: path (str), class (str), score (float), time (str)

    Returns:
        True on success, False on failure.
    """
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("[alert] TELEGRAM_TOKEN / TELEGRAM_CHAT_ID not set — skipping.")
        return False

    cls     = event.get("class", "unknown")
    score   = event.get("score", 0.0)
    ts      = event.get("time", "?")
    img_path = event.get("path", "")

    # Rate limit
    now = time.time()
    if now - _last_sent.get(cls, 0) < RATE_LIMIT_S:
        return False
    _last_sent[cls] = now

    caption = (
        f"🚨 *Pi 3 AI Security Camera*\n"
        f"Detected: `{cls}` ({score:.0%} confidence)\n"
        f"Time: `{ts}`\n"
        f"_sreconics/sreconics · Issue #64_"
    )

    try:
        if img_path and os.path.isfile(img_path):
            with open(img_path, "rb") as photo:
                resp = requests.post(
                    f"{API_BASE}/sendPhoto",
                    data={"chat_id": TELEGRAM_CHAT_ID, "caption": caption, "parse_mode": "Markdown"},
                    files={"photo": photo},
                    timeout=10,
                )
        else:
            resp = requests.post(
                f"{API_BASE}/sendMessage",
                json={"chat_id": TELEGRAM_CHAT_ID, "text": caption, "parse_mode": "Markdown"},
                timeout=10,
            )
        resp.raise_for_status()
        print(f"[alert] Telegram alert sent for class '{cls}'.")
        return True
    except requests.RequestException as e:
        print(f"[alert] Failed to send Telegram alert: {e}")
        return False


def send_startup_message() -> None:
    """Send a startup notification."""
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        return
    requests.post(
        f"{API_BASE}/sendMessage",
        json={
            "chat_id": TELEGRAM_CHAT_ID,
            "text": "✅ *Pi 3 AI Security Camera is online.*\nMonitoring started.",
            "parse_mode": "Markdown",
        },
        timeout=10,
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--test", action="store_true", help="Send a test message")
    args = parser.parse_args()

    if args.test:
        print("[alert] Sending test message …")
        ok = send_detection_alert({
            "class": "person",
            "score": 0.91,
            "time": "2026-10-22T12:00:00",
            "path": "",
        })
        print("Sent OK" if ok else "Failed (check TELEGRAM_TOKEN / CHAT_ID)")
    else:
        print("[alert] Import this module from detect.py. Use --test for a standalone test.")


if __name__ == "__main__":
    main()
