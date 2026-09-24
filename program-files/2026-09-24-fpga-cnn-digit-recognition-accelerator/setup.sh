#!/usr/bin/env bash
# setup.sh — One-shot bootstrap for PYNQ-Z2 CNN Digit Recognition
# Board  : PYNQ-Z2 (Zynq-7020 SoC)
# Project: FPGA CNN Inference Accelerator for Digit Recognition
# DevNode Technologies — 2026-09-24
#
# Run once as root (or with sudo) directly on the PYNQ-Z2:
#   chmod +x setup.sh && sudo ./setup.sh
#
# What it does
# ─────────────
#   1. Update package lists (no dist-upgrade to preserve PYNQ kernel)
#   2. Install system packages: python3-pip, v4l-utils, libjpeg-dev
#   3. Install Python dependencies into the PYNQ venv
#   4. Download demo MNIST sample images for offline testing
#   5. Create a systemd service so main.py starts on every boot

set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "======================================================"
echo "  PYNQ-Z2 Setup — FPGA CNN Digit Recognition"
echo "  DevNode Technologies"
echo "======================================================"

# ── 1. System packages ────────────────────────────────────────────────────────
echo "[1/5] Updating package lists..."
apt-get update -qq

echo "      Installing system deps..."
apt-get install -y --no-install-recommends \
    python3-pip \
    v4l-utils \
    libjpeg-dev \
    libopenblas-dev \
    2>&1 | grep -v "^Get:\|^Unpacking\|^Preparing\|^Selecting"

# ── 2. Python packages into PYNQ venv ─────────────────────────────────────────
echo "[2/5] Installing Python packages..."
PYNQ_PIP=/home/xilinx/.pynq_venv/bin/pip3
if [ ! -f "$PYNQ_PIP" ]; then
    PYNQ_PIP=$(which pip3)
fi

$PYNQ_PIP install --quiet --no-cache-dir \
    flask \
    opencv-python-headless \
    numpy \
    pillow

echo "      Python packages installed."

# ── 3. Verify PYNQ library ───────────────────────────────────────────────────
echo "[3/5] Checking PYNQ library..."
PYNQ_PYTHON=/home/xilinx/.pynq_venv/bin/python3
if [ ! -f "$PYNQ_PYTHON" ]; then
    PYNQ_PYTHON=$(which python3)
fi

if $PYNQ_PYTHON -c "import pynq; print('  pynq', pynq.__version__)" 2>/dev/null; then
    echo "      PYNQ OK"
else
    echo "      [WARN] PYNQ library not found — SW fallback will be used"
fi

# ── 4. Download demo test images (MNIST samples) ──────────────────────────────
echo "[4/5] Downloading MNIST demo images..."
DEMO_DIR="$SCRIPT_DIR/demo_images"
mkdir -p "$DEMO_DIR"

# Fetch a few sample PNG images from the MNIST dataset via EMNIST mirror
BASE_URL="https://raw.githubusercontent.com/myleott/mnist_png/master/data/testing"
for digit in 0 1 2 3 4 5 6 7 8 9; do
    # Download the first sample for each class
    IMG_URL="$BASE_URL/$digit/1.png"
    OUT_FILE="$DEMO_DIR/digit_${digit}.png"
    if curl -sSf "$IMG_URL" -o "$OUT_FILE" 2>/dev/null; then
        echo "      Downloaded digit_${digit}.png"
    else
        echo "      [WARN] Could not download digit ${digit} — skipping (offline OK)"
    fi
done

# ── 5. Systemd service ────────────────────────────────────────────────────────
echo "[5/5] Installing systemd service..."
SERVICE_FILE="/etc/systemd/system/cnn-digit-recognizer.service"

cat > "$SERVICE_FILE" << EOF
[Unit]
Description=FPGA CNN Digit Recognition — PYNQ-Z2
After=network.target

[Service]
Type=simple
User=xilinx
WorkingDirectory=${SCRIPT_DIR}
ExecStart=${PYNQ_PYTHON} ${SCRIPT_DIR}/main.py
Restart=on-failure
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable cnn-digit-recognizer.service
systemctl restart cnn-digit-recognizer.service

echo ""
echo "======================================================"
echo "  Setup complete!"
echo ""
echo "  Service status:"
systemctl is-active cnn-digit-recognizer.service || true
echo ""
echo "  REST API available at:"
echo "    http://$(hostname -I | awk '{print $1}' || echo 'PYNQ_IP'):5000/"
echo ""
echo "  Test inference:"
echo "    curl -X POST http://localhost:5000/predict \\"
echo "         -F image=@demo_images/digit_3.png"
echo ""
echo "  View logs:"
echo "    journalctl -u cnn-digit-recognizer -f"
echo ""
echo "  Next: place cnn_mnist.bit in this directory to enable HW inference"
echo "======================================================"
