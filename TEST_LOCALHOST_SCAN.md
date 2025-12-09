# Testing Localhost Scan Endpoint

## ✅ Verification Complete

### 1. Docker Image Status
- **ZAP Image**: `security-tools:zap` - ✅ Built successfully (1.91GB)
- **Image ID**: Latest build completed
- **Dependencies**: All installed (pyyaml, zap_common.py)

### 2. Services Status
- **Backend API**: ✅ Running on http://localhost:8000
- **Frontend**: ✅ Running on http://localhost:3000  
- **Database**: ✅ Running and healthy
- **Redis**: ✅ Running and healthy

## 🧪 Testing the Endpoint

### Option 1: Via Frontend (Recommended)

1. **Open the Frontend**:
   - Navigate to: http://localhost:3000
   - Login or Register if needed

2. **Access LocalHost Testing Page**:
   - Go to: http://localhost:3000/localhost-testing
   - Or navigate through the Dashboard

3. **Run a Scan**:
   - Enter a localhost URL: `http://localhost:3000`
   - Click "Run Local Scan"
   - Wait for the scan to complete (may take 1-2 minutes)
   - View the results and alerts

### Option 2: Via API (cURL)

Use the test script:
```bash
/tmp/test_localhost_scan.sh
```

Or manually:

```bash
# 1. Register a user (if not already registered)
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","username":"testuser","password":"testpass123"}'

# 2. Login to get token
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=testuser&password=testpass123" | \
  python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])")

# 3. Run localhost scan
curl -X POST http://localhost:8000/api/v1/scans/local-testing \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"target_url":"http://localhost:3000","label":"LocalHost Testing"}'
```

## 🔍 What to Expect

### Successful Response
```json
{
  "job_id": "uuid-here",
  "status": "completed",
  "target_url": "http://localhost:3000",
  "environment": "development",
  "alert_count": 0,
  "alerts": [],
  "created_at": "2024-...",
  "completed_at": "2024-..."
}
```

### With Alerts
If ZAP finds security issues, you'll see:
```json
{
  "alert_count": 3,
  "alerts": [
    {
      "name": "X-Content-Type-Options Header Missing",
      "risk": "Low",
      "description": "...",
      "solution": "...",
      "url": "http://localhost:3000"
    }
  ]
}
```

## ⚠️ Important Notes

1. **Localhost Access**: 
   - The ZAP container uses `host.docker.internal` to access localhost services
   - Ensure your target service is actually running on localhost

2. **Scan Duration**:
   - Baseline scans typically take 1-2 minutes
   - The frontend will show "Running OWASP ZAP..." during the scan

3. **Valid URLs**:
   - Only `http://localhost:*` or `http://127.0.0.1:*` are accepted
   - Other hosts will be rejected with a 400 error

## 🐛 Troubleshooting

### Issue: "Image not found"
```bash
# Rebuild the ZAP image
cd docker-tools/zap
docker build -t security-tools:zap .
```

### Issue: "Connection refused"
- Ensure the target service is running on localhost
- Check that the port is accessible: `curl http://localhost:3000`

### Issue: "Authentication failed"
- Make sure you're logged in through the frontend
- Or get a fresh token via the login endpoint

### Issue: "Scan timeout"
- ZAP scans can take time, especially on first run
- Check backend logs for detailed error messages

## 📝 Next Steps

1. ✅ Image built and verified
2. ✅ Endpoint implemented  
3. ✅ Frontend page ready
4. 🧪 **Test via frontend**: http://localhost:3000/localhost-testing

Enjoy testing! 🚀

