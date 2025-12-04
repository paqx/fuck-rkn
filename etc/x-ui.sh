#!/bin/bash

VERSION="2.8.5"

cd /root/

wget "https://github.com/MHSanaei/3x-ui/releases/download/v${VERSION}/x-ui-linux-amd64.tar.gz"
tar zxvf x-ui-linux-amd64.tar.gz

chmod +x x-ui/x-ui x-ui/bin/xray-linux-* x-ui/x-ui.sh

cp x-ui/x-ui.sh /usr/bin/x-ui

cp -f x-ui/x-ui.service /etc/systemd/system/
mv x-ui/ /usr/local/

systemctl daemon-reload
systemctl enable x-ui
