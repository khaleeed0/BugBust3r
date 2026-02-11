# Windows Startup Guide

## Quick Start

### Option 1: Automated Startup (Recommended)

Simply double-click `start-project.bat` to start all services automatically.

### Option 2: Manual Startup

Follow the steps below if you prefer manual control.

## Prerequisites

Before running the startup script, ensure you have:

1. **Docker Desktop** - [Download](https://www.docker.com/products/docker-desktop)
   - Must be running before starting the project
   - Enable WSL 2 backend (recommended)

2. **Node.js** (v16 or higher) - [Download](https://nodejs.org/)
   - Required for frontend

3. **Python** (v3.8 or higher) - [Download](https://www.python.org/)
   - Required for backend
   - Check "Add Python to PATH" during installation

## What the Startup Script Does

The `start-project.bat` script automatically:

1. ✅ Checks for Docker, Node.js, and Python
2. ✅ Starts PostgreSQL database (port 5433)
3. ✅ Starts Redis (port 6379)
4. ✅ Builds OWASP ZAP Docker image (if not exists)
5. ✅ Sets up Python virtual environment
6. ✅ Installs backend dependencies
7. ✅ Creates `.env` file (if missing)
8. ✅ Initializes database tables
9. ✅ Installs frontend dependencies
10. ✅ Starts backend server (port 8000)
11. ✅ Starts frontend server (port 3000)
12. ✅ Opens LocalHostTesting page in browser

## Services

After startup, the following services will be running:

| Service | URL | Description |
|--------|-----|-------------|
| Frontend | http://localhost:3000 | React application |
| Backend API | http://localhost:8000 | FastAPI backend |
| Database | localhost:5433 | PostgreSQL database |
| Redis | localhost:6379 | Redis cache |
| OWASP ZAP | Docker image | Security scanning tool |
| AddressSanitizer | Docker image | C/C++ memory safety (LocalHost Testing) |
| Ghauri | Docker image | SQL injection (LocalHost Testing) |

## Usage

### Starting the Project

```batch
start-project.bat
```

Or double-click the file in Windows Explorer.

### Stopping the Project

```batch
stop-project.bat
```

Or manually:
1. Close the Backend and Frontend command windows
2. Run: `docker-compose down`

## Troubleshooting

### Docker Not Running

**Error**: `Docker is not installed or not in PATH`

**Solution**:
1. Install Docker Desktop
2. Start Docker Desktop
3. Wait for it to fully start (whale icon in system tray)
4. Run the script again

### Port Already in Use

**Error**: `Port 8000/3000 is already in use`

**Solution**:
1. Run `stop-project.bat` to stop existing services
2. Or manually kill processes:
   ```batch
   netstat -ano | findstr :8000
   taskkill /PID <PID> /F
   ```

### Python Virtual Environment Issues

**Error**: `Failed to create virtual environment`

**Solution**:
1. Ensure Python is installed and in PATH
2. Try: `python --version` or `python3 --version`
3. Delete `backend\venv` folder and run script again

### Node Modules Issues

**Error**: `Failed to install Node.js dependencies`

**Solution**:
1. Delete `frontend\node_modules` folder
2. Delete `frontend\package-lock.json`
3. Run script again

### Database Connection Issues

**Error**: `Could not connect to database`

**Solution**:
1. Ensure Docker containers are running: `docker ps`
2. Check database is healthy: `docker logs security_scanner_db`
3. Verify port 5433 is not in use
4. Restart database: `docker-compose restart db`

### OWASP ZAP Build Fails

**Error**: `Failed to build OWASP ZAP image`

**Solution**:
1. Ensure Docker has enough resources (4GB+ RAM)
2. Check internet connection (downloads ZAP)
3. Try building manually:
   ```batch
   cd docker-tools\zap
   docker build -t security-tools:zap .
   ```

## Manual Steps (If Script Fails)

### 1. Start Database and Redis

```batch
docker-compose up -d db redis
```

### 2. Build OWASP ZAP Image

```batch
cd docker-tools\zap
docker build -t security-tools:zap .
cd ..\..
```

### 3. Setup Backend

```batch
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

Create `.env` file:
```
DATABASE_URL=postgresql://postgres:postgres@localhost:5433/security_scanner
REDIS_URL=redis://localhost:6379/0
DOCKER_SOCKET=unix://var/run/docker.sock
SECRET_KEY=f1ee38ee6f5d755ed3d0d3568ff8237ed33a85c0f679f1737c2e4a1229dec039
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
CORS_ORIGINS=["http://localhost:3000","http://127.0.0.1:3000"]
```

Start backend:
```batch
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 4. Setup Frontend

```batch
cd frontend
npm install
npm run dev
```

### 5. Open LocalHostTesting

Navigate to: http://localhost:3000/localhost-testing

## Verifying Services

### Check Backend

```batch
curl http://localhost:8000/health
```

Should return: `{"status":"healthy"}`

### Check Frontend

Open browser: http://localhost:3000

### Check Database

```batch
docker exec security_scanner_db psql -U postgres -d security_scanner -c "SELECT 1;"
```

### Check Redis

```batch
docker exec security_scanner_redis redis-cli ping
```

Should return: `PONG`

## Command Windows

The startup script opens two command windows:

1. **Bugbuster Backend** - Shows backend logs
2. **Bugbuster Frontend** - Shows frontend logs

Keep these windows open while using the application.

## Next Steps

After startup:

1. **Register a user**: http://localhost:3000/register
2. **Login**: http://localhost:3000/login
3. **Run LocalHost Testing**: http://localhost:3000/localhost-testing
4. **View Dashboard**: http://localhost:3000/dashboard

## Support

If you encounter issues:

1. Check the troubleshooting section above
2. Review logs in the command windows
3. Check Docker logs: `docker logs security_scanner_db`
4. Verify all prerequisites are installed

## Notes

- First startup may take longer (downloading dependencies, building images)
- OWASP ZAP image build takes 5-10 minutes on first run
- Services may take 10-30 seconds to fully start
- Keep Docker Desktop running while using the project

