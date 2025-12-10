# Setup Guide

## Quick Start

### 1. Build Security Tool Images

First, build all security tool Docker images:

```bash
cd docker-tools
chmod +x build-all.sh
./build-all.sh
```

This will create the following images:
- `security-tools:sublist3r`
- `security-tools:httpx`
- `security-tools:gobuster`
- `security-tools:zap`
- `security-tools:nuclei`
- `security-tools:sqlmap`

### 2. Configure Environment

Create the environment file (`.env.example` exists in the backend directory):

```bash
# Create .env file from example (if .env.example exists)
cp backend/.env.example backend/.env

# Or create manually with these settings:
cat > backend/.env << EOF
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/security_scanner
REDIS_URL=redis://localhost:6379/0
DOCKER_SOCKET=unix://var/run/docker.sock
SECRET_KEY=$(openssl rand -hex 32)
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
CORS_ORIGINS=["http://localhost:3000","http://127.0.0.1:3000"]
EOF
```

**Important**: Update the `SECRET_KEY` in `backend/.env` with a secure random string for production use.

### 3. Start with Docker Compose

```bash
docker-compose up -d
```

This starts:
- PostgreSQL database (port 5432)
- Redis (port 6379)
- FastAPI backend (port 8000)
- Celery worker
- React frontend (port 3000)

### 4. Access the Application

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

### 5. Create an Account and Start Scanning

1. Navigate to http://localhost:3000/register
2. Create a new account
3. Login and navigate to the Dashboard
4. **Create a Target**: Enter the URL you want to scan and create a target
5. **Start a Scan**: Select the target and initiate a scan job
6. Monitor progress on the Scans page
7. View detailed reports on the Reports page

## Manual Setup (Development)

### Backend Setup

```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Start database and Redis
docker-compose up -d db redis

# Initialize database (tables are auto-created, but you can run this manually)
python -m app.db.init_db

# Or if running from backend directory:
python app/db/init_db.py

# Run backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# In another terminal, run Celery worker
celery -A app.services.task_queue.celery_app worker --loglevel=info --queues=scans
```

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

The frontend will be available at:
- **Local**: http://localhost:3000
- **Network**: http://0.0.0.0:3000 (when running in Docker)

**Note**: Make sure the backend API is running on port 8000, or set the `VITE_API_URL` environment variable:
```bash
# Set custom API URL (optional)
export VITE_API_URL=http://localhost:8000
npm run dev
```

**Troubleshooting Frontend**:
- If port 3000 is in use, Vite will automatically try the next available port
- If you see CORS errors, ensure the backend CORS settings include your frontend URL
- Clear browser cache if you see stale content: `Ctrl+Shift+R` (Windows/Linux) or `Cmd+Shift+R` (Mac)

## Troubleshooting

### Docker Permission Issues

If you get Docker permission errors:

```bash
sudo usermod -aG docker $USER
newgrp docker
```

### Database Connection Errors

Ensure PostgreSQL is running:
```bash
docker-compose ps
```

Check database logs:
```bash
docker-compose logs db
```

### Security Tool Images Not Found

Make sure you've built all security tool images before running scans. This is a **required step**.

Check available images:
```bash
docker images | grep security-tools
```

If images are missing, build them:
```bash
cd docker-tools
chmod +x build-all.sh
./build-all.sh
```

Note: Building all images may take 10-30 minutes depending on your internet connection and system.

### Celery Worker Not Processing

Check Redis connection:
```bash
docker-compose logs redis
```

Check Celery worker logs:
```bash
docker-compose logs celery_worker
```

If worker isn't starting, ensure:
- Redis is running and accessible
- Database is initialized
- All dependencies are installed

### Database Tables Not Created

Tables are auto-created on backend startup. If they're missing:

```bash
# Option 1: Restart backend service
docker-compose restart backend

# Option 2: Manual initialization
docker-compose exec backend python app/db/init_db.py
```

Check if tables exist:
```bash
docker-compose exec db psql -U postgres -d security_scanner -c "\dt"
```

## Testing the Setup

1. **Test Backend API**:
   ```bash
   curl http://localhost:8000/health
   ```
   Expected response: `{"status":"healthy"}`

2. **Test Authentication**:
   ```bash
   curl -X POST http://localhost:8000/api/v1/auth/register \
     -H "Content-Type: application/json" \
     -d '{"email":"test@example.com","username":"testuser","password":"testpass123"}'
   ```
   Expected response: User object with id, email, username, role

3. **Test Login**:
   ```bash
   curl -X POST http://localhost:8000/api/v1/auth/login \
     -H "Content-Type: application/x-www-form-urlencoded" \
     -d "username=testuser&password=testpass123"
   ```
   Expected response: `{"access_token":"...","token_type":"bearer"}`

4. **Test Target Creation** (requires authentication token):
   ```bash
   TOKEN="your-access-token-here"
   curl -X POST http://localhost:8000/api/v1/targets \
     -H "Authorization: Bearer $TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"url":"https://example.com","name":"Example Site","asset_value":"high"}'
   ```

5. **Test Scan Creation** (requires target_id from previous step):
   ```bash
   curl -X POST http://localhost:8000/api/v1/scans \
     -H "Authorization: Bearer $TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"target_id":1}'
   ```

6. **Test Frontend**:
   Open http://localhost:3000 in your browser

## Production Deployment

For production:

1. Change `SECRET_KEY` to a secure random string
2. Use environment variables for all sensitive data
3. Enable HTTPS
4. Set up proper logging
5. Configure rate limiting
6. Use production-grade database backups
7. Monitor container resources

## Important Notes

### Workflow Changes
- **Targets First**: You must create a target before starting a scan. The new schema requires `target_id` instead of passing URLs directly.
- **UUID Job IDs**: Scan jobs now use UUID `job_id` instead of integer IDs for better scalability.

### Requirements
- The backend requires Docker socket access (`/var/run/docker.sock`)
- Docker must be running and accessible before starting scans
- Security tool images must be built before running scans
- Security scans can take significant time to complete (each stage runs sequentially)
- Large scans may consume considerable system resources
- Ensure adequate disk space for scan results

### Database
- Database tables are automatically created on startup via `main.py`
- UUID extension is automatically enabled
- Manual initialization via `app/db/init_db.py` is optional but recommended for production
- See `DATABASE_MIGRATION.md` if migrating from an older schema


