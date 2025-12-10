FROM python:3.9-slim

WORKDIR /app

# Install dependencies
RUN apt-get update && apt-get install -y \
    git \
    && rm -rf /var/lib/apt/lists/*

# Clone SQLMap
RUN git clone --depth 1 https://github.com/sqlmapproject/sqlmap.git /app/sqlmap

WORKDIR /app/sqlmap

# SQLMap doesn't have a requirements.txt, install common dependencies
RUN pip install --no-cache-dir requests

# Create output directory
RUN mkdir -p /output

CMD ["python3", "sqlmap.py"]


