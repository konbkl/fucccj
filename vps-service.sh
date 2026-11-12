#!/bin/bash
# Installs a systemd service so the bot starts on boot and restarts if it crashes.
# Usage (from the bot folder): sudo bash vps-service.sh
set -e
DIR="$(cd "$(dirname "$0")" && pwd)"
cat > /etc/systemd/system/baby-music.service <<UNIT
[Unit]
Description=Baby Music Telegram Bot
After=network-online.target
Wants=network-online.target

[Service]
WorkingDirectory=$DIR
ExecStart=/bin/bash $DIR/start
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
UNIT
systemctl daemon-reload
systemctl enable --now baby-music
echo "Done. Logs: journalctl -u baby-music -f"
