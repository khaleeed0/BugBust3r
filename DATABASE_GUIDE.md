# Database Guide - Security Scanner Project

## Overview

This project uses **PostgreSQL 15** as the primary database, running in a Docker container. The database stores all application data including users, scan targets, scan jobs, findings, and reports.

---

## Database Technology

- **Database**: PostgreSQL 15 (Alpine Linux)
- **Container Name**: `security_scanner_db`
- **Port Mapping**: `5433:5432` (host:container)
  - **Note**: Port 5433 is used on the host because port 5432 may be in use by a local PostgreSQL installation
- **Database Name**: `security_scanner`
- **Username**: `postgres`
- **Password**: `postgres` (change in production!)

---

## Database Schema

The database contains **8 main tables**:

### 1. **users**
Stores user account information
- `id` (SERIAL PRIMARY KEY)
- `username` (VARCHAR, UNIQUE)
- `email` (VARCHAR, UNIQUE)
- `password_hash` (VARCHAR) - bcrypt hashed passwords
- `role` (VARCHAR) - user roles (default: 'user')
- `created_at` (TIMESTAMP)
- `api_key` (VARCHAR, UNIQUE, optional)

### 2. **targets**
Contains the assets/URLs to be scanned
- `id` (SERIAL PRIMARY KEY)
- `user_id` (INTEGER, FK → users.id)
- `url` (VARCHAR, UNIQUE) - The target URL to scan
- `name` (VARCHAR) - Display name
- `created_at` (TIMESTAMP)
- `description` (TEXT)
- `asset_value` (VARCHAR) - 'critical', 'high', 'low'

### 3. **tools**
Registry of available security scanning tools
- `id` (SERIAL PRIMARY KEY)
- `name` (VARCHAR, UNIQUE) - Tool identifier (e.g., 'zap', 'nuclei')
- `display_name` (VARCHAR) - Human-readable name
- `docker_image` (VARCHAR) - Docker image name
- `celery_queue` (VARCHAR) - Queue name for task processing
- `is_enabled` (BOOLEAN)
- `description` (TEXT)
- `category` (VARCHAR) - Tool category

### 4. **scan_jobs**
Log of every scan execution
- `id` (SERIAL PRIMARY KEY)
- `job_id` (UUID, UNIQUE) - Unique job identifier
- `user_id` (INTEGER, FK → users.id)
- `target_id` (INTEGER, FK → targets.id)
- `status` (VARCHAR) - 'pending', 'running', 'completed', 'failed'
- `created_at` (TIMESTAMP)
- `completed_at` (TIMESTAMP)

### 5. **scan_schedules**
Configurations for recurring automated scans
- `id` (SERIAL PRIMARY KEY)
- `user_id` (INTEGER, FK → users.id)
- `target_id` (INTEGER, FK → targets.id)
- `schedule_type` (VARCHAR) - 'weekly', 'daily', etc.
- `is_active` (BOOLEAN)
- `next_scan_at` (TIMESTAMP)

### 6. **vulnerability_definitions**
Master catalog of vulnerability types
- `id` (SERIAL PRIMARY KEY)
- `name` (VARCHAR, UNIQUE) - Vulnerability name
- `description` (TEXT)
- `recommendation` (TEXT) - How to fix

### 7. **findings**
Specific instances of discovered vulnerabilities
- `id` (SERIAL PRIMARY KEY)
- `job_id` (UUID, FK → scan_jobs.job_id)
- `tool_id` (INTEGER, FK → tools.id)
- `definition_id` (INTEGER, FK → vulnerability_definitions.id)
- `target_id` (INTEGER, FK → targets.id)
- `severity` (VARCHAR) - 'critical', 'high', 'medium', 'low', 'info'
- `status` (VARCHAR) - 'new', 'reopened', 'acknowledged', 'resolved', 'false_positive'
- `first_seen_at` (TIMESTAMP)
- `last_seen_at` (TIMESTAMP)
- `location` (TEXT) - Where the vulnerability was found
- `evidence` (TEXT) - Proof/evidence of the vulnerability
- `confidence` (VARCHAR) - 'high', 'medium', 'low'
- `assigned_to_user_id` (INTEGER, FK → users.id)

### 8. **reports**
Metadata about generated scan reports
- `id` (SERIAL PRIMARY KEY)
- `job_id` (UUID, FK → scan_jobs.job_id)
- `format` (VARCHAR) - Report format (e.g., 'html', 'json', 'pdf')
- `file_path` (VARCHAR) - Path to report file
- `generated_at` (TIMESTAMP)

---

## How to Run the Database

### Option 1: Using Docker Compose (Recommended)

The database is automatically started with Docker Compose:

```bash
# Start only database and Redis
docker-compose up -d db redis

# Or start all services (database, Redis, backend, frontend)
docker-compose up -d
```

**Check Status:**

```bash
docker-compose ps
```

**View Logs:**
```bash
docker-compose logs db
```

### Option 2: Manual Docker Run

```bash
docker run -d \
  --name security_scanner_db \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=security_scanner \
  -p 5433:5432 \
  -v postgres_data:/var/lib/postgresql/data \
  postgres:15-alpine
```

### Option 3: Local PostgreSQL (Not Recommended)

