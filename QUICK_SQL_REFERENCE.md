# Quick SQL Reference - Get Scan Data

## 🔍 Most Common Queries

### 1. Get All Scans with Summary
```sql
SELECT 
    sj.job_id,
    sj.status,
    t.url as target_url,
    sj.created_at,
    sj.completed_at,
    (SELECT COUNT(*) FROM findings WHERE job_id = sj.job_id) as findings_count,
    (SELECT COUNT(*) FROM tool_executions WHERE job_id = sj.job_id) as stages_count
FROM scan_jobs sj
JOIN targets t ON sj.target_id = t.id
ORDER BY sj.created_at DESC;
```

### 2. Get All Findings for a Job
```sql
-- Replace 'YOUR_JOB_ID' with actual UUID
SELECT 
    f.id,
    f.severity,
    f.location,
    vd.name as vulnerability_name,
    vd.description,
    t.display_name as tool_name,
    f.evidence
FROM findings f
JOIN vulnerability_definitions vd ON f.definition_id = vd.id
JOIN tools t ON f.tool_id = t.id
WHERE f.job_id = 'YOUR_JOB_ID'
ORDER BY 
    CASE f.severity
        WHEN 'critical' THEN 1
        WHEN 'high' THEN 2
        WHEN 'medium' THEN 3
        WHEN 'low' THEN 4
        WHEN 'info' THEN 5
    END;
```

### 3. Get All Tool Outputs for a Job
```sql
-- Replace 'YOUR_JOB_ID' with actual UUID
SELECT 
    te.stage_number,
    te.stage_name,
    t.display_name as tool_name,
    te.status,
    te.execution_time,
    te.output,
    te.raw_output,
    te.error,
    te.input_data
FROM tool_executions te
JOIN tools t ON te.tool_id = t.id
WHERE te.job_id = 'YOUR_JOB_ID'
ORDER BY te.stage_number;
```

### 4. Get Tool Output for Specific Stage
```sql
-- Get Stage 1 (Sublist3r) output
SELECT te.output, te.raw_output, te.error
FROM tool_executions te
JOIN tools t ON te.tool_id = t.id
WHERE te.job_id = 'YOUR_JOB_ID' 
  AND te.stage_number = 1;

-- Get Stage 2 (Httpx) output
SELECT te.output, te.raw_output, te.error
FROM tool_executions te
WHERE te.job_id = 'YOUR_JOB_ID' 
  AND te.stage_number = 2;

-- Get Stage 3 (Gobuster) output
SELECT te.output, te.raw_output, te.error
FROM tool_executions te
WHERE te.job_id = 'YOUR_JOB_ID' 
  AND te.stage_number = 3;

-- Get Stage 4 (ZAP) output
SELECT te.output, te.raw_output, te.error
FROM tool_executions te
WHERE te.job_id = 'YOUR_JOB_ID' 
  AND te.stage_number = 4;

-- Get Stage 5 (Nuclei) output
SELECT te.output, te.raw_output, te.error
FROM tool_executions te
WHERE te.job_id = 'YOUR_JOB_ID' 
  AND te.stage_number = 5;

-- Get Stage 6 (SQLMap) output
SELECT te.output, te.raw_output, te.error
FROM tool_executions te
WHERE te.job_id = 'YOUR_JOB_ID' 
  AND te.stage_number = 6;
```

### 5. Get Findings Summary by Severity
```sql
SELECT 
    f.severity,
    COUNT(*) as count
FROM findings f
WHERE f.job_id = 'YOUR_JOB_ID'
GROUP BY f.severity
ORDER BY 
    CASE f.severity
        WHEN 'critical' THEN 1
        WHEN 'high' THEN 2
        WHEN 'medium' THEN 3
        WHEN 'low' THEN 4
        WHEN 'info' THEN 5
    END;
```

### 6. Get Findings by Tool
```sql
SELECT 
    t.display_name as tool_name,
    COUNT(*) as findings_count,
    COUNT(CASE WHEN f.severity = 'critical' THEN 1 END) as critical,
    COUNT(CASE WHEN f.severity = 'high' THEN 1 END) as high
FROM findings f
JOIN tools t ON f.tool_id = t.id
WHERE f.job_id = 'YOUR_JOB_ID'
GROUP BY t.display_name;
```

### 7. Check if Scan Has All Stages
```sql
SELECT 
    te.stage_number,
    te.stage_name,
    t.display_name as tool_name,
    te.status,
    te.execution_time,
    CASE WHEN te.error IS NOT NULL THEN 'YES' ELSE 'NO' END as has_error
FROM tool_executions te
JOIN tools t ON te.tool_id = t.id
WHERE te.job_id = 'YOUR_JOB_ID'
ORDER BY te.stage_number;
```

### 8. Get Latest Job ID for a Target
```sql
SELECT sj.job_id
FROM scan_jobs sj
JOIN targets t ON sj.target_id = t.id
WHERE t.url = 'https://example.com'
ORDER BY sj.created_at DESC
LIMIT 1;
```

## 📊 Verification Queries

### Check if Scans are Working
```sql
-- Count scans by status
SELECT status, COUNT(*) as count
FROM scan_jobs
GROUP BY status;

-- Count total findings
SELECT COUNT(*) as total_findings FROM findings;

-- Count tool executions
SELECT COUNT(*) as total_executions FROM tool_executions;

-- Check if any scans have all 6 stages
SELECT 
    sj.job_id,
    t.url,
    COUNT(DISTINCT te.stage_number) as stages_completed
FROM scan_jobs sj
JOIN targets t ON sj.target_id = t.id
LEFT JOIN tool_executions te ON te.job_id = sj.job_id
WHERE sj.status = 'completed'
GROUP BY sj.job_id, t.url
HAVING COUNT(DISTINCT te.stage_number) = 6;
```

## 🔧 How to Use

1. **Connect to PostgreSQL:**
   ```bash
   psql -h localhost -p 5432 -U postgres -d Bugbust3r
   ```

2. **Get a Job ID:**
   ```sql
   SELECT job_id, status, created_at 
   FROM scan_jobs 
   ORDER BY created_at DESC 
   LIMIT 5;
   ```

3. **Replace 'YOUR_JOB_ID'** in queries with the actual UUID

4. **View Output:**
   - `output` column contains JSON string of tool results
   - `raw_output` contains raw stdout/stderr
   - Use `LEFT(te.output, 1000)` to preview large outputs

## 📝 Notes

- All `job_id` values are UUIDs
- Tool outputs are stored as JSON strings
- Use `jsonb_pretty()` in PostgreSQL to format JSON output:
  ```sql
  SELECT jsonb_pretty(te.output::jsonb) as formatted_output
  FROM tool_executions te
  WHERE te.id = EXECUTION_ID;
  ```

