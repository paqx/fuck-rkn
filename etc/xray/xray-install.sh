#!/bin/bash

set -e

if [[ $EUID -ne 0 ]]; then
  echo "This script must be run as root"
  exit 1
fi

command -v unzip >/dev/null 2>&1 || apt-get update && apt-get install -y unzip


groupadd xray
useradd -r -g xray -s /usr/sbin/nologin xray


cd /usr/local/bin/
wget https://github.com/XTLS/Xray-core/releases/download/v25.10.15/Xray-linux-64.zip
unzip Xray-linux-64.zip
rm Xray-linux-64.zip


cd /usr/local/etc/
mkdir -p xray
cd xray/
touch config.json


cat  << 'EOF' > /etc/systemd/system/xray.service
[Unit]
Description=Xray Service
Documentation=https://github.com/XTLS/Xray-core
After=network.target nss-lookup.target

[Service]
User=xray
Group=xray

CapabilityBoundingSet=CAP_NET_BIND_SERVICE
AmbientCapabilities=CAP_NET_BIND_SERVICE
NoNewPrivileges=true

ExecStart=/usr/local/bin/xray run -config /usr/local/etc/xray/config.json
ExecReload=/bin/kill -HUP $MAINPID

Restart=on-failure
RestartSec=10
LimitNOFILE=51200

[Install]
WantedBy=multi-user.target
EOF


systemctl daemon-reload
