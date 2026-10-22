#!/usr/bin/env bash
# setup.sh — One-shot installation & systemd service setup
# Issue #64 · sreconics/sreconics · Board: Raspberry Pi 3
#
# Usage:
#   chmod +x setup.sh
#   sudo ./setup.sh
#
# What it does:
#   1. Updates the system and installs system deps
#   2. Installs Python packages (in a venv at /opt/pi3cam)
#   3. Downloads the TFLite MobileNetSSD model and COCO labels
#   4. Mounts USB drive to /media/usb
#   5. Creates two systemd services: pi3cam-detect + pi3cam-server
#   6. Optionally sets up a WiFi access point with hostapd/dnsmasq

set -euo pipefail

INSTALL_DIR="/opt/pi3cam"
SERVICE_DIR="/etc/systemd/system"
USB_DEVICE="/dev/sda1"
USB_MOUNT="/media/usb"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MODEL_URL="https://storage.googleapis.com/download.tensorflow.org/models/tflite/coco_ssd_mobilenet_v1_1.0_quant_2018_06_29.zip"
LABELS_URL="https://raw.githubusercontent.com/tensorflow/models/master/research/object_detection/data/mscoco_label_map.pbtxt"

# ── Colours ──────────────────────────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'
info()  { echo -e "${GREEN}[INFO]${NC}  $*"; }
warn()  { echo -e "${YELLOW}[WARN]${NC}  $*"; }
error() { echo -e "${RED}[ERROR]${NC} $*"; exit 1; }

[[ $EUID -ne 0 ]] && error "Run as root: sudo ./setup.sh"

# ── 1. System packages ────────────────────────────────────────────────────────
info "Updating package lists …"
apt-get update -qq

info "Installing system dependencies …"
apt-get install -y -qq \
    python3-venv python3-pip \
    libatlas-base-dev libopenblas-dev \
    libhdf5-dev libhdf5-serial-dev \
    libcamera-dev libcap-dev \
    libjpeg-dev zlib1g-dev libpng-dev \
    git curl wget unzip \
    hostapd dnsmasq \
    v4l-utils

# ── 2. Python venv ────────────────────────────────────────────────────────────
info "Creating Python venv at $INSTALL_DIR …"
mkdir -p "$INSTALL_DIR"
python3 -m venv "$INSTALL_DIR/venv"

info "Installing Python packages …"
"$INSTALL_DIR/venv/bin/pip" install --quiet --upgrade pip
"$INSTALL_DIR/venv/bin/pip" install --quiet \
    picamera2 \
    tflite-runtime \
    opencv-python-headless \
    flask \
    requests \
    python-dotenv \
    Pillow

