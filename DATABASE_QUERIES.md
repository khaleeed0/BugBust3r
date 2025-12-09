# Database Queries Guide

This guide provides SQL queries to retrieve scan data, findings, and tool outputs from the database.

## Quick Reference

### Get All Scans
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

### Get All Findings for a Job
```sql
-- Replace 'JOB_ID_HERE' with actual UUID
SELECT 
    f.severity,
    f.location,
    vd.name as vulnerability_name,
    t.display_name as tool_name
FROM findings f
JOIN vulnerability_definitions vd ON f.definition_id = vd.id
JOIN tools t ON f.tool_id = t.id
WHERE f.job_id = 'JOB_ID_HERE'
ORDER BY f.severity;
```

### Get All Tool Outputs for a Job
```sql
-- Replace 'JOB_ID_HERE' with actual UUID
SELECT 
    te.stage_number,
    te.stage_name,
    t.display_name as tool_name,
    te.status,
    te.execution_time,
    te.output,
    te.raw_output,
    te.error
FROM tool_executions te
JOIN tools t ON te.tool_id = t.id
WHERE te.job_id = 'JOB_ID_HERE'
ORDER BY te.stage_number;
```

## Using the Verification Script

Run the Python verification script to check scan data:

```bash
cd backend
python3 verify_scan_data.py
```

This will show:
- Total scans and their status
- Findings statistics by severity
- Tool execution statistics by stage
- Recent scans with details
- Sample findings and tool outputs

## Common Queries

### 1. Find a Job ID by Target URL
```sql
SELECT sj.job_id, sj.status, sj.created_at
FROM scan_jobs sj
JOIN targets t ON sj.target_id = t.id
WHERE t.url = 'https://example.com'
ORDER BY sj.created_at DESC;
```

### 2. Get Findings Count by Tool
```sql
SELECT 
    t.display_name as tool_name,
    COUNT(*) as findings_count
FROM findings f
JOIN tools t ON f.tool_id = t.id
WHERE f.job_id = 'JOB_ID_HERE'
GROUP BY t.display_name;
```

### 3. Get Failed Tool Executions
```sql
SELECT 
    te.stage_name,
    t.display_name as tool_name,
    te.error,
    te.completed_at
FROM tool_executions te
JOIN tools t ON te.tool_id = t.id
WHERE te.status = 'failed'
ORDER BY te.completed_at DESC;
```

### 4. Export Full Scan Data (JSON)
```sql
SELECT 
    json_build_object(
        'job_id', sj.job_id,
        'target_url', t.url,
        'status', sj.status,
        'findings', (
            SELECT json_agg(
                json_build_object(
                    'severity', f.severity,
                    'vulnerability', vd.name,
                    'location', f.location
                )
            )
            FROM findings f
            JOIN vulnerability_definitions vd ON f.definition_id = vd.id
            WHERE f.job_id = sj.job_id
        ),
        'stages', (
            SELECT json_agg(
                json_build_object(
                    'stage', te.stage_name,
                    'tool', tool.display_name,
                    'status', te.status
                )
            )
            FROM tool_executions te
            JOIN tools tool ON te.tool_id = tool.id
            WHERE te.job_id = sj.job_id
        )
    ) as scan_data
FROM scan_jobs sj
JOIN targets t ON sj.target_id = t.id
WHERE sj.job_id = 'JOB_ID_HERE';
```

## Database Tables

### scan_jobs
- `job_id` (UUID) - Primary identifier
- `status` - pending, running, completed, failed
- `created_at`, `completed_at`

### findings
- `job_id` (UUID) - Links to scan_jobs
- `tool_id` - Links to tools
- `definition_id` - Links to vulnerability_definitions
- `severity` - critical, high, medium, low, info
- `location`, `evidence`, `confidence`

### tool_executions
- `job_id` (UUID) - Links to scan_jobs
- `tool_id` - Links to tools
- `stage_number` - 1-6
- `stage_name` - Human-readable stage name
- `status` - pending, running, completed, failed
- `output` - JSON string of tool output
- `raw_output` - Raw stdout/stderr
- `input_data` - JSON string of input passed to tool
- `execution_time` - Seconds
- `error` - Error message if failed

## Notes

- All `job_id` values are UUIDs (format: `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`)
- Tool outputs are stored as JSON strings in the `output` column
- Raw outputs are limited to 10,000 characters
- Use `LEFT(column, N)` to preview large text fields
- Replace `'JOB_ID_HERE'` with actual UUIDs from your database

