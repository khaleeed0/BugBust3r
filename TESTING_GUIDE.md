# Complete Testing Guide

This guide walks you through verifying that scans work correctly and tools execute properly.

## Quick Start

Run all tests in sequence:
```bash
cd backend
./run_all_tests.sh
```

Or run tests individually:

## Step-by-Step Testing

### Step 1: Verify Database ✅

```bash
cd backend
python3 test_database.py
```

**What it checks:**
- Database connection
- All required tables exist
- Tables are accessible
- Indexes are in place

**Expected Result:**
```
✅ ALL DATABASE TESTS PASSED
Database is ready for scans!
```

**If it fails:**
- Check PostgreSQL is running
- Verify database connection string in `.env`
- Run migrations if tables are missing

### Step 2: Test Individual Tools 🔧

```bash
cd backend
python3 test_scan_execution.py
```

This will:
1. Test Docker connection
2. Check all Docker images exist
3. Test each tool individually
4. Optionally test full scan workflow
5. Optionally test batch scans

**What it tests:**
- ✅ Sublist3r - Subdomain enumeration
- ✅ Httpx - HTTP service detection  
- ✅ Gobuster - Directory discovery
- ✅ ZAP - Web application scanning
- ✅ Nuclei - Template-based scanning
- ✅ SQLMap - SQL injection testing

**Expected Result:**
```
✅ TOOLS ARE READY TO RUN
You can start scans and they will execute all 6 stages
```

### Step 3: Verify Scan Data 📊

```bash
cd backend
python3 verify_scan_data.py
```

**What it shows:**
- Total scans and their status
- Findings statistics
- Tool execution statistics
- Recent scans with details
- Sample findings and outputs

## Testing a Real Scan

### Option 1: Via Frontend

1. **Start the application:**
   ```bash
   ./start-project-mac.sh
   ```

2. **Register/Login:**
   - Go to http://localhost:3000
   - Register a new account or login

3. **Create a Target:**
   - Go to Dashboard
   - Add a new target (e.g., `https://example.com`)

4. **Start a Scan:**
   - Click "Start Scan" on the target
   - Wait for completion (5-10 minutes)

5. **View Results:**
   - Go to Reports page
   - Click "View Report" on the completed scan
   - Verify all 6 stages are shown
   - Check findings are displayed

### Option 2: Via API

```bash
# 1. Login and get token
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=YOUR_USER&password=YOUR_PASS" | \
  python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])")

# 2. Create target
TARGET_RESPONSE=$(curl -s -X POST http://localhost:8000/api/v1/targets \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"url":"https://example.com","name":"Test"}')

TARGET_ID=$(echo $TARGET_RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin)['id'])")

# 3. Start scan
SCAN_RESPONSE=$(curl -s -X POST http://localhost:8000/api/v1/scans \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"target_id\":$TARGET_ID}")

JOB_ID=$(echo $SCAN_RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin)['job_id'])")

echo "Scan started! Job ID: $JOB_ID"

# 4. Check status (wait a bit first)
sleep 10
curl -s http://localhost:8000/api/v1/jobs/$JOB_ID/status \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
```

## Verifying Scan Results

### Check Database

```sql
-- Connect to database
psql -h localhost -p 5432 -U postgres -d Bugbust3r

-- Get recent scans
SELECT job_id, status, created_at 
FROM scan_jobs 
ORDER BY created_at DESC 
LIMIT 5;

-- Check tool executions for a job (replace JOB_ID)
SELECT 
    stage_number,
    stage_name,
    status,
    execution_time
FROM tool_executions
WHERE job_id = 'JOB_ID'
ORDER BY stage_number;

-- Check findings for a job
SELECT 
    severity,
    COUNT(*) as count
FROM findings
WHERE job_id = 'JOB_ID'
GROUP BY severity;
```

### Check via API

```bash
# Get reports
curl -s http://localhost:8000/api/v1/reports \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool

# Get specific report (replace JOB_ID)
curl -s http://localhost:8000/api/v1/reports/JOB_ID \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
```

## Troubleshooting

### Tools Not Running

**Check Docker:**
```bash
docker ps
docker images | grep security-tools
```

**Build missing images:**
```bash
cd docker-tools
./build-all.sh
```

### Database Issues

**Check connection:**
```bash
psql -h localhost -p 5432 -U postgres -d Bugbust3r -c "SELECT version();"
```

**Run migrations:**
```bash
psql -h localhost -p 5432 -U postgres -d Bugbust3r -f backend/app/db/migrations/add_tool_executions.sql
```

### Scan Stuck

**Check job status:**
```sql
SELECT job_id, status, created_at, completed_at
FROM scan_jobs
WHERE status = 'running'
ORDER BY created_at DESC;
```

**Check backend logs:**
```bash
docker logs security_scanner_backend -f
```

## Expected Behavior

When everything works:

1. ✅ Database has all tables
2. ✅ All 6 Docker images exist
3. ✅ Each tool can run individually
4. ✅ Full scan creates job with status 'pending'
5. ✅ Job status changes to 'running'
6. ✅ All 6 stages execute in sequence
7. ✅ 6 records created in `tool_executions`
8. ✅ Multiple records created in `findings`
9. ✅ Job status changes to 'completed'
10. ✅ Report shows all stages and findings

## Success Criteria

A scan is successful if:
- ✅ Job status is 'completed'
- ✅ All 6 stages have `tool_executions` records
- ✅ At least some `findings` are created
- ✅ No critical errors in logs
- ✅ Report page displays all data

## Next Steps

After verification:
1. Run scans on real targets you own
2. Review findings in the Reports page
3. Export reports if needed
4. Monitor scan performance
5. Adjust tool configurations if needed

