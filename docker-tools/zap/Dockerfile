# Use Ubuntu base image with Java
FROM ubuntu:22.04

WORKDIR /app

# Avoid interactive prompts during apt-get install
ENV DEBIAN_FRONTEND=noninteractive

# Install Java 17 and dependencies
RUN apt-get update && apt-get install -y \
    openjdk-17-jdk \
    wget \
    curl \
    python3 \
    python3-pip \
    unzip \
    xvfb \
    x11-apps \
    libxi6 \
    libxtst6 \
    libxrender1 \
    libxrandr2 \
    libnss3 \
    libatk1.0-0 \
    libgtk-3-0 \
    libdbus-glib-1-2 \
    && rm -rf /var/lib/apt/lists/*

# Set JAVA_HOME
ENV JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
ENV PATH="${JAVA_HOME}/bin:${PATH}"

# Download and install OWASP ZAP to /zap (expected by zap-baseline.py)
RUN ZAP_VERSION="2.16.1" && \
    wget -q "https://github.com/zaproxy/zaproxy/releases/download/v${ZAP_VERSION}/ZAP_${ZAP_VERSION}_Linux.tar.gz" -O zap.tar.gz && \
    tar -xzf zap.tar.gz && \
    rm zap.tar.gz && \
    mkdir -p /zap && \
    mv ZAP_*/* /zap/ && \
    chmod +x /zap/*.sh && \
    ln -s /zap/zap.sh /zap/zap-x.sh

# Install ZAP Python API and dependencies
RUN pip3 install --no-cache-dir python-owasp-zap-v2.4 requests pyyaml

# Download ZAP baseline script and zap_common module
RUN wget -q https://raw.githubusercontent.com/zaproxy/zaproxy/main/docker/zap-baseline.py -O /app/zap-baseline.py && \
    wget -q https://raw.githubusercontent.com/zaproxy/zaproxy/main/docker/zap_common.py -O /app/zap_common.py && \
    chmod +x /app/zap-baseline.py && \
    sed -i '1s|.*|#!/usr/bin/env python3|' /app/zap-baseline.py && \
    sed -i 's|from zap_common import|import sys; sys.path.insert(0, "/app"); from zap_common import|' /app/zap-baseline.py || true

# Create output directory
RUN mkdir -p /output

# Set PATH to include ZAP
ENV PATH="/zap:${PATH}"
ENV DISPLAY=:0
ENV ZAP_PATH=/zap

# Create ZAP work directory
RUN mkdir -p /zap/wrk && chmod 777 /zap/wrk

# Default command
CMD ["/app/zap-baseline.py"]
