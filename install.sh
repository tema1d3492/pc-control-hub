#!/bin/bash
sudo apt update && sudo apt install python3-flask python3-psutil wakeonlan -y
DIR=$(pwd)
sudo tee /etc/systemd/system/pc-hub.service > /dev/null << SERVICE
[Unit]
Description=PC Control Hub Web Service
After=network.target

[Service]
User=root
WorkingDirectory=$DIR
ExecStart=/usr/bin/python3 $DIR/app.py
Restart=always

[Install]
WantedBy=multi-user.target
SERVICE
sudo systemctl daemon-reload && sudo systemctl enable --now pc-hub.service
echo "Installed on port 80. Edit $DIR/config.json to configure devices."
