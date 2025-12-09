# Registration Error Troubleshooting Guide

## Problem
Registration endpoint returns an error and doesn't connect to the database.

## Diagnosis Steps

### 1. Check Database Status

```bash
# Check if database container is running
docker ps | grep security_scanner_db

# Test database connection
docker exec security_scanner_db psql -U postgres -d security_scanner -c "SELECT 1;"
```

**Expected**: Database should be running and accessible.

### 2. Check Database Connection String

```bash
# Check .env file
cat backend/.env | grep DATABASE_URL

# Should be:
# DATABASE_URL=postgresql://postgres:postgres@localhost:5433/security_scanner
```

**Note**: Port is **5433** (not 5432) because local PostgreSQL may be using 5432.

### 3. Verify Database Tables Exist

```bash
# Check if users table exists
docker exec security_scanner_db psql -U postgres -d security_scanner -c "\d users"
```

**Expected**: Should show the users table structure.

### 4. Test Database Connection from Backend

```bash
cd backend
source venv/bin/activate
python3 -c "
from app.db.database import engine
from sqlalchemy import text
try:
    with engine.connect() as conn:
        conn.execute(text('SELECT 1'))
        print('✅ Database connection successful!')
except Exception as e:
    print(f'❌ Connection failed: {e}')
"
```

### 5. Check Backend Logs

```bash
# If running with uvicorn, check terminal output
# Look for errors like:
# - "Could not connect to database"
# - "relation users does not exist"
# - Connection timeout errors
```

## Common Issues and Solutions

### Issue 1: Database Not Running

**Symptoms**: Connection refused errors

**Solution**:
```bash
# Start database
docker-compose up -d db

# Wait for it to be healthy
docker ps | grep security_scanner_db
```

### Issue 2: Wrong Port in Connection String

**Symptoms**: Connection timeout or refused

**Solution**:
```bash
# Check current port
docker ps | grep security_scanner_db

# Update backend/.env
# Should be port 5433 (not 5432)
DATABASE_URL=postgresql://postgres:postgres@localhost:5433/security_scanner
```

### Issue 3: Tables Don't Exist

**Symptoms**: "relation users does not exist"

**Solution**:
```bash
# Manually create tables
cd backend
source venv/bin/activate
python app/db/init_db.py

# Or restart backend (auto-creates tables)
# The backend auto-creates tables on startup
```

### Issue 4: Database Connection Pool Exhausted

**Symptoms**: "too many connections" errors

**Solution**:
```bash
# Restart database
docker-compose restart db

# Or restart backend
# (if running in terminal, Ctrl+C and restart)
```

### Issue 5: Backend Not Reading .env File

**Symptoms**: Using default connection string (wrong port)

**Solution**:
```bash
# Verify .env file exists
ls -la backend/.env

# Check if it's being read
cd backend
source venv/bin/activate
python3 -c "from app.core.config import settings; print(settings.DATABASE_URL)"
```

## Testing Registration

### Via API (cURL)

```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "username": "testuser",
    "password": "testpass123"
  }'
```

### Expected Success Response

```json
{
  "id": 1,
  "email": "test@example.com",
  "username": "testuser",
  "role": "user"
}
```

### Common Error Responses

**400 Bad Request**:
```json
{
  "detail": "Email already registered"
}
```
or
```json
{
  "detail": "Username already taken"
}
```

**500 Internal Server Error**:
```json
{
  "detail": "Registration failed: <error message>"
}
```

## Quick Fix Checklist

1. ✅ Database container running: `docker ps | grep security_scanner_db`
2. ✅ Database accessible: `docker exec security_scanner_db psql -U postgres -d security_scanner -c "SELECT 1;"`
3. ✅ Tables exist: `docker exec security_scanner_db psql -U postgres -d security_scanner -c "\dt"`
4. ✅ .env file correct: `cat backend/.env | grep DATABASE_URL`
5. ✅ Backend running: `curl http://localhost:8000/health`
6. ✅ Connection string correct: Port 5433 (not 5432)

## Debugging Commands

```bash
# 1. Check database status
docker ps | grep security_scanner_db

# 2. Check database logs
docker logs security_scanner_db

# 3. Test connection
docker exec security_scanner_db psql -U postgres -d security_scanner -c "SELECT COUNT(*) FROM users;"

# 4. Check backend connection
cd backend
source venv/bin/activate
python3 -c "from app.db.database import engine; from sqlalchemy import text; engine.connect().execute(text('SELECT 1'))"

# 5. View backend logs (if running in terminal)
# Look for database connection messages
```

## If Still Not Working

1. **Restart everything**:
   ```bash
   docker-compose down
   docker-compose up -d db redis
   # Wait 10 seconds
   # Then start backend manually or via docker-compose
   ```

2. **Check backend terminal output** for detailed error messages

3. **Verify database is accessible from host**:
   ```bash
   psql -h localhost -p 5433 -U postgres -d security_scanner
   # Password: postgres
   ```

4. **Check for port conflicts**:
   ```bash
   lsof -i:5433
   ```

## Current Status

Based on testing:
- ✅ Database is running
- ✅ Database is accessible
- ✅ Users table exists
- ✅ Connection string is correct (port 5433)
- ✅ Backend can connect to database

**If registration still fails**, the error should now be more descriptive with the improved error handling. Check the backend logs for the specific error message.

