#!/usr/bin/env bash
# setup.sh — One-shot installer for the Pi 4 NIDS station
# Installs: Docker, Suricata 7, Zeek 6, Python deps,
#           Grafana+Loki (Docker Compose), systemd services.
# Tested: Raspberry Pi 4, Raspberry Pi OS 64-bit Bookworm
#
# Usage:
#   chmod +x setup.sh && sudo ./setup.sh
#
# After install:
#   • Edit MIRROR_IFACE in /etc/nids/nids.conf
#   • systemctl start nids-capture nids-classifier nids-threatmap
#   • Browse http://<pi-ip>:3000  (Grafana)
#   • Browse http://<pi-ip>:5000  (Live Threat Map)

set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
NIDS_HOME="/opt/nids"
CONF_DIR="/etc/nids"
LOG_DIR="/var/log/nids"

echo "══════════════════════════════════════════════"
echo "  Pi 4 NIDS Station — Setup Script"
echo "  $(date)"
echo "══════════════════════════════════════════════"

# ── 0. Prerequisites ───────────────────────────────────────────
apt-get update -qq
apt-get install -y --no-install-recommends \
    curl git python3 python3-pip python3-venv \
    libpcap-dev net-tools ca-certificates gnupg lsb-release

# ── 1. Docker (if not present) ─────────────────────────────────
if ! command -v docker &>/dev/null; then
    echo "[1/6] Installing Docker …"
    curl -fsSL https://get.docker.com | sh
    usermod -aG docker pi 2>/dev/null || true
else
    echo "[1/6] Docker already installed: $(docker --version)"
fi

# ── 2. Suricata 7 ──────────────────────────────────────────────
if ! command -v suricata &>/dev/null; then
    echo "[2/6] Installing Suricata 7 …"
    add-apt-repository -y ppa:oisf/suricata-stable 2>/dev/null || \
        echo "deb https://ppa.launchpadcontent.net/oisf/suricata-stable/ubuntu jammy main" \
        > /etc/apt/sources.list.d/suricata.list
    apt-get update -qq
    apt-get install -y suricata
    suricata-update
else
    echo "[2/6] Suricata already installed: $(suricata --version 2>&1 | head -1)"
fi

# ── 3. Zeek 6 ──────────────────────────────────────────────────
if ! command -v zeek &>/dev/null; then
    echo "[3/6] Installing Zeek 6 …"
    echo "deb https://download.opensuse.org/repositories/security:/zeek/Debian_12/ /" \
        > /etc/apt/sources.list.d/zeek.list
    curl -fsSL "https://download.opensuse.org/repositories/security:/zeek/Debian_12/Release.key" \
        | gpg --dearmor -o /etc/apt/trusted.gpg.d/zeek.gpg
    apt-get update -qq
    apt-get install -y zeek
else
    echo "[3/6] Zeek already installed: $(zeek --version 2>&1 | head -1)"
fi

# ── 4. Python virtualenv + deps ────────────────────────────────
echo "[4/6] Setting up Python environment …"
mkdir -p "$NIDS_HOME"
python3 -m venv "$NIDS_HOME/venv"
"$NIDS_HOME/venv/bin/pip" install -q --upgrade pip
"$NIDS_HOME/venv/bin/pip" install -q \
    scapy flask flask-socketio requests numpy \
    scikit-learn joblib imbalanced-learn pandas \
    geoip2 jinja2

# ── 5. Copy project files ──────────────────────────────────────
echo "[5/6] Installing NIDS files to $NIDS_HOME …"
mkdir -p "$CONF_DIR" "$LOG_DIR"
cp "$SCRIPT_DIR"/*.py     "$NIDS_HOME/"
cp "$SCRIPT_DIR/docker-compose.yml" "$NIDS_HOME/"
chown -R pi:pi "$NIDS_HOME" "$LOG_DIR" 2>/dev/null || true

cat > "$CONF_DIR/nids.conf" <<'EOF'
# NIDS Station configuration
MIRROR_IFACE=eth1
LOKI_URL=http://localhost:3100
CLASSIFIER_PORT=8765
THREATMAP_PORT=5000
EOF

# ── 6. Systemd services ────────────────────────────────────────
echo "[6/6] Installing systemd services …"

cat > /etc/systemd/system/nids-loki-grafana.service <<'EOF'
[Unit]
Description=NIDS Loki + Grafana Stack
Requires=docker.service
After=docker.service network-online.target

[Service]
WorkingDirectory=/opt/nids
ExecStart=/usr/bin/docker compose up
ExecStop=/usr/bin/docker compose down
Restart=on-failure
User=pi

[Install]
WantedBy=multi-user.target
EOF

cat > /etc/systemd/system/nids-capture.service <<'EOF'
[Unit]
Description=NIDS Capture Daemon (Suricata-parallel Scapy sniff)
After=network-online.target nids-loki-grafana.service

[Service]
EnvironmentFile=/etc/nids/nids.conf
ExecStart=/opt/nids/venv/bin/python3 /opt/nids/nids_capture.py \
    --iface ${MIRROR_IFACE} --loki ${LOKI_URL}
Restart=always
RestartSec=5
User=root

[Install]
WantedBy=multi-user.target
EOF

cat > /etc/systemd/system/nids-classifier.service <<'EOF'
[Unit]
Description=NIDS ML Flow Classifier Microservice
After=network-online.target

[Service]
EnvironmentFile=/etc/nids/nids.conf
ExecStart=/opt/nids/venv/bin/python3 /opt/nids/flow_classifier.py \
    --model /opt/nids/model.pkl --port ${CLASSIFIER_PORT}
Restart=always
RestartSec=5
User=pi

[Install]
WantedBy=multi-user.target
EOF

cat > /etc/systemd/system/nids-threatmap.service <<'EOF'
[Unit]
Description=NIDS Live Threat Map (Flask/SocketIO)
After=nids-loki-grafana.service

[Service]
EnvironmentFile=/etc/nids/nids.conf
ExecStart=/opt/nids/venv/bin/python3 /opt/nids/threat_map.py \
    --loki ${LOKI_URL} --port ${THREATMAP_PORT}
Restart=always
RestartSec=5
User=pi

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable nids-loki-grafana nids-capture nids-classifier nids-threatmap

# Daily report cron
echo "59 23 * * *  pi  /opt/nids/venv/bin/python3 /opt/nids/daily_report.py >> /var/log/nids/cron.log 2>&1" \
    > /etc/cron.d/nids-daily-report

echo ""
echo "✅  Setup complete!"
echo ""
echo "  Next steps:"
echo "  1. Edit MIRROR_IFACE in /etc/nids/nids.conf (default: eth1)"
echo "  2. Download GeoLite2-City.mmdb → /opt/nids/GeoLite2-City.mmdb"
echo "  3. (Optional) train model: cd /opt/nids && venv/bin/python3 train_classifier.py"
echo "  4. systemctl start nids-loki-grafana && systemctl start nids-capture"
echo ""
echo "  Dashboards:"
echo "    Grafana:    http://$(hostname -I | awk '{print $1}'):3000  (admin / nids_admin)"
echo "    Threat Map: http://$(hostname -I | awk '{print $1}'):5000"
