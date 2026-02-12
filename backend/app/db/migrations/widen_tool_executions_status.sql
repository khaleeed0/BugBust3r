-- Widen tool_executions.status to allow values like 'completed_with_issues' (21 chars)
-- Run with: psql -h localhost -p 5432 -U postgres -d Bugbust3r -f widen_tool_executions_status.sql

ALTER TABLE tool_executions
  ALTER COLUMN status TYPE VARCHAR(50);
