FROM alpine:3.19

ARG GOBUSTER_VERSION=3.8.2
ENV GOBUSTER_VERSION=${GOBUSTER_VERSION}

WORKDIR /app

# Install runtime deps and download Gobuster release
RUN apk add --no-cache ca-certificates wget tar \
    && wget -q "https://github.com/OJ/gobuster/releases/download/v${GOBUSTER_VERSION}/gobuster_Linux_x86_64.tar.gz" -O /tmp/gobuster.tar.gz \
    && tar -xzf /tmp/gobuster.tar.gz -C /tmp \
    && mv /tmp/gobuster /app/gobuster \
    && chmod +x /app/gobuster \
    && rm -rf /tmp/gobuster /tmp/gobuster.tar.gz

# Prepare directories and user
RUN adduser -D scanner \
    && mkdir -p /wordlists /output \
    && chown -R scanner:scanner /app /wordlists /output

USER scanner

CMD ["/app/gobuster"]


