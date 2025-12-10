-- SQL Queries to Retrieve Scan Data from Database
-- Use these queries to verify scans are working and retrieve all findings and tool outputs

-- ============================================================================
-- 1. GET ALL SCAN JOBS WITH STATUS
-- ============================================================================
SELECT 
    sj.job_id,
    sj.status,
    sj.created_at,
    sj.completed_at,
    t.url as target_url,
    u.username,
    COUNT(DISTINCT f.id) as findings_count,
    COUNT(DISTINCT te.id) as tool_executions_count
FROM scan_jobs sj
LEFT JOIN targets t ON sj.target_id = t.id
LEFT JOIN users u ON sj.user_id = u.id
LEFT JOIN findings f ON f.job_id = sj.job_id
LEFT JOIN tool_executions te ON te.job_id = sj.job_id
GROUP BY sj.job_id, sj.status, sj.created_at, sj.completed_at, t.url, u.username
ORDER BY sj.created_at DESC;

-- ============================================================================
-- 2. GET ALL FINDINGS FOR A SPECIFIC JOB
-- ============================================================================
-- Replace 'JOB_ID_HERE' with actual job_id UUID
SELECT 
    f.id,
    f.severity,
    f.status,
    f.location,
    f.evidence,
    f.confidence,
    f.first_seen_at,
    vd.name as vulnerability_name,
    vd.description,
    vd.recommendation,
    t.display_name as tool_name,
    t.name as tool_id
FROM findings f
JOIN vulnerability_definitions vd ON f.definition_id = vd.id
JOIN tools t ON f.tool_id = t.id
WHERE f.job_id = 'JOB_ID_HERE'  -- Replace with actual job_id
ORDER BY 
    CASE f.severity
        WHEN 'critical' THEN 1
        WHEN 'high' THEN 2
        WHEN 'medium' THEN 3
        WHEN 'low' THEN 4
        WHEN 'info' THEN 5
    END,
    f.first_seen_at;

-- ============================================================================
-- 3. GET ALL TOOL EXECUTIONS (OUTPUTS) FOR A SPECIFIC JOB
-- ============================================================================
-- Replace 'JOB_ID_HERE' with actual job_id UUID
SELECT 
    te.id,
    te.stage_number,
    te.stage_name,
    te.status,
    te.execution_time,
    te.started_at,
    te.completed_at,
    t.display_name as tool_name,
    t.name as tool_id,
    te.input_data,
    LEFT(te.output, 500) as output_preview,  -- First 500 chars
    LEFT(te.raw_output, 500) as raw_output_preview,  -- First 500 chars
    te.error
FROM tool_executions te
JOIN tools t ON te.tool_id = t.id
WHERE te.job_id = 'JOB_ID_HERE'  -- Replace with actual job_id
ORDER BY te.stage_number;

-- ============================================================================
-- 4. GET FULL TOOL OUTPUT (for specific execution)
-- ============================================================================
-- Replace EXECUTION_ID with actual tool_execution id
SELECT 
    te.stage_name,
    t.display_name as tool_name,
    te.input_data,
    te.output,
    te.raw_output,
    te.error,
    te.execution_time
FROM tool_executions te
JOIN tools t ON te.tool_id = t.id
WHERE te.id = EXECUTION_ID;  -- Replace with actual execution id

-- ============================================================================
-- 5. GET FINDINGS SUMMARY BY SEVERITY FOR A JOB
-- ============================================================================
SELECT 
    f.severity,
    COUNT(*) as count,
    COUNT(CASE WHEN f.status = 'new' THEN 1 END) as new_count,
    COUNT(CASE WHEN f.status = 'resolved' THEN 1 END) as resolved_count
FROM findings f
WHERE f.job_id = 'JOB_ID_HERE'  -- Replace with actual job_id
GROUP BY f.severity
ORDER BY 
    CASE f.severity
        WHEN 'critical' THEN 1
        WHEN 'high' THEN 2
        WHEN 'medium' THEN 3
        WHEN 'low' THEN 4
        WHEN 'info' THEN 5
    END;

-- ============================================================================
-- 6. GET FINDINGS BY TOOL FOR A JOB
-- ============================================================================
SELECT 
    t.display_name as tool_name,
    t.name as tool_id,
    COUNT(*) as findings_count,
    COUNT(CASE WHEN f.severity = 'critical' THEN 1 END) as critical,
    COUNT(CASE WHEN f.severity = 'high' THEN 1 END) as high,
    COUNT(CASE WHEN f.severity = 'medium' THEN 1 END) as medium,
    COUNT(CASE WHEN f.severity = 'low' THEN 1 END) as low,
    COUNT(CASE WHEN f.severity = 'info' THEN 1 END) as info
