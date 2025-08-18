#!/bin/bash
# DocXP Quick Setup Script
# Optimized for machines with existing infrastructure

set -e  # Exit on any error

echo "🚀 DocXP Quick Setup Starting..."
echo "=============================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}✅${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠️${NC} $1"
}

print_error() {
    echo -e "${RED}❌${NC} $1"
}

print_info() {
    echo -e "${BLUE}ℹ️${NC} $1"
}

# Check prerequisites
echo ""
echo "🔍 Checking Prerequisites..."

# Check Python
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2)
    print_status "Python found: $PYTHON_VERSION"
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    PYTHON_VERSION=$(python --version 2>&1 | cut -d' ' -f2)
    print_status "Python found: $PYTHON_VERSION"
    PYTHON_CMD="python"
else
    print_error "Python not found. Please install Python 3.11+"
    exit 1
fi

# Check Git
if command -v git &> /dev/null; then
    GIT_VERSION=$(git --version | cut -d' ' -f3)
    print_status "Git found: $GIT_VERSION"
else
    print_error "Git not found. Please install Git"
    exit 1
fi

# Check optional services
echo ""
echo "🔍 Checking Optional Services..."

if command -v podman &> /dev/null; then
    PODMAN_VERSION=$(podman --version | cut -d' ' -f3)
    print_status "Podman found: $PODMAN_VERSION"
    HAS_PODMAN=true
else
    print_warning "Podman not found. Optional services will be skipped"
    HAS_PODMAN=false
fi

if command -v aws &> /dev/null; then
    print_status "AWS CLI found"
    HAS_AWS=true
else
    print_warning "AWS CLI not found. Bedrock features will be disabled"
    HAS_AWS=false
fi

# Setup Python environment
echo ""
echo "🐍 Setting up Python Environment..."

if [ ! -d "docxp-env" ]; then
    print_info "Creating virtual environment..."
    $PYTHON_CMD -m venv docxp-env
    print_status "Virtual environment created"
else
    print_info "Virtual environment already exists"
fi

# Activate virtual environment
print_info "Activating virtual environment..."
source docxp-env/bin/activate

# Install dependencies
print_info "Installing Python dependencies..."
pip install -r backend/requirements.txt

print_status "Dependencies installed"

# Create basic .env file if it doesn't exist
echo ""
echo "⚙️ Setting up Configuration..."

if [ ! -f "backend/.env" ]; then
    print_info "Creating configuration file..."
    cat > backend/.env << EOF
# DocXP Configuration
APP_NAME=DocXP
DEBUG=false

# Core Database
DATABASE_URL=sqlite+aiosqlite:///./docxp.db

# Processing Configuration
MAX_CONCURRENT_REPOS=4
BATCH_SIZE=50
MAX_WORKERS=4
PROCESSING_TIMEOUT=600

# Neo4j (Optional - will gracefully degrade if not available)
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=docxp-2024
NEO4J_ENABLED=true

# Redis (Optional - will gracefully degrade if not available)
REDIS_URL=redis://localhost:6379
RQ_REDIS_URL=redis://localhost:6379
REDIS_ENABLED=true

# AWS Bedrock (Optional)
AWS_REGION=us-east-1
BEDROCK_MODEL_ID=us.anthropic.claude-3-5-sonnet-20241022-v2:0
EOF

    print_status "Configuration file created at backend/.env"
else
    print_info "Configuration file already exists"
fi

# Offer to setup optional services with Podman
if [ "$HAS_PODMAN" = true ]; then
    echo ""
    echo "🐳 Optional: Setup Enhanced Services with Podman"
    read -p "Would you like to start Neo4j and Redis with Podman? (y/n): " -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_info "Starting Neo4j with Podman..."
        podman run -d \
            --name docxp-neo4j \
            -p 7474:7474 -p 7687:7687 \
            -e NEO4J_AUTH=neo4j/docxp-2024 \
            neo4j:latest > /dev/null 2>&1 || print_warning "Neo4j container may already exist"
        
        print_info "Starting Redis with Podman..."
        podman run -d \
            --name docxp-redis \
            -p 6379:6379 \
            redis:latest > /dev/null 2>&1 || print_warning "Redis container may already exist"
        
        print_status "Optional services started"
        
        # Wait a moment for services to start
        sleep 5
    fi
fi

# Run validation test
echo ""
echo "🧪 Running Validation Test..."

cd backend
if $PYTHON_CMD simple_golden_path_test.py; then
    echo ""
    echo "=============================================="
    print_status "🎉 DocXP Setup Complete!"
    echo ""
    echo "Your DocXP installation is ready for enterprise use."
    echo ""
    echo "Next steps:"
    echo "  1. Analyze a repository:"
    echo "     cd backend && python analyze_repo.py"
    echo ""
    echo "  2. Create a project:"
    echo "     cd backend && python project.py"
    echo ""
    echo "  3. Review documentation:"
    echo "     - QUICK_DEPLOYMENT_GUIDE.md"
    echo "     - PHASE_1_COMPLETION_REPORT.md"
    echo ""
    if [ "$HAS_PODMAN" = true ]; then
        echo "  4. Manage services:"
        echo "     podman start docxp-neo4j docxp-redis"
        echo "     podman stop docxp-neo4j docxp-redis"
        echo ""
    fi
    echo "=============================================="
else
    echo ""
    print_error "Setup validation failed. Please check the error messages above."
    echo ""
    echo "Common fixes:"
    echo "  - Ensure Python 3.11+ is installed"
    echo "  - Check network connectivity"
    echo "  - Verify file permissions"
    echo ""
    echo "For help, see QUICK_DEPLOYMENT_GUIDE.md"
    exit 1
fi