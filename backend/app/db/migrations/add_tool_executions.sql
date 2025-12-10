-- Migration: Add tool_executions table to store tool outputs
-- This table stores the execution results and outputs from each tool in the scan pipeline

CREATE TABLE IF NOT EXISTS tool_executions (
    id SERIAL PRIMARY KEY,
    job_id UUID REFERENCES scan_jobs(job_id) ON DELETE CASCADE,
    tool_id INTEGER REFERENCES tools(id),
    stage_number INTEGER NOT NULL,
    stage_name VARCHAR(200) NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    execution_time INTEGER,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    output TEXT,
    raw_output TEXT,
    error TEXT,
    input_data TEXT
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_tool_executions_job_id ON tool_executions(job_id);
CREATE INDEX IF NOT EXISTS idx_tool_executions_tool_id ON tool_executions(tool_id);
CREATE INDEX IF NOT EXISTS idx_tool_executions_stage_number ON tool_executions(stage_number);