# ── 3. Copy project files ─────────────────────────────────────────────────────
info "Copying project files …"
cp "$SCRIPT_DIR"/*.py "$INSTALL_DIR/"

# ── 4. Download model + labels ────────────────────────────────────────────────
if [[ ! -f "$INSTALL_DIR/MobileNetSSD_quant.tflite" ]]; then
    info "Downloading TFLite model …"
    cd /tmp
    wget -q "$MODEL_URL" -O model.zip
    unzip -q model.zip
    mv detect.tflite "$INSTALL_DIR/MobileNetSSD_quant.tflite" 2>/dev/null || \
    mv coco_ssd_mobilenet_v1_1.0_quant_2018_06_29/detect.tflite "$INSTALL_DIR/MobileNetSSD_quant.tflite"
    cd "$SCRIPT_DIR"
fi

if [[ ! -f "$INSTALL_DIR/coco_labels.txt" ]]; then
    info "Downloading COCO labels …"
    wget -q "https://raw.githubusercontent.com/tensorflow/examples/master/lite/examples/object_detection/android/app/src/main/assets/labelmap.txt" \
         -O "$INSTALL_DIR/coco_labels.txt" || \
    python3 -c "
labels = ['???','person','bicycle','car','motorcycle','airplane','bus','train',
          'truck','boat','traffic light','fire hydrant','???','stop sign',
          'parking meter','bench','bird','cat','dog','horse','sheep','cow',
          'elephant','bear','zebra','giraffe','???','backpack','umbrella']
with open('$INSTALL_DIR/coco_labels.txt','w') as f: f.write('\n'.join(labels))
"
fi

# ── 5. USB mount ──────────────────────────────────────────────────────────────
info "Setting up USB event storage mount …"
mkdir -p "$USB_MOUNT"
if blkid "$USB_DEVICE" &>/dev/null; then
    grep -q "$USB_MOUNT" /etc/fstab || \
        echo "$USB_DEVICE  $USB_MOUNT  auto  defaults,nofail  0 2" >> /etc/fstab
    mount -a || warn "USB drive not present — will mount on reboot."
else
    warn "USB device $USB_DEVICE not found. Storing events in $USB_MOUNT (on SD card)."
    mkdir -p "$USB_MOUNT/events"
fi

# ── 6. Create .env file ───────────────────────────────────────────────────────
if [[ ! -f "$INSTALL_DIR/.env" ]]; then
    info "Creating .env template …"
    cat > "$INSTALL_DIR/.env" <<EOF
# Telegram Bot credentials (optional — alerts disabled if blank)
TELEGRAM_TOKEN=
TELEGRAM_CHAT_ID=
EOF
    warn "Edit $INSTALL_DIR/.env to enable Telegram alerts."
fi

# ── 7. systemd services ───────────────────────────────────────────────────────
info "Creating systemd service: pi3cam-detect …"
cat > "$SERVICE_DIR/pi3cam-detect.service" <<EOF
[Unit]
Description=Pi 3 AI Object Detection (TFLite)
After=network.target

[Service]
User=pi
WorkingDirectory=$INSTALL_DIR
ExecStart=$INSTALL_DIR/venv/bin/python detect.py \
    --model $INSTALL_DIR/MobileNetSSD_quant.tflite \
    --labels $INSTALL_DIR/coco_labels.txt \
    --threshold 0.50 \
    --save-dir $USB_MOUNT/events \
    --no-preview
Restart=always
RestartSec=5
EnvironmentFile=-$INSTALL_DIR/.env

[Install]
WantedBy=multi-user.target
EOF

info "Creating systemd service: pi3cam-server …"
cat > "$SERVICE_DIR/pi3cam-server.service" <<EOF
[Unit]
Description=Pi 3 AI Camera Flask Server
After=network.target pi3cam-detect.service

[Service]
User=pi
WorkingDirectory=$INSTALL_DIR
ExecStart=$INSTALL_DIR/venv/bin/python server.py \
    --host 0.0.0.0 \
    --port 5000 \
    --event-dir $USB_MOUNT/events
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable pi3cam-detect pi3cam-server
systemctl start  pi3cam-detect pi3cam-server

info "Services started. Check status with:"
echo "  sudo systemctl status pi3cam-detect"
echo "  sudo systemctl status pi3cam-server"

# ── 8. WiFi Access Point (optional) ──────────────────────────────────────────
read -rp "Set up WiFi access point? (y/N): " SETUP_AP
if [[ "$SETUP_AP" =~ ^[Yy]$ ]]; then
    AP_SSID="Pi3Cam-AP"
    AP_PASS="pi3camera"

    cat > /etc/hostapd/hostapd.conf <<EOF
interface=wlan0
ssid=$AP_SSID
wpa_passphrase=$AP_PASS
hw_mode=g
channel=7
wmm_enabled=0
macaddr_acl=0
auth_algs=1
ignore_broadcast_ssid=0
wpa=2
wpa_key_mgmt=WPA-PSK
rsn_pairwise=CCMP
EOF

    cat > /etc/dnsmasq.conf <<EOF
interface=wlan0
dhcp-range=192.168.50.10,192.168.50.50,255.255.255.0,24h
EOF

    ip addr add 192.168.50.1/24 dev wlan0 || true
    systemctl unmask hostapd
    systemctl enable hostapd dnsmasq
    systemctl restart hostapd dnsmasq

    info "WiFi AP '$AP_SSID' (pass: $AP_PASS) active on 192.168.50.1"
    info "Open http://192.168.50.1:5000 on your phone."
fi

PI_IP=$(hostname -I | awk '{print $1}')
info "Setup complete!"
echo -e "${GREEN}  Dashboard: http://$PI_IP:5000${NC}"
echo -e "${GREEN}  Gallery:   http://$PI_IP:5000/events${NC}"
