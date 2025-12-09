# Testing Scan Workflow

This guide explains how to verify that scans are working and tools execute correctly.

## Step 1: Verify Database

First, check that the database is properly set up:

```bash
cd backend
python3 test_database.py
```

This will verify:
- ✅ Database connection
- ✅ All required tables exist
- ✅ Tables are accessible
- ✅ Indexes are in place

**Expected Output:**
```
✅ Database connected successfully
✅ Table 'scan_jobs' exists
✅ Table 'findings' exists
✅ Table 'tool_executions' exists
...
✅ ALL DATABASE TESTS PASSED
```

## Step 2: Test Tool Execution

Test that all tools can run:

```bash
cd backend
python3 test_scan_execution.py
```

This will:
1. **Test Docker Connection** - Verifies Docker daemon is running
2. **Test Docker Images** - Checks all 6 tool images exist
3. **Test Individual Tools** - Runs each tool separately
4. **Test Full Scan Workflow** - Runs a complete scan (optional)
5. **Test Batch Scans** - Runs multiple scans (optional)

### Individual Tool Tests

Each tool is tested with a safe target (`example.com`):
- **Sublist3r**: Subdomain enumeration
- **Httpx**: HTTP service detection
- **Gobuster**: Directory discovery
- **ZAP**: Web application scanning (takes 30-60 seconds)
- **Nuclei**: Template-based scanning
- **SQLMap**: SQL injection testing

### Full Scan Workflow Test

This creates a real scan job and runs all 6 stages:
1. Creates a test target
2. Creates a scan job
3. Executes all 6 stages in sequence
4. Verifies results are stored in database

**Note:** This takes 5-10 minutes to complete.

### Batch Scan Test

Tests multiple scans in sequence to verify:
- Multiple jobs can run
- Database handles concurrent data
- Tools work consistently

## Step 3: Verify Results in Database

After running tests, verify data is stored:

```bash
# Run verification script
python3 verify_scan_data.py

# Or use SQL directly
psql -h localhost -p 5432 -U postgres -d Bugbust3r
```

### Quick SQL Checks

```sql
-- Check scan jobs
SELECT job_id, status, created_at 
FROM scan_jobs 
ORDER BY created_at DESC 
LIMIT 5;

-- Check tool executions
SELECT 
    stage_number,
    stage_name,
    status,
    execution_time
FROM tool_executions
ORDER BY completed_at DESC
LIMIT 10;

-- Check findings
SELECT 
    severity,
    COUNT(*) as count
FROM findings
GROUP BY severity;
```

## Step 4: Test via API

You can also test scans via the API:

```bash
# 1. Get auth token (login)
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=YOUR_USERNAME&password=YOUR_PASSWORD" | \
  python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])")

# 2. Create a target
TARGET_ID=$(curl -s -X POST http://localhost:8000/api/v1/targets \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"url":"https://example.com","name":"Test Target"}' | \
  python3 -c "import sys, json; print(json.load(sys.stdin)['id'])")

# 3. Start a scan
JOB_RESPONSE=$(curl -s -X POST http://localhost:8000/api/v1/scans \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"target_id\":$TARGET_ID}")

echo $JOB_RESPONSE | python3 -m json.tool

# 4. Check scan status (replace JOB_ID)
curl -s http://localhost:8000/api/v1/jobs/JOB_ID/status \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
```

## Troubleshooting

### Docker Issues

If tools fail to run:
```bash
# Check Docker is running
docker ps

# Check if images exist
docker images | grep security-tools

# Build missing images
cd docker-tools/[tool-name]
docker build -t security-tools:[tool-name] .
```

### Database Issues

If database tests fail:
```bash
# Check PostgreSQL is running
psql -h localhost -p 5432 -U postgres -d Bugbust3r -c "SELECT version();"

# Run migration if tool_executions table is missing
psql -h localhost -p 5432 -U postgres -d Bugbust3r -f backend/app/db/migrations/add_tool_executions.sql
```

### Tool Execution Issues

If individual tools fail:
1. Check Docker logs: `docker logs [container-name]`
2. Verify image is built correctly
3. Check network connectivity
4. Verify target URL is accessible

## Expected Behavior

When a scan runs successfully:

1. **Job Created**: `scan_jobs` table has new record with status 'pending'
2. **Status Changes**: Job status changes to 'running', then 'completed'
3. **Tool Executions**: 6 records created in `tool_executions` table (one per stage)
4. **Findings Created**: Multiple records in `findings` table (vulnerabilities discovered)
5. **Data Flow**: Each stage's output is stored and passed to next stage

## Verification Checklist

- [ ] Database connection works
- [ ] All tables exist and are accessible
- [ ] Docker daemon is running
- [ ] All 6 Docker images exist
- [ ] Each tool can run individually
- [ ] Full scan workflow completes
- [ ] Data is stored in database
- [ ] Findings are created
- [ ] Tool executions are stored
- [ ] Reports can be generated

## Next Steps

After verification:
1. Run a real scan on a target you own
2. Check the reports page in the frontend
3. Verify all findings are displayed
4. Check tool outputs in the database
5. Generate reports

