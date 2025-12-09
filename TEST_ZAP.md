# Testing ZAP Integration

This guide explains how to test the ZAP (OWASP ZAP) integration in the Bugbuster project.

## Issue Fixed

The ZAP baseline script requires the `/zap/wrk` directory to be mounted as a volume. This has been fixed by creating a temporary directory and mounting it properly.

## Prerequisites

1. **ZAP Docker Image**: The `security-tools:zap` image must be built
   ```bash
   cd docker-tools/zap
   docker build -t security-tools:zap .
   ```

2. **Docker Running**: Ensure Docker is running and accessible

3. **Backend Running**: The backend service should be running (via docker-compose or directly)

## Testing ZAP

### Option 1: Using the Test Script

Run the automated test script:

```bash
# From the project root
cd backend
python3 test_zap.py
```

This will:
- Check if the ZAP image exists
- Test a scan on localhost:5000 (if a service is running)
- Test a scan on an external URL (example.com)

### Option 2: Using the Frontend

1. Start the test server (in a separate terminal):
   ```bash
   cd backend
   python3 test_server.py
   ```
   This starts a simple HTTP server on `http://localhost:5000`

2. Open the frontend and navigate to the LocalHost Testing page:
   - Go to `http://localhost:3000/local-host-testing`
   - Enter `http://localhost:5000` in the URL field
   - Click "Run Local Scan"

3. Wait for the scan to complete (may take 1-2 minutes)

4. View the results:
   - If successful: You'll see alerts and scan details
   - If failed: You'll see the error message in a red box

### Option 3: Manual Docker Test

Test ZAP directly using Docker:

```bash
# Create a temporary directory for ZAP work
mkdir -p /tmp/zap_work

# Run ZAP scan
docker run --rm \
  -v /tmp/zap_work:/zap/wrk \
  --add-host=host.docker.internal:host-gateway \
  security-tools:zap \
  python3 /app/zap-baseline.py -t http://host.docker.internal:5000 -J -j -d

# Clean up
rm -rf /tmp/zap_work
```

## Expected Results

### Successful Scan
- Status: `completed` or `completed_with_alerts`
- Alerts: List of security issues found (if any)
- Exit code: 0

### Failed Scan
- Status: `failed`
- Error message displayed
- Common errors:
  - Image not found: Build the ZAP image
  - Connection refused: Target service not running
  - Volume mount error: Should be fixed now

## Troubleshooting

### Error: "Image not found"
```bash
cd docker-tools/zap
docker build -t security-tools:zap .
```

### Error: "Connection refused" or "Cannot connect to target"
- Ensure the target service is running
- For localhost scans, the service must be accessible from Docker
- Use `host.docker.internal` instead of `localhost` (handled automatically)

### Error: "/zap/wrk is not mounted"
- This should be fixed now
- If you still see this, check backend logs:
  ```bash
  docker logs security_scanner_backend
  ```

### Scan takes too long
- ZAP scans can take 1-5 minutes depending on the target
- This is normal behavior
- Check backend logs for progress

## Viewing Logs

### Backend Logs
```bash
docker logs security_scanner_backend -f
```

### ZAP Container Logs
If running ZAP manually, logs are shown in stdout/stderr.

## Next Steps

After verifying ZAP works:
1. Test with different target URLs
2. Review the alerts found
3. Check the frontend displays results correctly
4. Verify error handling works for various failure scenarios

