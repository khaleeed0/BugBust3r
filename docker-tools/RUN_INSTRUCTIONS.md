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

## Notes

- All images are tagged as `security-tools:<toolname>` after running `build-all.sh`.
- Use `docker pull` to refresh base images before building if needed.
- Mount volumes when you need to persist output (e.g., `-v $(pwd)/output:/output`).
- Some tools (e.g., ZAP, SQLMap) may take significant time depending on target complexity.


