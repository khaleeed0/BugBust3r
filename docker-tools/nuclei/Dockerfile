FROM alpine:3.19

ARG NUCLEI_VERSION=3.5.1
ENV NUCLEI_VERSION=${NUCLEI_VERSION}

WORKDIR /app

# Install dependencies and download official Nuclei release
RUN apk add --no-cache ca-certificates wget unzip git \
    && wget -q "https://github.com/projectdiscovery/nuclei/releases/download/v${NUCLEI_VERSION}/nuclei_${NUCLEI_VERSION}_linux_amd64.zip" -O /tmp/nuclei.zip \
    && unzip /tmp/nuclei.zip -d /tmp/nuclei \
    && mv /tmp/nuclei/nuclei /app/nuclei \
    && chmod +x /app/nuclei \
    && rm -rf /tmp/nuclei /tmp/nuclei.zip

# Initialize templates (best effort)
RUN /app/nuclei -update-templates || true

# Create non-root user and output directory
RUN adduser -D scanner \
    && mkdir -p /output \
    && chown -R scanner:scanner /app /output

USER scanner

CMD ["/app/nuclei"]


