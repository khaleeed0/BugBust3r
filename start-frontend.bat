@echo off
REM Start only the BugBust3r frontend (React) at http://localhost:3000
cd /d "%~dp0frontend"

if not exist "node_modules" (
    echo Installing dependencies...
    call npm install
    if errorlevel 1 (
        echo Failed to install. Check Node.js is installed: node --version
        pause
        exit /b 1
    )
)

echo.
echo Starting BugBust3r frontend on http://localhost:3000
echo Keep this window open. Close the window to stop the frontend.
echo.

call npm run dev

pause