If you have PostgreSQL installed locally, you can connect to it, but you'll need to:
1. Create the database: `CREATE DATABASE security_scanner;`
2. Update the connection string in `backend/.env`
3. Run migrations manually

---

## Connection Details

### From Host Machine (Local Development)

```bash
# Connection String
postgresql://postgres:postgres@localhost:5433/security_scanner

# Using psql command
psql -h localhost -p 5433 -U postgres -d security_scanner
```

### From Docker Containers

```bash
# Connection String (from backend container)
postgresql://postgres:postgres@db:5432/security_scanner

# Note: Uses service name 'db' and internal port 5432
```

### Environment Variables

The backend reads the connection string from:
- **File**: `backend/.env`
- **Variable**: `DATABASE_URL`
- **Default**: `postgresql://postgres:postgres@localhost:5432/security_scanner`

---

## Database Initialization

### Automatic Initialization

The database tables are **automatically created** when the backend starts. The `main.py` file includes:

```python
# Enable UUID extension
conn.execute(text('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"'))

# Create all tables
Base.metadata.create_all(bind=engine)
```

### Manual Initialization

If you need to manually initialize:

```bash
# Option 1: Using Python script
cd backend
python app/db/init_db.py

# Option 2: Using SQL file
docker exec -i security_scanner_db psql -U postgres -d security_scanner < backend/app/db/schema.sql
```

---

## Common Database Operations

### Connect to Database

```bash
# Using Docker exec
docker exec -it security_scanner_db psql -U postgres -d security_scanner

# Using psql from host (if installed)
psql -h localhost -p 5433 -U postgres -d security_scanner
```

### View All Tables

```sql
\dt
```

### View Table Structure

```sql
\d users
\d targets
\d scan_jobs
```

### Query Examples

```sql
-- Count users
SELECT COUNT(*) FROM users;

-- View all scan jobs
SELECT * FROM scan_jobs ORDER BY created_at DESC LIMIT 10;

-- View findings by severity
SELECT severity, COUNT(*) FROM findings GROUP BY severity;

-- View targets for a user
SELECT * FROM targets WHERE user_id = 1;
```

### Backup Database

```bash
# Create backup
docker exec security_scanner_db pg_dump -U postgres security_scanner > backup.sql

# Restore backup
docker exec -i security_scanner_db psql -U postgres security_scanner < backup.sql
```

### Reset Database (⚠️ Deletes All Data)

```bash
# Stop and remove container
docker-compose down -v

# Start fresh
docker-compose up -d db
```

---

## Database Management

### Check Database Status

```bash
# Check if container is running
docker ps | grep security_scanner_db

# Check health
docker inspect security_scanner_db | grep -A 5 Health

# Check logs
docker logs security_scanner_db
```

### View Database Size

```sql
SELECT pg_size_pretty(pg_database_size('security_scanner'));
```

### View Table Sizes

```sql
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

---

## Troubleshooting

### Database Won't Start

```bash
# Check if port 5433 is available
lsof -i:5433

# Check Docker logs
docker logs security_scanner_db

# Remove and recreate
docker-compose down -v
docker-compose up -d db
```

### Connection Refused

1. **Check if database is running:**
   ```bash
   docker ps | grep security_scanner_db
   ```

2. **Check connection string in backend/.env:**
   ```bash
   cat backend/.env | grep DATABASE_URL
   ```
   Should be: `DATABASE_URL=postgresql://postgres:postgres@localhost:5433/security_scanner`

3. **Test connection:**
   ```bash
   docker exec security_scanner_db psql -U postgres -d security_scanner -c "SELECT 1;"
   ```

### Tables Not Created

```bash
# Manually run initialization
cd backend
python app/db/init_db.py

# Or restart backend (tables auto-create on startup)
docker-compose restart backend
```

### Permission Errors

```bash
# Check database permissions
docker exec security_scanner_db psql -U postgres -d security_scanner -c "\du"

# Reset password if needed
docker exec security_scanner_db psql -U postgres -c "ALTER USER postgres WITH PASSWORD 'postgres';"
```

---

## Production Considerations

⚠️ **Important for Production:**

1. **Change Default Password:**
   ```bash
   # Update docker-compose.yml
   POSTGRES_PASSWORD: your-secure-password
   
   # Update backend/.env
   DATABASE_URL=postgresql://postgres:your-secure-password@localhost:5433/security_scanner
   ```

2. **Use Environment Variables:**
   - Don't hardcode passwords
   - Use secrets management

3. **Enable SSL:**
   - Configure SSL connections for production
   - Update connection string with SSL parameters

4. **Regular Backups:**
   - Set up automated backups
   - Test restore procedures

5. **Monitoring:**
   - Monitor database performance
   - Set up alerts for disk space, connections, etc.

---

## Summary

- **Database**: PostgreSQL 15 (Docker container)
- **Port**: 5433 (host) → 5432 (container)
- **Auto-initialization**: Yes (on backend startup)
- **Connection**: `postgresql://postgres:postgres@localhost:5433/security_scanner`
- **Tables**: 8 tables (users, targets, tools, scan_jobs, scan_schedules, vulnerability_definitions, findings, reports)

The database is ready to use once you run `docker-compose up -d db`!

