-- Enables the use of UUIDs for unique job identifiers
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Stores user account information, roles, and API keys
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) DEFAULT 'user',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    api_key VARCHAR(255) UNIQUE
);

-- Contains the assets to be scanned
CREATE TABLE targets (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    url VARCHAR(500) UNIQUE NOT NULL,
    name VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    description TEXT,
    asset_value VARCHAR(50) -- e.g., 'critical', 'high', 'low'
);

-- A dynamic registry of all available security scanners
CREATE TABLE tools (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL,
    display_name VARCHAR(100) NOT NULL,
    docker_image VARCHAR(255) NOT NULL,
    celery_queue VARCHAR(100) NOT NULL,
    is_enabled BOOLEAN DEFAULT true,
    description TEXT,
    category VARCHAR(50) -- e.g., 'Discovery', 'Scanning'
);

-- A log for every single scan that is executed
CREATE TABLE scan_jobs (
    id SERIAL PRIMARY KEY,
    job_id UUID DEFAULT uuid_generate_v4() UNIQUE NOT NULL,
    user_id INTEGER REFERENCES users(id),
    target_id INTEGER REFERENCES targets(id),
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'running', 'completed', 'failed')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP
);

-- Stores configurations for recurring, automated scans
CREATE TABLE scan_schedules (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    target_id INTEGER REFERENCES targets(id),
    schedule_type VARCHAR(20) DEFAULT 'weekly',
    is_active BOOLEAN DEFAULT true,
    next_scan_at TIMESTAMP
);

-- A master catalog of unique vulnerability types
CREATE TABLE vulnerability_definitions (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) UNIQUE NOT NULL,
    description TEXT,
    recommendation TEXT
);

-- Records every specific instance a vulnerability is discovered
CREATE TABLE findings (
    id SERIAL PRIMARY KEY,
    job_id UUID REFERENCES scan_jobs(job_id) ON DELETE CASCADE,
    tool_id INTEGER REFERENCES tools(id),
    definition_id INTEGER REFERENCES vulnerability_definitions(id),
    target_id INTEGER REFERENCES targets(id),
    severity VARCHAR(20) NOT NULL CHECK (severity IN ('critical', 'high', 'medium', 'low', 'info')),
    status VARCHAR(20) DEFAULT 'new' CHECK (status IN ('new', 'reopened', 'acknowledged', 'resolved', 'false_positive')),
    first_seen_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_seen_at TIMESTAMP,
    location TEXT, -- e.g., URL path, IP:Port, filename
    evidence TEXT, -- e.g., Server response, code snippet
    confidence VARCHAR(20), -- e.g., 'high', 'medium', 'low'
    assigned_to_user_id INTEGER REFERENCES users(id)
);

-- Stores tool execution outputs and results for each stage
CREATE TABLE tool_executions (
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

-- Holds metadata about generated reports
CREATE TABLE reports (
    id SERIAL PRIMARY KEY,
    job_id UUID REFERENCES scan_jobs(job_id) ON DELETE CASCADE,
    format VARCHAR(10) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better performance
CREATE INDEX idx_scan_jobs_user_id ON scan_jobs(user_id);
CREATE INDEX idx_scan_jobs_target_id ON scan_jobs(target_id);
CREATE INDEX idx_scan_jobs_status ON scan_jobs(status);
CREATE INDEX idx_findings_job_id ON findings(job_id);
CREATE INDEX idx_findings_target_id ON findings(target_id);
CREATE INDEX idx_findings_severity ON findings(severity);
CREATE INDEX idx_findings_status ON findings(status);
CREATE INDEX idx_targets_user_id ON targets(user_id);
CREATE INDEX idx_tool_executions_job_id ON tool_executions(job_id);
CREATE INDEX idx_tool_executions_tool_id ON tool_executions(tool_id);
CREATE INDEX idx_tool_executions_stage_number ON tool_executions(stage_number);

