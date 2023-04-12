#!/bin/bash

apt install -y python3-pip python3-venv python3-pyaudio \
                git wget libatlas-base-dev libglib2.0-dev \
                libgirepository1.0-dev libcairo2-dev \
                gfortran gcc libopenblas-dev libopenblas-base \
                libblas-dev llvm python3-scipy build-essential \
                portaudio19-dev sox

CWD=$(pwd)

export PA_ALSA_PLUGHW=1

python3 -m venv $CWD/env/node

source $CWD/env/node/bin/activate
 
pip3 install -r requirements.txt
