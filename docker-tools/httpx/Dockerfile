FROM alpine:3.19

ARG HTTPX_VERSION=1.7.2
ENV HTTPX_VERSION=${HTTPX_VERSION}

WORKDIR /app

# Install runtime deps and download official binary release
RUN apk add --no-cache ca-certificates wget unzip \
    && wget -q "https://github.com/projectdiscovery/httpx/releases/download/v${HTTPX_VERSION}/httpx_${HTTPX_VERSION}_linux_amd64.zip" -O /tmp/httpx.zip \
    && unzip /tmp/httpx.zip -d /tmp/httpx \
    && mv /tmp/httpx/httpx /app/httpx \
    && chmod +x /app/httpx \
    && rm -rf /tmp/httpx /tmp/httpx.zip

# Create unprivileged user and output directory
RUN adduser -D scanner \
    && mkdir -p /output \
    && chown -R scanner:scanner /app /output

USER scanner

CMD ["/app/httpx"]


