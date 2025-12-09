@echo off
REM ============================================
REM Bugbuster Project Stop Script for Windows
REM ============================================

setlocal enabledelayedexpansion

echo.
echo ============================================
echo   Stopping Bugbuster Project
echo ============================================
echo.

REM Stop Docker containers
echo Stopping Docker containers...
docker-compose down

REM Kill processes on ports 8000 and 3000
echo Stopping services on ports 8000 and 3000...

REM Find and kill process on port 8000
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8000 ^| findstr LISTENING') do (
    echo Killing process %%a on port 8000...
    taskkill /F /PID %%a >nul 2>&1
)

REM Find and kill process on port 3000
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :3000 ^| findstr LISTENING') do (
    echo Killing process %%a on port 3000...
    taskkill /F /PID %%a >nul 2>&1
)

echo.
echo ============================================
echo   All services stopped!
echo ============================================
echo.
pause

