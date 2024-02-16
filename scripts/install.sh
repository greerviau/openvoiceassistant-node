#!/bin/bash
apt-get update && apt-get install -y python3-pip python3-venv git wget \
                libatlas-base-dev libglib2.0-dev \
                libgirepository1.0-dev libcairo2-dev libspeexdsp-dev\
                gfortran gcc libopenblas-dev portaudio19-dev \
                libblas-dev llvm python3-scipy build-essential sox

CWD=$(pwd)

python3 -m venv $CWD/env

source $CWD/env/bin/activate
 
python -m pip install --upgrade pip
python -m pip install --upgrade wheel
python -m pip install -r requirements_rpi.txt

cat <<EOF > "/etc/systemd/system/ova_hub_backend.service"
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