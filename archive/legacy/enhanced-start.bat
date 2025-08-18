@echo off
REM ============================================
REM     DocXP Production-Ready Startup Script
REM ============================================

setlocal enabledelayedexpansion
cls

echo ================================================
echo           DocXP Application Launcher
echo       AI-Powered Documentation Platform
echo ================================================
echo.

REM Set window title
title DocXP - Starting Services

REM ===== STEP 1: Environment Checks =====
echo [1/6] Checking system requirements...
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo   X ERROR: Python is not installed or not in PATH
    echo.
    echo   Please install Python 3.10 or higher from:
    echo   https://www.python.org/downloads/
    echo.
    pause
    exit /b 1
)
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo   + Python %PYTHON_VERSION% found

REM Check Node.js
node --version >nul 2>&1
if errorlevel 1 (
    echo   X ERROR: Node.js is not installed or not in PATH
    echo.
    echo   Please install Node.js 18 or higher from:
    echo   https://nodejs.org/
    echo.
    pause
    exit /b 1
)
for /f %%i in ('node --version') do set NODE_VERSION=%%i
echo   + Node.js %NODE_VERSION% found

REM Check npm
npm --version >nul 2>&1
if errorlevel 1 (
    echo   X ERROR: npm is not installed
    pause
    exit /b 1
)
echo   + npm found

echo.
echo [2/6] Setting up backend environment...
cd backend

REM Create virtual environment if it doesn't exist
if not exist venv (
    echo   Creating Python virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo   X ERROR: Failed to create virtual environment
        pause
        exit /b 1
    )
)

REM Activate virtual environment
echo   Activating virtual environment...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo   X ERROR: Failed to activate virtual environment
    pause
    exit /b 1
)

REM Install/upgrade pip silently
python -m pip install --upgrade pip >nul 2>&1

REM Install requirements
echo   Installing Python dependencies...
pip install -q -r requirements.txt
if errorlevel 1 (
    echo   X ERROR: Failed to install Python dependencies
    echo   Check requirements.txt and your internet connection
    pause
    exit /b 1
)

echo.
echo [3/6] Running environment validation...
python startup_check.py
if errorlevel 1 (
    echo.
    echo   X Environment validation failed!
    echo   Please fix the issues above and try again.
    echo.
    pause
    exit /b 1
)

REM Check if validation marker exists
if not exist .validated (
    echo   X ERROR: Validation marker not found
    echo   The environment check may have failed silently
    pause
    exit /b 1
)

echo.
echo [4/6] Initializing database...
python -c "from app.core.database import init_db; import asyncio; asyncio.run(init_db())" 2>nul
if errorlevel 1 (
    echo   ! Warning: Database initialization had issues
    echo   Attempting to continue...
)

REM Create required directories
if not exist output mkdir output
if not exist temp mkdir temp
if not exist logs mkdir logs
if not exist configs mkdir configs

echo.
echo [5/6] Starting backend server...
REM Kill any existing backend process on port 8001
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8001') do (
    taskkill /F /PID %%a >nul 2>&1
)

REM Start backend in background
start /B /MIN cmd /c "python main.py > logs\backend_startup.log 2>&1"

REM Wait for backend to be ready
echo   Waiting for backend to initialize...
set BACKEND_READY=0
for /L %%i in (1,1,30) do (
    if !BACKEND_READY!==0 (
        timeout /t 1 /nobreak >nul
        curl -s http://localhost:8001/health >nul 2>&1
        if not errorlevel 1 (
            set BACKEND_READY=1
            echo   + Backend API is ready!
        ) else (
            echo   . Waiting... [%%i/30]
        )
    )
)

if !BACKEND_READY!==0 (
    echo   X ERROR: Backend failed to start after 30 seconds
    echo   Check logs\backend_startup.log for details
    pause
    exit /b 1
)

echo.
echo [6/6] Starting frontend application...
cd ..\frontend

REM Install Node dependencies if needed
if not exist node_modules (
    echo   Installing frontend dependencies...
    call npm install --silent
    if errorlevel 1 (
        echo   X ERROR: Failed to install frontend dependencies
        pause
        exit /b 1
    )
) else (
    echo   Frontend dependencies already installed
)

REM Kill any existing frontend process on port 4200
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :4200') do (
    taskkill /F /PID %%a >nul 2>&1
)

REM Start frontend in background
echo   Starting Angular development server...
start /B /MIN cmd /c "npm start > ..\backend\logs\frontend_startup.log 2>&1"

REM Wait for frontend to be ready
echo   Waiting for frontend to compile...
set FRONTEND_READY=0
for /L %%i in (1,1,60) do (
    if !FRONTEND_READY!==0 (
        timeout /t 2 /nobreak >nul
        curl -s http://localhost:4200 >nul 2>&1
        if not errorlevel 1 (
            set FRONTEND_READY=1
            echo   + Frontend is ready!
        ) else (
            echo   . Compiling... [%%i/60]
        )
    )
)

if !FRONTEND_READY!==0 (
    echo   X ERROR: Frontend failed to start after 2 minutes
    echo   Check logs\frontend_startup.log for details
    pause
    exit /b 1
)

echo.
echo ================================================
echo        DocXP Started Successfully!
echo ================================================
echo.
echo   Dashboard:    http://localhost:4200
echo   API Backend:  http://localhost:8001
echo   API Docs:     http://localhost:8001/docs
echo   Health Check: http://localhost:8001/health/detailed
echo.
echo   Logs Location: backend\logs\
echo.
echo   Press Ctrl+C in this window to stop all services
echo ================================================
echo.

REM Open browser after a short delay
timeout /t 2 /nobreak >nul
start http://localhost:4200

REM Keep the script running and monitor services
echo Monitoring services (Press Ctrl+C to stop)...
echo.

:MONITOR_LOOP
timeout /t 30 /nobreak >nul

REM Check if backend is still running
curl -s http://localhost:8001/health >nul 2>&1
if errorlevel 1 (
    echo.
    echo ! WARNING: Backend service appears to be down
    echo Attempting to restart...
    cd ..\backend
    start /B /MIN cmd /c "python main.py >> logs\backend_restart.log 2>&1"
    cd ..\frontend
)

REM Check if frontend is still running
curl -s http://localhost:4200 >nul 2>&1
if errorlevel 1 (
    echo.
    echo ! WARNING: Frontend service appears to be down
    echo Attempting to restart...
    start /B /MIN cmd /c "npm start >> ..\backend\logs\frontend_restart.log 2>&1"
)

goto MONITOR_LOOP

:CLEANUP
echo.
echo Shutting down DocXP services...
REM Kill processes
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8001') do (
    taskkill /F /PID %%a >nul 2>&1
)
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :4200') do (
    taskkill /F /PID %%a >nul 2>&1
)
echo Services stopped.
exit /b 0
