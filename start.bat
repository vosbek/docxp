@echo off
echo ===============================================
echo    DocXP - AI Documentation Platform
echo    Starting Development Environment
echo ===============================================
echo.

:: Check Python installation
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.10+ from https://www.python.org
    pause
    exit /b 1
)

:: Check Node.js installation
node --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Node.js is not installed or not in PATH
    echo Please install Node.js 18+ from https://nodejs.org
    pause
    exit /b 1
)

echo [1/4] Starting Backend Setup...
cd backend

:: Create virtual environment if it doesn't exist
if not exist "venv" (
    echo Creating Python virtual environment...
    python -m venv venv
)

:: Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

:: Install backend dependencies
echo Installing backend dependencies...
pip install -q -r requirements.txt

:: Check for .env file
if not exist ".env" (
    echo.
    echo WARNING: .env file not found!
    echo Please copy .env.template to .env and configure your AWS credentials
    echo.
    pause
)

:: Start backend server
echo.
echo [2/4] Starting Backend Server...
start cmd /k "cd /d %CD% && venv\Scripts\activate.bat && python main.py"

:: Wait for backend to start
timeout /t 5 /nobreak >nul

:: Frontend setup
echo.
echo [3/4] Starting Frontend Setup...
cd ..\frontend

:: Install frontend dependencies if needed
if not exist "node_modules" (
    echo Installing frontend dependencies...
    npm install
)

:: Start frontend server
echo.
echo [4/4] Starting Frontend Server...
start cmd /k "cd /d %CD% && ng serve"

:: Wait for frontend to start
timeout /t 10 /nobreak >nul

:: Open browser
echo.
echo ===============================================
echo    DocXP is starting up!
echo    
echo    Backend API: http://localhost:8000
echo    Frontend UI: http://localhost:4200
echo    
echo    Opening browser in 5 seconds...
echo ===============================================
timeout /t 5 /nobreak >nul

:: Open default browser
start http://localhost:4200

echo.
echo DocXP is running!
echo Press Ctrl+C in each window to stop the servers
pause