FROM findings f
JOIN tools t ON f.tool_id = t.id
WHERE f.job_id = 'JOB_ID_HERE'  -- Replace with actual job_id
GROUP BY t.display_name, t.name
ORDER BY findings_count DESC;

-- ============================================================================
-- 7. GET ALL STAGES STATUS FOR A JOB
-- ============================================================================
SELECT 
    te.stage_number,
    te.stage_name,
    t.display_name as tool_name,
    te.status,
    te.execution_time,
    CASE 
        WHEN te.error IS NOT NULL THEN 'Has Error'
        ELSE 'No Error'
    END as error_status,
    te.started_at,
    te.completed_at,
    LENGTH(te.output) as output_size,
    LENGTH(te.raw_output) as raw_output_size
FROM tool_executions te
JOIN tools t ON te.tool_id = t.id
WHERE te.job_id = 'JOB_ID_HERE'  -- Replace with actual job_id
ORDER BY te.stage_number;

-- ============================================================================
-- 8. GET RECENT SCANS WITH COMPLETE INFORMATION
-- ============================================================================
SELECT 
    sj.job_id,
    sj.status,
    t.url as target_url,
    sj.created_at,
    sj.completed_at,
    EXTRACT(EPOCH FROM (sj.completed_at - sj.created_at)) as duration_seconds,
    (SELECT COUNT(*) FROM findings WHERE job_id = sj.job_id) as total_findings,
    (SELECT COUNT(*) FROM tool_executions WHERE job_id = sj.job_id) as stages_completed,
    (SELECT COUNT(*) FROM tool_executions WHERE job_id = sj.job_id AND status = 'failed') as stages_failed
FROM scan_jobs sj
JOIN targets t ON sj.target_id = t.id
WHERE sj.status IN ('completed', 'failed')
ORDER BY sj.created_at DESC
LIMIT 10;

-- ============================================================================
-- 9. GET ALL TOOL OUTPUTS FOR ALL JOBS (Summary)
-- ============================================================================
SELECT 
    sj.job_id,
    t.url as target_url,
    te.stage_number,
    te.stage_name,
    tool.display_name as tool_name,
    te.status,
    te.execution_time,
    te.error IS NOT NULL as has_error
FROM scan_jobs sj
JOIN targets t ON sj.target_id = t.id
JOIN tool_executions te ON te.job_id = sj.job_id
JOIN tools tool ON te.tool_id = tool.id
ORDER BY sj.created_at DESC, te.stage_number;

-- ============================================================================
-- 10. EXPORT FULL SCAN DATA FOR A JOB (JSON-like format)
-- ============================================================================
-- This query gives you all data in a structured format
SELECT 
    json_build_object(
        'job_id', sj.job_id,
        'target_url', t.url,
        'status', sj.status,
        'created_at', sj.created_at,
        'completed_at', sj.completed_at,
        'stages', (
            SELECT json_agg(
                json_build_object(
                    'stage_number', te.stage_number,
                    'stage_name', te.stage_name,
                    'tool_name', tool.display_name,
                    'status', te.status,
                    'execution_time', te.execution_time,
                    'has_output', te.output IS NOT NULL,
                    'has_error', te.error IS NOT NULL
                )
            )
            FROM tool_executions te
            JOIN tools tool ON te.tool_id = tool.id
            WHERE te.job_id = sj.job_id
        ),
        'findings_summary', (
            SELECT json_build_object(
                'total', COUNT(*),
                'critical', COUNT(*) FILTER (WHERE severity = 'critical'),
                'high', COUNT(*) FILTER (WHERE severity = 'high'),
                'medium', COUNT(*) FILTER (WHERE severity = 'medium'),
                'low', COUNT(*) FILTER (WHERE severity = 'low'),
                'info', COUNT(*) FILTER (WHERE severity = 'info')
            )
            FROM findings
            WHERE job_id = sj.job_id
        )
    ) as scan_data
FROM scan_jobs sj
JOIN targets t ON sj.target_id = t.id
WHERE sj.job_id = 'JOB_ID_HERE';  -- Replace with actual job_id

