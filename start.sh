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

echo "[1/5] Starting Backend Setup..."
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
    echo "ERROR: .env file not found!"
    echo "Creating .env from template..."
    cp .env.template .env
    echo ""
    echo "IMPORTANT: Please edit backend/.env and configure your AWS credentials:"
    echo "  - AWS_REGION (default: us-east-1)"
    echo "  - AWS_PROFILE (if using AWS CLI profiles)"
    echo "  OR"
    echo "  - AWS_ACCESS_KEY_ID"
    echo "  - AWS_SECRET_ACCESS_KEY"
    echo "  - AWS_SESSION_TOKEN (if using temporary credentials)"
    echo ""
    read -p "Press Enter to continue after configuring..."
fi

# Validate AWS credentials
echo ""
echo "[2/5] Validating AWS Credentials..."
if ! python3 -c "import sys; sys.path.insert(0, '.'); from app.services.ai_service import AIService; ai = AIService(); print('AWS Credentials validated successfully!')"; then
    echo ""
    echo "==============================================="
    echo "ERROR: AWS Credentials validation failed!"
    echo ""
    echo "Please ensure you have configured one of the following:"
    echo ""
    echo "Option 1: AWS Profile"
    echo "  - Set AWS_PROFILE in .env file"
    echo "  - Ensure AWS CLI is configured with: aws configure"
    echo ""
    echo "Option 2: Explicit Credentials"
    echo "  - Set AWS_ACCESS_KEY_ID in .env file"
    echo "  - Set AWS_SECRET_ACCESS_KEY in .env file"
    echo "  - Set AWS_SESSION_TOKEN in .env file (if using temporary credentials)"
    echo ""
    echo "Option 3: IAM Role (for EC2/ECS)"
    echo "  - Ensure the instance has proper IAM role attached"
    echo ""
    echo "Required IAM Permissions:"
    echo "  - bedrock:InvokeModel"
    echo "  - bedrock:ListFoundationModels"
    echo ""
    echo "For more information, see:"
    echo "https://docs.aws.amazon.com/bedrock/latest/userguide/getting-started.html"
    echo "==============================================="
    exit 1
fi

# Start backend server
echo ""
echo "[3/5] Starting Backend Server on port 8001..."
python main.py &
BACKEND_PID=$!

# Wait for backend to start
sleep 5

# Frontend setup
echo ""
echo "[4/5] Starting Frontend Setup..."
cd ../frontend

# Install frontend dependencies if needed
if [ ! -d "node_modules" ]; then
    echo "Installing frontend dependencies..."
    npm install
fi

# Start frontend server
echo ""
echo "[5/5] Starting Frontend Server..."
ng serve &
FRONTEND_PID=$!

# Wait for frontend to start
sleep 10

# Open browser (works on macOS and most Linux distributions)
echo ""
echo "==============================================="
echo "   DocXP is starting up!"
echo "   "
echo "   Backend API: http://localhost:8001"
echo "   Frontend UI: http://localhost:4200"
echo "   "
echo "   Opening browser in 5 seconds..."
echo "==============================================="
sleep 5

# Open browser based on OS
if [[ "$OSTYPE" == "darwin"* ]]; then
    open http://localhost:4200
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    xdg-open http://localhost:4200 2>/dev/null || echo "Please open http://localhost:4200 in your browser"
fi

echo ""
echo "DocXP is running!"
echo "Backend PID: $BACKEND_PID"
echo "Frontend PID: $FRONTEND_PID"
echo ""
echo "To stop the servers:"
echo "  kill $BACKEND_PID $FRONTEND_PID"
echo ""
echo "Troubleshooting:"
echo "- If you see CORS errors, ensure backend is running on port 8001"
echo "- If AWS errors occur, check your credentials in backend/.env"
echo "- For logs, check backend/logs/docxp.log"
echo ""
echo "Press Ctrl+C to stop all servers"

# Wait for user interrupt
trap "kill $BACKEND_PID $FRONTEND_PID; exit" INT
wait
