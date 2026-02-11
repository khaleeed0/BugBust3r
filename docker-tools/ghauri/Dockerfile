# Ghauri - SQL injection detection and exploitation (Python)
# https://github.com/r0oth3x49/ghauri
# Supports boolean/time/error-based blind SQLi; good for PostgreSQL.
FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*

RUN git clone https://github.com/r0oth3x49/ghauri.git /app/ghauri

WORKDIR /app/ghauri
RUN pip install --no-cache-dir -r requirements.txt && pip install --no-cache-dir -e .

# Non-interactive; attack URL passed at runtime
ENTRYPOINT ["ghauri"]
