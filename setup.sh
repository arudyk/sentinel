#!/usr/bin/env bash
# Sentinel one-shot setup script — run once on the Raspberry Pi after first boot.
# Usage: cd /home/sentinel/sentinel && bash setup.sh

set -euo pipefail

SENTINEL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SERVICE_SRC="$SENTINEL_DIR/systemd/sentinel.service"
SERVICE_DEST="/etc/systemd/system/sentinel.service"

echo "=== Sentinel Setup ==="
echo "Directory: $SENTINEL_DIR"
echo ""

# ── 1. System packages ───────────────────────────────────────────────────────

echo "[1/6] Installing system packages..."
sudo apt-get update -qq
sudo apt-get install -y \
    python3-picamera2 \
    python3-libcamera \
    libcamera-apps \
    python3-rpi.gpio \
    python3-smbus2 \
    i2c-tools \
    python3-venv \
    git

# Enable I2C if not already enabled
if ! grep -q "^dtparam=i2c_arm=on" /boot/firmware/config.txt 2>/dev/null; then
    echo "dtparam=i2c_arm=on" | sudo tee -a /boot/firmware/config.txt
    echo "  I2C enabled in config.txt (reboot required for I2C to be active)"
fi

# ── 2. PiSugar 3 power manager ───────────────────────────────────────────────

echo "[2/6] Installing PiSugar power manager..."
wget -qO /tmp/pisugar-power-manager.sh https://cdn.pisugar.com/release/pisugar-power-manager.sh
# Run non-interactively: pass model selection via stdin (3 = PiSugar 3)
echo "3" | sudo bash /tmp/pisugar-power-manager.sh -c release
sudo systemctl enable pisugar-server
sudo systemctl start pisugar-server

# ── 3. Python virtual environment ────────────────────────────────────────────

echo "[3/6] Creating virtual environment..."
# --system-site-packages is critical: lets venv see apt-installed picamera2 / RPi.GPIO
python3 -m venv --system-site-packages "$SENTINEL_DIR/venv"

# ── 4. Python dependencies ───────────────────────────────────────────────────

echo "[4/6] Installing Python dependencies..."
"$SENTINEL_DIR/venv/bin/pip" install --quiet --upgrade pip
"$SENTINEL_DIR/venv/bin/pip" install --quiet -r "$SENTINEL_DIR/requirements.txt"

# ── 5. Systemd service ───────────────────────────────────────────────────────

echo "[5/6] Installing systemd service..."
sudo cp "$SERVICE_SRC" "$SERVICE_DEST"
sudo systemctl daemon-reload
sudo systemctl enable sentinel.service
sudo systemctl restart sentinel.service

# ── 6. Done ──────────────────────────────────────────────────────────────────

echo "[6/6] Setup complete."
echo ""

PI_IP=$(hostname -I | awk '{print $1}')
echo "  Local URL:     http://${PI_IP}:8080"
echo "  Hostname URL:  http://sentinel.local:8080"
echo ""
echo "  Service status:  sudo systemctl status sentinel"
echo "  Logs:            sudo journalctl -u sentinel -f"
echo ""
