#!/usr/bin/env bash
# setup.sh — Pi 5 Surveillance DVR automated setup
# Run as: bash setup.sh
# Tested on: Raspberry Pi OS Bookworm (64-bit) on Pi 5

set -euo pipefail
CYAN='\033[0;36m'; GREEN='\033[0;32m'; RED='\033[0;31m'; NC='\033[0m'
info()  { echo -e "${CYAN}[INFO]${NC}  $*"; }
ok()    { echo -e "${GREEN}[OK]${NC}    $*"; }
err()   { echo -e "${RED}[ERR]${NC}   $*"; exit 1; }

# ── 1. Detect Pi 5 ──────────────────────────────────────────────────────────
info "Checking hardware..."
MODEL=$(cat /proc/device-tree/model 2>/dev/null || echo "unknown")
echo "  Board: $MODEL"
[[ "$MODEL" == *"Pi 5"* ]] || echo "  Warning: not a Pi 5 — proceeding anyway"

# ── 2. Update system ─────────────────────────────────────────────────────────
info "Updating package lists..."
sudo apt-get update -qq

# ── 3. Install Docker ────────────────────────────────────────────────────────
if ! command -v docker &>/dev/null; then
    info "Installing Docker..."
    curl -fsSL https://get.docker.com | sudo sh
    sudo usermod -aG docker "$USER"
    ok "Docker installed"
else
    ok "Docker already installed: $(docker --version)"
fi

# ── 4. Install docker-compose plugin ────────────────────────────────────────
if ! docker compose version &>/dev/null; then
    info "Installing docker-compose plugin..."
    sudo apt-get install -y docker-compose-plugin
    ok "docker-compose plugin installed"
else
    ok "docker-compose: $(docker compose version)"
fi

# ── 5. Prepare NVMe mount ────────────────────────────────────────────────────
info "Configuring NVMe storage mount..."
NVME_DEV=$(lsblk -dno NAME,TRAN 2>/dev/null | awk '$2=="nvme"{print "/dev/"$1}' | head -1)
if [ -z "$NVME_DEV" ]; then
    echo "  No NVMe device detected — skipping auto-mount"
    echo "  Manually mount your NVMe SSD at /mnt/nvme before starting"
else
    echo "  Detected: $NVME_DEV"
    sudo mkdir -p /mnt/nvme
    if ! grep -q "/mnt/nvme" /etc/fstab; then
        UUID=$(sudo blkid -s UUID -o value "$NVME_DEV")
        echo "UUID=$UUID  /mnt/nvme  ext4  defaults,noatime  0  2" | sudo tee -a /etc/fstab
        sudo mount /mnt/nvme
        ok "NVMe mounted at /mnt/nvme"
    else
        ok "/mnt/nvme already in fstab"
    fi
fi
sudo mkdir -p /mnt/nvme/frigate

# ── 6. Enable Pi Camera (libcamera / v4l2) ──────────────────────────────────
info "Enabling camera..."
if ! grep -q "^camera_auto_detect=1" /boot/firmware/config.txt 2>/dev/null; then
    echo "camera_auto_detect=1" | sudo tee -a /boot/firmware/config.txt
    ok "Camera auto-detect enabled (reboot required)"
else
    ok "Camera already enabled"
fi
sudo apt-get install -y libcamera-tools v4l-utils -qq

# ── 7. Create .env template ──────────────────────────────────────────────────
if [ ! -f .env ]; then
    info "Creating .env template..."
    cat > .env <<'ENV'
# Frigate NVR settings
FRIGATE_RTSP_PASSWORD=changeme

# Telegram bot (get from @BotFather)
TELEGRAM_TOKEN=your_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id_here
ENV
    ok ".env template created — fill in TELEGRAM_TOKEN and TELEGRAM_CHAT_ID"
else
    ok ".env already exists"
fi

# ── 8. Create Mosquitto config ───────────────────────────────────────────────
mkdir -p mosquitto/config mosquitto/data mosquitto/log
if [ ! -f mosquitto/config/mosquitto.conf ]; then
    cat > mosquitto/config/mosquitto.conf <<'MQTTCONF'
listener 1883
listener 9001
protocol websockets
allow_anonymous true
persistence true
persistence_location /mosquitto/data/
log_dest file /mosquitto/log/mosquitto.log
MQTTCONF
    ok "Mosquitto config created"
fi

# ── 9. Done ──────────────────────────────────────────────────────────────────
echo ""
ok "Setup complete!"
echo ""
echo "  Next steps:"
echo "  1. Edit .env — set TELEGRAM_TOKEN and TELEGRAM_CHAT_ID"
echo "  2. Adjust frigate_config.yml camera paths if needed"
echo "  3. Reboot if camera was just enabled:"
echo "       sudo reboot"
echo "  4. Start the stack:"
echo "       docker compose up -d"
echo "  5. Open Frigate UI: http://$(hostname -I | awk '{print $1}'):5000"
echo ""
