#!/bin/bash
# setup.sh — Bootstrap the Pi 3 LoRa Gateway
# Run once as pi (sudo as needed)

set -euo pipefail

echo "[1/5] Enabling SPI interface..."
sudo raspi-config nonint do_spi 0

echo "[2/5] Installing system packages..."
sudo apt update -q
sudo apt install -y python3-pip mosquitto mosquitto-clients sqlite3

echo "[3/5] Installing Python deps..."
pip3 install \
    adafruit-blinka \
    adafruit-circuitpython-rfm9x \
    paho-mqtt \
    flask

echo "[4/5] Enabling & starting Mosquitto MQTT broker..."
sudo systemctl enable mosquitto
sudo systemctl start mosquitto

echo "[5/5] Installing systemd service..."
SERVICE_FILE="/etc/systemd/system/lora-gateway.service"
sudo tee "$SERVICE_FILE" > /dev/null <<'EOF'
[Unit]
Description=LoRa Gateway Receiver + Flask Dashboard
After=network.target mosquitto.service

[Service]
ExecStart=/usr/bin/python3 /home/pi/lora_gateway/main.py
WorkingDirectory=/home/pi/lora_gateway
Restart=always
RestartSec=5
User=pi
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable lora-gateway
sudo systemctl start lora-gateway

echo ""
echo "✅  Setup complete!"
echo "   Dashboard → http://$(hostname -I | awk '{print $1}'):5000"
echo "   MQTT      → mosquitto_sub -h localhost -t 'sensors/lora/#' -v"
echo "   Logs      → journalctl -u lora-gateway -f"
