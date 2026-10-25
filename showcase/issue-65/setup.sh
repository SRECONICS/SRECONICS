#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# setup.sh — Smart Home Energy Monitor Stack (Pi 4 Edition)
# Installs: Mosquitto MQTT, InfluxDB 2.x, Grafana, Node-RED
# Run as: chmod +x setup.sh && sudo ./setup.sh
# ─────────────────────────────────────────────────────────────────────────────
set -euo pipefail

INFLUX_USER="sreconics"
INFLUX_PASS="changeme_secure"   # ← change before running
INFLUX_ORG="sreconics"
INFLUX_BUCKET="energy"
GRAFANA_PORT=3000
NODERED_PORT=1880

echo "==> Updating package lists..."
apt-get update -qq

# ── 1. Mosquitto MQTT broker ─────────────────────────────────────────────────
echo "==> Installing Mosquitto..."
apt-get install -y mosquitto mosquitto-clients
cat > /etc/mosquitto/conf.d/local.conf <<'EOF'
listener 1883 0.0.0.0
allow_anonymous true
EOF
systemctl enable --now mosquitto
echo "    Mosquitto OK — port 1883"

# ── 2. InfluxDB 2.x ──────────────────────────────────────────────────────────
echo "==> Installing InfluxDB 2.x..."
curl -fsSL https://repos.influxdata.com/influxdata-archive_compat.key | \
  gpg --dearmor -o /etc/apt/trusted.gpg.d/influxdata-archive_compat.gpg
echo "deb [signed-by=/etc/apt/trusted.gpg.d/influxdata-archive_compat.gpg] \
  https://repos.influxdata.com/debian stable main" \
  > /etc/apt/sources.list.d/influxdata.list
apt-get update -qq
apt-get install -y influxdb2 influxdb2-cli
systemctl enable --now influxd
sleep 3   # let the daemon start

influx setup \
  --username "$INFLUX_USER" \
  --password "$INFLUX_PASS" \
  --org     "$INFLUX_ORG" \
  --bucket  "$INFLUX_BUCKET" \
  --retention 0 \
  --force   2>/dev/null || echo "    InfluxDB already initialised"

INFLUX_TOKEN=$(influx auth list --json | python3 -c \
  "import sys,json; print(json.load(sys.stdin)[0]['token'])")
echo "    InfluxDB token: $INFLUX_TOKEN"
echo "INFLUX_TOKEN=$INFLUX_TOKEN" >> /etc/environment

# ── 3. Grafana ───────────────────────────────────────────────────────────────
echo "==> Installing Grafana..."
apt-get install -y apt-transport-https software-properties-common wget
wget -q -O /etc/apt/trusted.gpg.d/grafana.gpg \
  https://apt.grafana.com/gpg.key
echo "deb [signed-by=/etc/apt/trusted.gpg.d/grafana.gpg] \
  https://apt.grafana.com stable main" \
  > /etc/apt/sources.list.d/grafana.list
apt-get update -qq
apt-get install -y grafana
sed -i "s/;http_port = 3000/http_port = $GRAFANA_PORT/" \
  /etc/grafana/grafana.ini
systemctl enable --now grafana-server
echo "    Grafana OK — http://$(hostname -I | awk '{print $1}'):$GRAFANA_PORT"

# ── 4. Node-RED ──────────────────────────────────────────────────────────────
echo "==> Installing Node-RED..."
bash <(curl -fsSL https://raw.githubusercontent.com/node-red/linux-installers/master/deb/update-nodejs-and-nodered) \
  --confirm-root --confirm-install --skip-pi --no-init
systemctl enable --now nodered
echo "    Node-RED OK — http://$(hostname -I | awk '{print $1}'):$NODERED_PORT"

# ── 5. Python deps ───────────────────────────────────────────────────────────
echo "==> Installing Python dependencies..."
pip3 install --break-system-packages \
  adafruit-circuitpython-ads1x15 \
  paho-mqtt \
  influxdb-client \
  minimalmodbus

# ── 6. Systemd service for energy_monitor.py ─────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cat > /etc/systemd/system/energy-monitor.service <<EOF
[Unit]
Description=Pi 4 Smart Home Energy Monitor
After=network.target mosquitto.service influxd.service

[Service]
ExecStart=/usr/bin/python3 $SCRIPT_DIR/energy_monitor.py
WorkingDirectory=$SCRIPT_DIR
Restart=always
RestartSec=10
Environment="INFLUX_TOKEN=$INFLUX_TOKEN"

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable --now energy-monitor
echo "    energy-monitor service enabled"

echo ""
echo "============================================================"
echo "  Setup complete!"
echo "  Grafana   → http://$(hostname -I | awk '{print $1}'):$GRAFANA_PORT  (admin/admin)"
echo "  Node-RED  → http://$(hostname -I | awk '{print $1}'):$NODERED_PORT"
echo "  InfluxDB  → http://$(hostname -I | awk '{print $1}'):8086"
echo "  MQTT      → mqtt://$(hostname -I | awk '{print $1}'):1883"
echo "============================================================"
echo "  Edit energy_monitor.py and set INFLUX_TOKEN from above."
