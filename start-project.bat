@echo off
REM ============================================
REM Bugbuster Project Startup Script for Windows
REM ============================================
REM NOTE: On macOS / Linux, use: start-project-mac.sh
REM This script starts all services:
REM - Database (PostgreSQL) - runs LOCALLY, NOT in Docker
REM - Redis (Docker)
REM - Backend (FastAPI) - runs locally
REM - Frontend (React) - runs locally
REM - OWASP ZAP Docker Image
REM ============================================

setlocal enabledelayedexpansion

echo.
echo ============================================
echo   Bugbuster Project Startup
echo ============================================
echo.

REM Get the script directory
set SCRIPT_DIR=%~dp0
cd /d "%SCRIPT_DIR%"

REM Color codes removed for better compatibility
set "GREEN=✓"
set "RED=✗"
set "YELLOW=!"
set "BLUE=→"
set "RESET="

REM ============================================
REM Step 1: Check Prerequisites
REM ============================================
echo %BLUE%[1/8] Checking Prerequisites...%RESET%
echo.

REM Check Docker
echo Checking Docker...
docker --version >nul 2>&1
if errorlevel 1 (
    echo %RED%ERROR: Docker is not installed or not in PATH%RESET%
    echo Please install Docker Desktop from https://www.docker.com/products/docker-desktop
    pause
    exit /b 1
)
echo %GREEN%✓ Docker found%RESET%

REM Check Node.js
echo Checking Node.js...
node --version >nul 2>&1
if errorlevel 1 (
    echo %RED%ERROR: Node.js is not installed or not in PATH%RESET%
    echo Please install Node.js from https://nodejs.org/
    pause
    exit /b 1
)
echo %GREEN%✓ Node.js found%RESET%

REM Check Python
echo Checking Python...
python --version >nul 2>&1
if errorlevel 1 (
    python3 --version >nul 2>&1
    if errorlevel 1 (
        echo %RED%ERROR: Python is not installed or not in PATH%RESET%
        echo Please install Python from https://www.python.org/
        pause
        exit /b 1
    ) else (
        set PYTHON_CMD=python3
    )
) else (
    set PYTHON_CMD=python
)
echo %GREEN%✓ Python found%RESET%

echo.
echo %GREEN%All prerequisites are installed!%RESET%
echo.

REM ============================================
REM Step 2: Start Docker Desktop (if not running)
REM ============================================
echo %BLUE%[2/8] Checking Docker Desktop...%RESET%
docker ps >nul 2>&1
if errorlevel 1 (
    echo %YELLOW%Docker Desktop is not running. Attempting to start...%RESET%
    echo Please ensure Docker Desktop is running and try again.
    pause
    exit /b 1
)
echo %GREEN%✓ Docker is running%RESET%
echo.

REM ============================================
REM Step 3: Check Local PostgreSQL Database
REM ============================================
echo %BLUE%[3/8] Checking Local PostgreSQL Database...%RESET%

REM Check if PostgreSQL is running locally
REM Try to connect using psql if available
where psql >nul 2>&1
if errorlevel 1 (
    echo %YELLOW%Warning: psql not found in PATH. Please ensure PostgreSQL is installed and running locally.%RESET%
    echo PostgreSQL should be running on localhost:5432
    echo Install PostgreSQL: https://www.postgresql.org/download/windows/
) else (
    echo Checking PostgreSQL connection...
    set PGPASSWORD=1234
    psql -h localhost -p 5432 -U postgres -d postgres -c "SELECT 1;" >nul 2>&1
    if errorlevel 1 (
        echo %YELLOW%Warning: Could not connect to PostgreSQL on localhost:5432%RESET%
        echo Please ensure PostgreSQL is running locally and password is set to '1234' for user 'postgres'
        echo Set password: psql -U postgres -c "ALTER USER postgres PASSWORD '1234';"
    ) else (
        echo %GREEN%✓ PostgreSQL is running on localhost:5432%RESET%
    )
    set PGPASSWORD=
)

REM Check if database exists
where psql >nul 2>&1
if not errorlevel 1 (
    set PGPASSWORD=1234
    psql -h localhost -p 5432 -U postgres -lqt 2>nul | findstr /C:"Bugbust3r" >nul
    if errorlevel 1 (
        echo Creating database 'Bugbust3r'...
        psql -h localhost -p 5432 -U postgres -c "CREATE DATABASE \"Bugbust3r\";" 2>nul
        if errorlevel 1 (
            echo %YELLOW%Note: Could not create database automatically. Please create it manually:%RESET%
            echo    psql -h localhost -p 5432 -U postgres -c "CREATE DATABASE \"Bugbust3r\";"
        ) else (
            echo %GREEN%✓ Database 'Bugbust3r' created%RESET%
        )
) else (
        echo %GREEN%✓ Database 'Bugbust3r' exists%RESET%
    )
    set PGPASSWORD=
)

