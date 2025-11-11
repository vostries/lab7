FROM jenkins/jenkins:lts

USER root

RUN apt-get update && \
    apt-get install -y \
    python3 \
    chromium \
    chromium-driver \
    wget \
    curl \
    git \
    unzip \
    qemu-system-arm && \
    ln -sf /usr/bin/chromium /usr/bin/google-chrome && \
    apt-get clean

USER jenkins