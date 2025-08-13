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

echo [1/5] Starting Backend Setup...
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
    echo ERROR: .env file not found!
    echo Creating .env from template...
    copy .env.template .env >nul
    echo.
    echo IMPORTANT: Please edit backend\.env and configure your AWS credentials:
    echo   - AWS_REGION (default: us-east-1)
    echo   - AWS_PROFILE (if using AWS CLI profiles)
    echo   OR
    echo   - AWS_ACCESS_KEY_ID
    echo   - AWS_SECRET_ACCESS_KEY
    echo   - AWS_SESSION_TOKEN (if using temporary credentials)
    echo.
    pause
)

:: Validate AWS credentials
echo.
echo [2/5] Validating AWS Credentials...
python -c "import sys; sys.path.insert(0, '.'); from app.services.ai_service import AIService; ai = AIService(); print('AWS Credentials validated successfully!')" 2>&1
if errorlevel 1 (
    echo.
    echo ===============================================
    echo ERROR: AWS Credentials validation failed!
    echo.
    echo Please ensure you have configured one of the following:
    echo.
    echo Option 1: AWS Profile
    echo   - Set AWS_PROFILE in .env file
    echo   - Ensure AWS CLI is configured with: aws configure
    echo.
    echo Option 2: Explicit Credentials
    echo   - Set AWS_ACCESS_KEY_ID in .env file
    echo   - Set AWS_SECRET_ACCESS_KEY in .env file
    echo   - Set AWS_SESSION_TOKEN in .env file (if using temporary credentials)
    echo.
    echo Option 3: IAM Role (for EC2/ECS)
    echo   - Ensure the instance has proper IAM role attached
    echo.
    echo Required IAM Permissions:
    echo   - bedrock:InvokeModel
    echo   - bedrock:ListFoundationModels
    echo.
    echo For more information, see:
    echo https://docs.aws.amazon.com/bedrock/latest/userguide/getting-started.html
    echo ===============================================
    pause
    exit /b 1
)

:: Start backend server
echo.
echo [3/5] Starting Backend Server on port 8001...
start cmd /k "cd /d %CD% && venv\Scripts\activate.bat && python main.py"

:: Wait for backend to start
timeout /t 5 /nobreak >nul

:: Frontend setup
echo.
echo [4/5] Starting Frontend Setup...
cd ..\frontend

:: Install frontend dependencies if needed
if not exist "node_modules" (
    echo Installing frontend dependencies...
    npm install
)

:: Start frontend server
echo.
echo [5/5] Starting Frontend Server...
start cmd /k "cd /d %CD% && ng serve"

:: Wait for frontend to start
timeout /t 10 /nobreak >nul

:: Open browser
echo.
echo ===============================================
echo    DocXP is starting up!
echo    
echo    Backend API: http://localhost:8001
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
echo.
echo Troubleshooting:
echo - If you see CORS errors, ensure backend is running on port 8001
echo - If AWS errors occur, check your credentials in backend\.env
echo - For logs, check backend\logs\docxp.log
pause