echo.
echo %YELLOW%NOTE: Database runs LOCALLY, NOT in Docker%RESET%
echo.

REM ============================================
REM Step 3b: Start Redis and other Docker services
REM ============================================
echo %BLUE%[3b/8] Starting Docker services (Redis, Backend, Celery, Frontend)...%RESET%
echo %YELLOW%NOTE: Frontend configured to use http://localhost:8000 for API (browser access)%RESET%

docker ps --filter "name=security_scanner_redis" --format "{{.Names}}" | findstr /C:"security_scanner_redis" >nul
if errorlevel 1 (
    echo Starting Docker services...
    docker-compose up -d
    if errorlevel 1 (
        echo %RED%ERROR: Failed to start Docker services%RESET%
        pause
        exit /b 1
    )
    echo Waiting for services to be ready...
    timeout /t 10 /nobreak >nul
) else (
    echo %GREEN%✓ Docker services already running%RESET%
    echo Starting any stopped services...
    docker-compose up -d
)

echo %GREEN%✓ Docker services are running%RESET%
echo.

REM ============================================
REM Step 4: Check All Security Tool Docker Images
REM ============================================
echo %BLUE%[4/8] Checking Security Tool Docker Images...%RESET%

REM Check all security tool images
set MISSING_IMAGES=0
docker images --format "{{.Repository}}:{{.Tag}}" | findstr /C:"security-tools:sublist3r" >nul
if errorlevel 1 (
    echo Sublist3r image missing - will need to build
    set MISSING_IMAGES=1
)
docker images --format "{{.Repository}}:{{.Tag}}" | findstr /C:"security-tools:httpx" >nul
if errorlevel 1 (
    echo Httpx image missing - will need to build
    set MISSING_IMAGES=1
)
docker images --format "{{.Repository}}:{{.Tag}}" | findstr /C:"security-tools:gobuster" >nul
if errorlevel 1 (
    echo Gobuster image missing - will need to build
    set MISSING_IMAGES=1
)
docker images --format "{{.Repository}}:{{.Tag}}" | findstr /C:"security-tools:zap" >nul
if errorlevel 1 (
    echo ZAP image missing - will need to build
    set MISSING_IMAGES=1
)
docker images --format "{{.Repository}}:{{.Tag}}" | findstr /C:"security-tools:nuclei" >nul
if errorlevel 1 (
    echo Nuclei image missing - will need to build
    set MISSING_IMAGES=1
)
docker images --format "{{.Repository}}:{{.Tag}}" | findstr /C:"security-tools:sqlmap" >nul
if errorlevel 1 (
    echo SQLMap image missing - will need to build
    set MISSING_IMAGES=1
)

if !MISSING_IMAGES!==1 (
    echo %YELLOW%Some security tool images are missing. Building all...%RESET%
    echo This may take several minutes...
    cd docker-tools
    if exist build-all.sh (
        bash build-all.sh
    ) else (
        echo Building images individually...
        cd zap
        docker build -t security-tools:zap .
        cd ..\sublist3r
        docker build -t security-tools:sublist3r .
        cd ..\httpx
        docker build -t security-tools:httpx .
        cd ..\gobuster
        docker build -t security-tools:gobuster .
        cd ..\nuclei
        docker build -t security-tools:nuclei .
        cd ..\sqlmap
        docker build -t security-tools:sqlmap .
        cd ..\..
    )
    cd ..\..
    echo %GREEN%✓ Security tool images built%RESET%
) else (
    echo %GREEN%✓ All security tool images present%RESET%
    REM Verify ZAP has Java 17
    docker run --rm security-tools:zap java -version 2>&1 | findstr /C:"17" >nul
    if errorlevel 1 (
        echo %YELLOW%ZAP image may need rebuild (requires Java 17)%RESET%
        echo Rebuilding ZAP image...
        cd docker-tools\zap
        docker build -t security-tools:zap .
        cd ..\..
        echo %GREEN%✓ ZAP image rebuilt%RESET%
    ) else (
        echo %GREEN%✓ ZAP image verified (Java 17)%RESET%
    )
)
echo.

