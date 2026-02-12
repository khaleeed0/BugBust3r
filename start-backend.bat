@echo off
REM Start only Redis + Backend so the API is reachable at http://localhost:8000
setlocal
cd /d "%~dp0"

echo.
echo Starting BugBust3r API (Redis + Backend)...
echo.

docker-compose up -d redis backend
if errorlevel 1 (
    echo ERROR: docker-compose failed. Is Docker Desktop running?
    pause
    exit /b 1
)

echo Waiting 15 seconds for backend to start...
timeout /t 15 /nobreak >nul 2>&1

echo.
echo Opening http://localhost:8000/health in your browser.
echo If you see {"status":"healthy"} the API is running.
echo If the page does not load, the backend may have failed (check Docker Desktop).
echo.
start "" "http://localhost:8000/health"
pause
