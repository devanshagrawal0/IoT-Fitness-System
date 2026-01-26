#!/usr/bin/env bash
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SERVICE_SRC="$REPO_DIR/service/smartgym.service"
SERVICE_DST="/etc/systemd/system/smartgym.service"

echo "Copying service file to $SERVICE_DST"
sudo cp "$SERVICE_SRC" "$SERVICE_DST"

echo "Reloading systemd and enabling service"
sudo systemctl daemon-reload
sudo systemctl enable smartgym.service
sudo systemctl restart smartgym.service

echo "Done. Check status:"
echo "  sudo systemctl status smartgym.service --no-pager"
