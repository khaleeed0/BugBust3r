FROM python:3.9-slim

WORKDIR /app

# Install dependencies
RUN apt-get update && apt-get install -y \
    git \
    && rm -rf /var/lib/apt/lists/*

# Clone and install Sublist3r
RUN git clone https://github.com/aboul3la/Sublist3r.git /app/sublist3r \
    && cd /app/sublist3r \
    && pip install --no-cache-dir -r requirements.txt

# Install Sublist3r dependencies
RUN pip install --no-cache-dir dnspython requests

WORKDIR /app/sublist3r

# Create output directory
RUN mkdir -p /output

CMD ["python3", "sublist3r.py"]


