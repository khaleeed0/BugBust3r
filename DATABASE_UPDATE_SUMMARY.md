# Database Schema Update Summary

## Overview

All database models and related code have been updated to match the comprehensive database schema documentation provided. The system now uses a more robust, scalable schema with proper relationships and data normalization.

## Files Updated

### Models (backend/app/models/)

1. **user.py** - Updated User model
   - Added `role` field (default: 'user')
   - Added `api_key` field for API access
   - Changed `hashed_password` to `password_hash`
   - Removed `is_active` field
   - Updated relationships

2. **target.py** - NEW model
   - Complete Target model with all fields
   - Relationships to User, ScanJob, ScanSchedule, and Finding

3. **tool.py** - NEW model
   - Tool registry model
   - Stores Docker image and queue information

4. **job.py** - Completely rewritten
   - `ScanJob` model with UUID `job_id`
   - `ScanSchedule` model for recurring scans
   - `VulnerabilityDefinition` model for vulnerability catalog
   - `Finding` model for individual vulnerabilities
   - `Report` model for generated reports
   - All enums (JobStatus, FindingSeverity, FindingStatus)

### API Endpoints (backend/app/api/v1/endpoints/)

1. **auth.py** - Updated
   - Removed `full_name` from UserCreate
   - Updated UserResponse to match new schema
   - Removed `is_active` check

2. **targets.py** - NEW endpoint
   - POST /api/v1/targets - Create target
   - GET /api/v1/targets - List targets
   - GET /api/v1/targets/{id} - Get target
   - DELETE /api/v1/targets/{id} - Delete target

3. **scans.py** - Updated
   - Now requires `target_id` instead of `target_url`
   - Returns UUID `job_id`
   - Links to Target model

4. **jobs.py** - Updated
   - Uses UUID `job_id` instead of integer
   - Returns findings instead of stage results
   - Links to Target model

5. **reports.py** - Updated
   - Uses UUID `job_id`
   - Returns findings with vulnerability definitions
   - Shows findings summary by severity and status

### Services (backend/app/services/)

1. **scan_service.py** - Completely rewritten
   - Creates/updates Tool records
   - Creates/updates VulnerabilityDefinition records
   - Creates Finding records for each vulnerability
   - Links findings to tools, targets, and vulnerability definitions
   - Tracks first_seen_at and last_seen_at

### Database (backend/app/db/)

1. **database.py** - Updated
   - Added UUID import

2. **init_db.py** - Updated
   - Creates UUID extension
   - Creates all new tables

3. **schema.sql** - NEW file
   - Complete SQL schema matching documentation
   - Includes all indexes

### Configuration

1. **main.py** - Updated
   - Creates UUID extension on startup
   - Handles errors gracefully

## Key Schema Changes

### Before → After

1. **Job → ScanJob**
   - `id` (int) → `id` (int) + `job_id` (UUID)
   - `target_url` (string) → `target_id` (FK to targets)
   - `owner_id` → `user_id`

2. **JobResult → Finding**
   - Stage-based results → Individual vulnerability findings
   - Links to VulnerabilityDefinition
   - Tracks remediation lifecycle
   - Includes severity, confidence, location, evidence

3. **New: Target Model**
   - Centralized target management
   - Links to users
   - Includes asset_value for prioritization

4. **New: Tool Model**
   - Registry of all security tools
   - Stores Docker image and queue info

5. **New: VulnerabilityDefinition Model**
   - Master catalog of vulnerability types
   - Prevents data redundancy
   - Stores description and recommendations

6. **New: ScanSchedule Model**
   - Recurring scan configurations
   - Links to users and targets

7. **Report Model**
   - Links to UUID `job_id`
   - Stores file_path instead of content
   - Includes format field

## Workflow Changes

### Old Workflow
1. User submits scan with URL
2. Job created with target_url
3. Tools run, results stored in JobResult
4. Results displayed by stage

### New Workflow
1. User creates Target
2. User submits scan with target_id
3. Job created with UUID job_id
4. Tools run, findings created
5. Findings linked to VulnerabilityDefinitions
6. Findings displayed with severity, status, recommendations

## Benefits

1. **Data Normalization**: Vulnerability definitions stored once, referenced many times
2. **Better Tracking**: Individual findings with lifecycle tracking
3. **Scalability**: UUID job_ids prevent collisions
4. **Flexibility**: Targets can be reused, scheduled, prioritized
5. **Remediation Workflow**: Findings can be assigned, acknowledged, resolved
6. **Reporting**: Better structured data for reports

## Migration Required

See `DATABASE_MIGRATION.md` for detailed migration steps.

## Testing Checklist

- [ ] User registration and login
- [ ] Target creation
- [ ] Scan job creation with target_id
- [ ] Tool execution and finding creation
- [ ] Vulnerability definition creation/retrieval
- [ ] Finding status updates
- [ ] Report generation
- [ ] UUID handling in all endpoints
- [ ] Foreign key relationships
- [ ] Cascade deletes

## Next Steps

1. Update frontend to work with new API
2. Add target management UI
3. Update scan creation to use targets
4. Display findings instead of stage results
5. Add finding status management
6. Add vulnerability definition management (admin)

