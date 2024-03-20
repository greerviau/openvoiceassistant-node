#!/bin/bash

source ./env/bin/activate

export PA_ALSA_PLUGHW=1

python -m node $1 $2 $3