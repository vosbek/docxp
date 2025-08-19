@echo off
REM DocXP Backend Startup Script

echo 🚀 Starting DocXP Backend API...
echo ===============================

REM Activate virtual environment
call docxp-env\Scripts\activate.bat

REM Change to backend directory
cd backend

REM Start FastAPI server
echo Starting FastAPI server on http://localhost:8001
echo Press Ctrl+C to stop the server
echo.
python -m uvicorn main:app --host 0.0.0.0 --port 8001 --reload