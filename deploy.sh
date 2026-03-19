#!/usr/bin/env bash
# Deploy Sentinel to the robot — push to origin then pull on the Pi.
# Usage: bash deploy.sh
#
# Overrides (env vars):
#   SENTINEL_HOST  — robot IP or hostname  (default: 192.168.1.138)
#   SENTINEL_USER  — SSH user              (default: sentinel)

set -euo pipefail

ROBOT_HOST="${SENTINEL_HOST:-192.168.1.138}"
ROBOT_USER="${SENTINEL_USER:-sentinel}"
REMOTE="${ROBOT_USER}@${ROBOT_HOST}"

echo "=== Sentinel Deploy ==="
echo "Target: ${REMOTE}"
echo ""

# ── 1. Push local commits to origin ──────────────────────────────────────────

echo "[1/3] Pushing to origin..."
git push
echo ""

# ── 2. Pull on robot and restart service ─────────────────────────────────────

echo "[2/3] Pulling on robot and restarting service..."
ssh "${REMOTE}" "cd ~/sentinel && git fetch origin && git checkout -B main origin/main && sudo systemctl restart sentinel"
echo ""

# ── 3. Verify service is running ─────────────────────────────────────────────

echo "[3/3] Service status:"
ssh "${REMOTE}" "sudo systemctl status sentinel --no-pager -l"
echo ""
echo "Done. Follow logs with:"
echo "  ssh ${REMOTE} 'sudo journalctl -u sentinel -f'"
