#!/bin/bash
apt-get update && apt-get install -y python3-pip python3-venv git wget \
                libatlas-base-dev libglib2.0-dev \
                libgirepository1.0-dev libcairo2-dev libspeexdsp-dev\
                gfortran gcc libopenblas-dev portaudio19-dev \
                libblas-dev llvm python3-scipy build-essential sox sed

CWD=$(pwd)

python3 -m venv $CWD/env

source $CWD/env/bin/activate
 
python -m pip install -r requirements_rpi.txt

cp $CWD/scripts/ova_node.service.sample /etc/systemd/system/ova_node.service
sed -i -e "s|OVAPATH|$CWD|g" /etc/systemd/system/ova_node.service
sed -i -e "s|USER|${USER}|g" /etc/systemd/system/ova_node.service

systemctl start ova_node.service
systemctl enable ova_node.service