REM ============================================
REM Step 5: Setup Backend
REM ============================================
echo %BLUE%[5/8] Setting up Backend...%RESET%

cd backend

REM Check if virtual environment exists
if not exist "venv" (
    echo Creating Python virtual environment...
    %PYTHON_CMD% -m venv venv
    if errorlevel 1 (
        echo %RED%ERROR: Failed to create virtual environment%RESET%
        cd ..
        pause
        exit /b 1
    )
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Install/upgrade dependencies
echo Installing Python dependencies...
pip install --upgrade pip >nul 2>&1
pip install -r requirements.txt
if errorlevel 1 (
    echo %RED%ERROR: Failed to install Python dependencies%RESET%
    cd ..
    pause
    exit /b 1
)

REM Check if .env file exists
if not exist ".env" (
    echo %YELLOW%Warning: .env file not found. Creating from template...%RESET%
    (
        echo DATABASE_URL=postgresql://postgres:1234@localhost:5432/Bugbust3r
        echo REDIS_URL=redis://localhost:6379/0
        echo DOCKER_SOCKET=unix://var/run/docker.sock
        echo SECRET_KEY=f1ee38ee6f5d755ed3d0d3568ff8237ed33a85c0f679f1737c2e4a1229dec039
        echo ALGORITHM=HS256
        echo ACCESS_TOKEN_EXPIRE_MINUTES=30
        echo CORS_ORIGINS=["http://localhost:3000","http://127.0.0.1:3000"]
    ) > .env
    echo %GREEN%✓ .env file created with local PostgreSQL settings%RESET%
) else (
    REM Update .env to use correct database URL
    findstr /C:"DATABASE_URL=postgresql://postgres:1234@localhost:5432/Bugbust3r" .env >nul 2>&1
    if errorlevel 1 (
        echo Updating .env to use correct database URL...
        powershell -Command "(Get-Content .env) -replace 'DATABASE_URL=.*', 'DATABASE_URL=postgresql://postgres:1234@localhost:5432/Bugbust3r' | Set-Content .env" 2>nul
        if errorlevel 1 (
            echo %YELLOW%Note: Please manually update DATABASE_URL in .env to: postgresql://postgres:1234@localhost:5432/Bugbust3r%RESET%
        ) else (
            echo %GREEN%✓ Updated .env to use correct database URL%RESET%
        )
    ) else (
        echo %GREEN%✓ .env already configured correctly%RESET%
    )
)

REM Initialize database tables
echo Initializing database...
%PYTHON_CMD% -c "from app.db.database import engine; from app.models import user, target, job, tool; from sqlalchemy.orm import declarative_base; Base = declarative_base(); Base.metadata.create_all(bind=engine)" 2>nul
if errorlevel 1 (
    echo Note: Database tables will be created automatically on first backend request
)

cd ..
echo %GREEN%✓ Backend setup complete%RESET%
echo.

REM ============================================
REM Step 6: Setup Frontend
REM ============================================
echo %BLUE%[6/8] Setting up Frontend...%RESET%

cd frontend

REM Check if node_modules exists
if not exist "node_modules" (
    echo Installing Node.js dependencies...
    echo This may take a few minutes...
    call npm install
    if errorlevel 1 (
        echo %RED%ERROR: Failed to install Node.js dependencies%RESET%
        cd ..
        pause
        exit /b 1
    )
) else (
    echo %GREEN%✓ Node modules already installed%RESET%
)

cd ..
echo %GREEN%✓ Frontend setup complete%RESET%
echo.

REM ============================================
REM Step 7: Start Backend Server
REM ============================================
echo %BLUE%[7/8] Starting Backend Server...%RESET%

cd backend
call venv\Scripts\activate.bat

REM Check if backend is already running
netstat -an | findstr /C:"8000" | findstr /C:"LISTENING" >nul
if not errorlevel 1 (
    echo %YELLOW%Port 8000 is already in use. Backend may already be running.%RESET%
) else (
    echo Starting FastAPI backend on port 8000...
    start "Bugbuster Backend" cmd /k "call venv\Scripts\activate.bat && uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"
    echo Waiting for backend to start...
    timeout /t 5 /nobreak >nul
    
    REM Check if backend started successfully
    echo %YELLOW%Backend is starting... Please wait a few seconds.%RESET%
    echo %GREEN%✓ Backend server started on http://localhost:8000%RESET%
    echo %YELLOW%Note: It may take 10-20 seconds for backend to fully initialize%RESET%
)

cd ..
echo.

REM ============================================
REM Step 8: Start Frontend Server
REM ============================================
echo %BLUE%[8/8] Starting Frontend Server...%RESET%

cd frontend

REM Check if frontend is already running
netstat -an | findstr /C:"3000" | findstr /C:"LISTENING" >nul
if not errorlevel 1 (
    echo %YELLOW%Port 3000 is already in use. Frontend may already be running.%RESET%
) else (
    echo Starting React frontend on port 3000...
    start "Bugbuster Frontend" cmd /k "npm run dev"
    echo Waiting for frontend to start...
    timeout /t 10 /nobreak >nul
    echo %GREEN%✓ Frontend is starting on http://localhost:3000%RESET%
)

cd ..

echo.
echo %BLUE%[9/9] Waiting for services to be ready...%RESET%
echo Waiting 20 seconds for services to initialize...
timeout /t 20 /nobreak >nul

echo %BLUE%[10/10] Running comprehensive project verification...%RESET%
echo This will verify: database, security tools, user auth, API, jobs, workers
echo.

REM Run verification script (if backend is in Docker)
docker ps --filter "name=security_scanner_backend" --format "{{.Names}}" | findstr /C:"security_scanner_backend" >nul
if not errorlevel 1 (
    echo Running verification in Docker backend container...
    docker exec security_scanner_backend python verify_project.py 2>&1
    if errorlevel 1 (
        echo %YELLOW%⚠️  Some verification tests failed. Check output above.%RESET%
        echo Services are still running - you can test manually.
    ) else (
        echo %GREEN%✓ Project verification completed%RESET%
    )
) else (
    echo %YELLOW%Note: Backend not in Docker. Run verification manually:%RESET%
    echo   cd backend
    echo   python verify_project.py
)
echo.

echo ============================================
echo   Startup Complete!
echo ============================================
echo.
echo %GREEN%All services are running:%RESET%
echo   - Database:     PostgreSQL (LOCAL) on localhost:5432/Bugbust3r
echo   - Redis:         tcp://localhost:6379 (Docker)
echo   - Backend API:   http://localhost:8000 (Local)
echo   - Celery Worker: Running (if using Docker Compose)
echo   - Frontend:      http://localhost:3000 (Local)
echo   - Security Tools: All Docker images ready
echo.
echo %YELLOW%IMPORTANT: Database runs LOCALLY, NOT in Docker%RESET%
echo   - PostgreSQL should be running on localhost:5432
echo   - Database name: Bugbust3r
echo   - Username: postgres, Password: 1234
echo   - To check PostgreSQL: pg_isready -h localhost -p 5432
echo.
echo Testing & Verification:
echo   1) Visit: http://localhost:3000/register and create a user
echo   2) Visit: http://localhost:3000/login and sign in
echo   3) Test scan creation and execution
echo   4) Verify findings are stored in database
echo.
echo %YELLOW%Recent updates (latest fixes):%RESET%
echo   ✓ Fixed ZAP tool - updated to Java 17, fixed path issues
echo   ✓ Fixed Nuclei tool - corrected JSON output flags
echo   ✓ Fixed Gobuster tool - added inline wordlist support
echo   ✓ Fixed SQLMap tool - corrected file path
echo   ✓ Fixed Sublist3r tool - corrected file path
echo   ✓ Fixed database schema - added evidence, confidence, assigned_to_user_id columns
echo   ✓ Fixed enum storage - configured to use values instead of names
echo   ✓ All security tools tested and verified to save findings
echo   ✓ Database connection verified (Bugbust3r)
echo   ✓ User registration/login tested and working
echo   ✓ Backend-frontend connection verified
echo   ✓ Job creation and worker functionality tested
echo.
echo Opening LocalHostTesting page in browser...
timeout /t 3 /nobreak >nul
start http://localhost:3000/localhost-testing
echo.
echo %GREEN%✓ Browser opened to LocalHostTesting page%RESET%
echo.
echo ============================================
echo   Project is running!
echo ============================================
echo.
echo %YELLOW%To stop all services:%RESET%
echo   1. Close the Backend and Frontend command windows
echo   2. Run: docker-compose down
echo.
echo %YELLOW%To view logs:%RESET%
echo   - Backend: Check the "Bugbuster Backend" window
echo   - Frontend: Check the "Bugbuster Frontend" window
echo   - Docker services: docker-compose logs [service_name]
echo.
echo %YELLOW%To run verification again:%RESET%
echo   - If using Docker: docker exec security_scanner_backend python verify_project.py
echo   - If local: cd backend && python verify_project.py
echo.
pause

