#!/bin/bash
apt-get update && apt-get install -y python3-pip python3-venv git wget \
                libatlas-base-dev libglib2.0-dev \
                libgirepository1.0-dev libcairo2-dev libspeexdsp-dev\
                gfortran gcc libopenblas-dev portaudio19-dev \
                libblas-dev build-essential

CWD=$(pwd)
echo $CWD

git config --global --add safe.directory $CWD

rm -r $CWD/env

python3 -m venv $CWD/env

source $CWD/env/bin/activate
 
python -m pip install --upgrade pip
python -m pip install --upgrade wheel
python -m pip install -r requirements_rpi.txt

rm /etc/systemd/system/ova_node.service

cat <<EOF > "/etc/systemd/system/ova_node.service"
[Unit]
Description=openvoiceassistant Node

[Service]
ExecStart=/bin/bash $CWD/scripts/start_node.sh
WorkingDirectory=$CWD
Restart=always
RestartSec=30
User=$USER

[Install]
WantedBy=multi-user.target
EOF

systemctl enable ova_node.service
systemctl restart ova_node.service