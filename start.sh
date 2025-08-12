#!/bin/bash

echo "==============================================="
echo "   DocXP - AI Documentation Platform"
echo "   Starting Development Environment"
echo "==============================================="
echo ""

# Check Python installation
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed"
    echo "Please install Python 3.10+ from https://www.python.org"
    exit 1
fi

# Check Node.js installation
if ! command -v node &> /dev/null; then
    echo "ERROR: Node.js is not installed"
    echo "Please install Node.js 18+ from https://nodejs.org"
    exit 1
fi

echo "[1/4] Starting Backend Setup..."
cd backend

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install backend dependencies
echo "Installing backend dependencies..."
pip install -q -r requirements.txt

# Check for .env file
if [ ! -f ".env" ]; then
    echo ""
    echo "WARNING: .env file not found!"
    echo "Please copy .env.template to .env and configure your AWS credentials"
    echo ""
    read -p "Press Enter to continue..."
fi

# Start backend server in background
echo ""
echo "[2/4] Starting Backend Server..."
python main.py &
BACKEND_PID=$!

# Wait for backend to start
sleep 5

# Frontend setup
echo ""
echo "[3/4] Starting Frontend Setup..."
cd ../frontend

# Install frontend dependencies if needed
if [ ! -d "node_modules" ]; then
    echo "Installing frontend dependencies..."
    npm install
fi

# Start frontend server in background
echo ""
echo "[4/4] Starting Frontend Server..."
ng serve &
FRONTEND_PID=$!

# Wait for frontend to start
sleep 10

echo ""
echo "==============================================="
echo "   DocXP is starting up!"
echo "   "
echo "   Backend API: http://localhost:8000"
echo "   Frontend UI: http://localhost:4200"
echo "   "
echo "   Opening browser in 5 seconds..."
echo "==============================================="
sleep 5

# Open browser (works on Mac and most Linux distros)
if [[ "$OSTYPE" == "darwin"* ]]; then
    open http://localhost:4200
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    xdg-open http://localhost:4200
fi

echo ""
echo "DocXP is running!"
echo "Press Ctrl+C to stop all servers"

# Wait for user to stop
trap "kill $BACKEND_PID $FRONTEND_PID; exit" INT
wait
