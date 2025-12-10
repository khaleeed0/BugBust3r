# Semgrep - Static analysis tool for finding bugs and security issues
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Semgrep using pip3
RUN pip3 install --no-cache-dir semgrep

# Verify installation and add to PATH
RUN python3 -m pip show semgrep || pip3 install --no-cache-dir semgrep
RUN which semgrep || echo "semgrep installed via pip"

# Create output directory
RUN mkdir -p /output /source

# Set working directory
WORKDIR /source

# Create symlink if needed (semgrep might be installed as python module)
RUN python3 -c "import semgrep; print('Semgrep installed')" || pip3 install --no-cache-dir semgrep

# Default command
CMD ["python3", "-m", "semgrep", "--help"]

