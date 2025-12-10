# Database Migration Guide

## Overview

The database schema has been updated to match the comprehensive schema documentation. This guide explains the changes and how to migrate.

## Key Changes

### 1. User Model
- **Added**: `role` field (default: 'user')
- **Added**: `api_key` field for API access
- **Removed**: `is_active` field (users are active by default)
- **Changed**: `hashed_password` → `password_hash`

### 2. New Target Model
- **New Table**: `targets`
- Stores assets to be scanned
- Links to users via `user_id`
- Includes `asset_value` for prioritization

### 3. New Tool Model
- **New Table**: `tools`
- Registry of all security scanners
- Stores Docker image and queue information

### 4. ScanJob Model Updates
- **Changed**: Uses UUID `job_id` instead of integer
- **Changed**: Links to `target_id` instead of storing `target_url`
- **Removed**: `error_message` field
- **Removed**: `updated_at` field

### 5. New ScanSchedule Model
- **New Table**: `scan_schedules`
- Stores recurring scan configurations

### 6. New VulnerabilityDefinition Model
- **New Table**: `vulnerability_definitions`
- Master catalog of vulnerability types
- Prevents data redundancy

### 7. New Finding Model
- **New Table**: `findings`
- Replaces `JobResult` table
- Links to job, tool, vulnerability definition, and target
- Tracks remediation lifecycle

### 8. Report Model Updates
- **Changed**: Links to `job_id` (UUID) instead of integer
- **Added**: `format` field (pdf, html, etc.)
- **Changed**: `file_path` instead of storing content

## Migration Steps

### Option 1: Fresh Start (Recommended for Development)

1. Drop existing database:
```sql
DROP DATABASE security_scanner;
CREATE DATABASE security_scanner;
```

2. Run the new schema:
```bash
psql -U postgres -d security_scanner -f backend/app/db/schema.sql
```

Or use the Python init script:
```bash
python backend/app/db/init_db.py
```

### Option 2: Manual Migration (For Production)

1. **Backup existing database**:
```bash
pg_dump security_scanner > backup.sql
```

2. **Create new tables**:
```sql
-- Run schema.sql to create new tables
```

3. **Migrate data** (if needed):
```sql
-- Migrate users
INSERT INTO users (id, username, email, password_hash, role, created_at)
SELECT id, username, email, hashed_password, 'user', created_at
FROM old_users;

-- Create targets from old jobs
INSERT INTO targets (user_id, url, created_at)
SELECT DISTINCT owner_id, target_url, created_at
FROM old_jobs;

-- Migrate scan jobs
INSERT INTO scan_jobs (id, job_id, user_id, target_id, status, created_at, completed_at)
SELECT 
    j.id,
    uuid_generate_v4(),
    j.owner_id,
    t.id,
    j.status,
    j.created_at,
    j.completed_at
FROM old_jobs j
JOIN targets t ON t.url = j.target_url;
```

## API Changes

### Endpoints Updated

1. **POST /api/v1/scans**
   - Now requires `target_id` instead of `target_url`
   - Must create target first using `/api/v1/targets`

2. **GET /api/v1/jobs/{job_id}/status**
   - `job_id` is now UUID, not integer
   - Returns `findings` instead of `results`

3. **GET /api/v1/reports**
   - Returns findings summary instead of stage results

### New Endpoints

1. **POST /api/v1/targets** - Create a target
2. **GET /api/v1/targets** - List targets
3. **GET /api/v1/targets/{id}** - Get target details
4. **DELETE /api/v1/targets/{id}** - Delete target

## Frontend Updates Needed

The frontend will need updates to:
1. Create targets before scanning
2. Use UUID for job IDs
3. Display findings instead of stage results
4. Show vulnerability definitions and recommendations

## Testing

After migration, test:
1. User registration and login
2. Target creation
3. Scan job creation
4. Finding creation during scans
5. Report generation
6. Finding status updates

## Rollback

If you need to rollback:
1. Restore from backup
2. Revert code changes
3. Restart services

