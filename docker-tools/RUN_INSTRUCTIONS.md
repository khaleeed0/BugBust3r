# Security Tool Containers - Run Instructions

Each tool is packaged as a standalone Docker container. Use the following commands to run them manually outside the orchestrated scan service.

> **Tip:** Replace `example.com` with your actual target. Only scan assets you own or have permission to test.

---

## Sublist3r (Subdomain Enumeration)

```bash
docker run --rm security-tools:sublist3r python3 sublist3r.py -d example.com
```

Additional options (see `-h`):
```bash
docker run --rm security-tools:sublist3r python3 sublist3r.py -d example.com -t 50 -o /output/results.txt
```

---

## Httpx (HTTP Service Detection)

```bash
echo "https://example.com" | docker run -i --rm security-tools:httpx /app/httpx -title -tech-detect
```

Scan a list of subdomains:
```bash
cat subdomains.txt | docker run -i --rm security-tools:httpx /app/httpx -json -o /output/httpx.json
```

---

## Gobuster (Directory Discovery)

```bash
docker run --rm security-tools:gobuster /app/gobuster dir -u https://example.com -w /wordlists/common.txt
```

You can mount a custom wordlist:
```bash
docker run --rm -v $(pwd)/wordlists:/data security-tools:gobuster \
  /app/gobuster dir -u https://example.com -w /data/custom.txt -t 50
```

---

## OWASP ZAP Baseline

```bash
docker run --rm security-tools:zap /app/zap-baseline.py -t https://example.com -r report.html
```

Generate JSON report:
```bash
docker run --rm -v $(pwd)/output:/output security-tools:zap \
  /app/zap-baseline.py -t https://example.com -J /output/zap-report.json
```

---

## Nuclei (Template-Based Scanning)

```bash
docker run --rm security-tools:nuclei /app/nuclei -u https://example.com -severity medium,high -json
```

Specify templates:
```bash
docker run --rm security-tools:nuclei /app/nuclei -u https://example.com -t cves/ -json -o /output/nuclei.json
```

---

## SQLMap (SQL Injection Testing)

```bash
docker run --rm security-tools:sqlmap python3 sqlmap.py -u "https://example.com/page?id=1" --batch
```

Dump database example:
```bash
docker run --rm security-tools:sqlmap python3 sqlmap.py \
  -u "https://example.com/page?id=1" --batch --dump
```

---

## AddressSanitizer (C/C++ Memory Safety)

Runs a demo vulnerable program by default (detects stack-buffer-overflow). Optional: mount your C/C++ source directory.

```bash
# Demo mode (creates and runs a small vulnerable C program)
docker run --rm security-tools:addresssanitizer sh -c "USE_DEMO=true /app/run_asan.sh"

# Scan your source (replace /path/to/source with host path; use absolute path)
docker run --rm -v /path/to/source:/source:ro security-tools:addresssanitizer sh -c "USE_DEMO=false /app/run_asan.sh"
```

---

## Ghauri (SQL Injection – Blind SQLi, PostgreSQL-friendly)

Uses `host.docker.internal` to reach a target on the host (macOS/Windows). For Linux use `--network host` and `127.0.0.1`.

```bash
# Help
docker run --rm security-tools:ghauri -h

# Test localhost target (macOS/Windows)
docker run --rm security-tools:ghauri -u "http://host.docker.internal:8000/item?id=1" --batch --dbs --level=1

# Enumerate databases
docker run --rm security-tools:ghauri -u "http://host.docker.internal:8000/page?id=1" --batch --current-db
```

---

## Notes

- All images are tagged as `security-tools:<toolname>` after running `build-all.sh`.
- Use `docker pull` to refresh base images before building if needed.
- Mount volumes when you need to persist output (e.g., `-v $(pwd)/output:/output`).
- Some tools (e.g., ZAP, SQLMap) may take significant time depending on target complexity.


