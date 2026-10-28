#!/usr/bin/env python3
"""
notify.py — Telegram push-notification bot for Frigate NVR events.
Subscribes to MQTT topic frigate/events and sends a photo + alert
to a Telegram chat whenever a person/car is detected.

Environment variables (set in docker-compose .env):
  MQTT_HOST          IP / hostname of Mosquitto (default: localhost)
  MQTT_PORT          MQTT port (default: 1883)
  TELEGRAM_TOKEN     Bot token from @BotFather
  TELEGRAM_CHAT_ID   Target chat / group ID
  FRIGATE_URL        Frigate base URL (default: http://frigate:5000)
  MIN_SCORE          Minimum detection score to trigger (default: 0.70)
  COOLDOWN_SEC       Seconds to suppress repeat alerts for same camera (default: 30)

Install: pip install paho-mqtt requests
"""

import os, json, time, logging, requests
import paho.mqtt.client as mqtt

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-7s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger("frigate_notify")

# ── Config from environment ──────────────────────────────────────────────────
MQTT_HOST       = os.environ.get("MQTT_HOST", "localhost")
MQTT_PORT       = int(os.environ.get("MQTT_PORT", 1883))
TELEGRAM_TOKEN  = os.environ["TELEGRAM_TOKEN"]
TELEGRAM_CHAT   = os.environ["TELEGRAM_CHAT_ID"]
FRIGATE_URL     = os.environ.get("FRIGATE_URL", "http://frigate:5000")
MIN_SCORE       = float(os.environ.get("MIN_SCORE", 0.70))
COOLDOWN_SEC    = int(os.environ.get("COOLDOWN_SEC", 30))

TRACK_OBJECTS   = {"person", "car", "motorcycle", "bicycle"}

# ── State ────────────────────────────────────────────────────────────────────
last_alert: dict[str, float] = {}   # camera → last alert epoch

def send_telegram(text: str, photo_bytes: bytes | None = None) -> None:
    """Send a Telegram message with optional photo attachment."""
    base = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"
    try:
        if photo_bytes:
            resp = requests.post(
                f"{base}/sendPhoto",
                data={"chat_id": TELEGRAM_CHAT, "caption": text, "parse_mode": "HTML"},
                files={"photo": ("snap.jpg", photo_bytes, "image/jpeg")},
                timeout=15,
            )
        else:
            resp = requests.post(
                f"{base}/sendMessage",
                data={"chat_id": TELEGRAM_CHAT, "text": text, "parse_mode": "HTML"},
                timeout=10,
            )
        resp.raise_for_status()
        log.info("Telegram alert sent ✓")
    except Exception as exc:
        log.error("Telegram send failed: %s", exc)

def fetch_snapshot(event_id: str) -> bytes | None:
    """Download the latest snapshot for a Frigate event."""
    url = f"{FRIGATE_URL}/api/events/{event_id}/snapshot.jpg?bbox=1&quality=85"
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        return r.content
    except Exception as exc:
        log.warning("Snapshot fetch failed (%s): %s", event_id, exc)
        return None

def on_message(client, userdata, msg) -> None:
    try:
        data = json.loads(msg.payload)
    except json.JSONDecodeError:
        return

    # Frigate publishes two types: "new" (new event) and "update"
    event_type = data.get("type")
    if event_type not in ("new",):
        return

    after = data.get("after", {})
    label   = after.get("label", "")
    camera  = after.get("camera", "unknown")
    score   = after.get("score", 0.0)
    event_id = after.get("id", "")

    if label not in TRACK_OBJECTS:
        return
    if score < MIN_SCORE:
        return

    # Cooldown — avoid alert spam for the same camera
    now = time.time()
    if now - last_alert.get(camera, 0) < COOLDOWN_SEC:
        log.debug("Cooldown active for %s, skipping.", camera)
        return
    last_alert[camera] = now

    score_pct = round(score * 100)
    text = (
        f"🚨 <b>Frigate Alert</b>\n"
        f"📷 Camera: <code>{camera}</code>\n"
        f"🏷️ Object: <b>{label}</b> ({score_pct}% confidence)\n"
        f"🕐 {time.strftime('%Y-%m-%d %H:%M:%S')}"
    )
    log.info("Alert: %s on %s (%.0f%%)", label, camera, score * 100)

    photo = fetch_snapshot(event_id) if event_id else None
    send_telegram(text, photo)

def on_connect(client, userdata, flags, rc, props=None) -> None:
    if rc == 0:
        log.info("Connected to MQTT broker %s:%d", MQTT_HOST, MQTT_PORT)
        client.subscribe("frigate/events", qos=1)
        log.info("Subscribed to frigate/events")
    else:
        log.error("MQTT connect failed, rc=%d", rc)

def main() -> None:
    log.info("Starting Frigate Notify Service")
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.on_connect = on_connect
    client.on_message = on_message

    while True:
        try:
            client.connect(MQTT_HOST, MQTT_PORT, keepalive=60)
            client.loop_forever()
        except Exception as exc:
            log.error("Connection error: %s — retrying in 10s", exc)
            time.sleep(10)

if __name__ == "__main__":
    main()
