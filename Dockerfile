FROM ubuntu:20.04 as base
ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y \
    python3 python3-pip nginx wget pulseaudio \
    alsa-utils sox libsox-fmt-all iputils-ping \
    libportaudio2 portaudio19-dev python3-pyaudio

COPY ./requirements.txt /tmp/requirements.txt
RUN pip3 install --upgrade pip "setuptools<58.0.0"

RUN pip3 install -r tmp/requirements.txt --timeout 60

ENV PULSE_SERVER=host.docker.internal

FROM base AS development

RUN apt-get update && apt-get install -y git
#RUN useradd -ms /bin/bash user
#RUN usermod -aG sudo user

FROM base as deployment

COPY ./ /app
WORKDIR /app