#!/bin/bash
# DocXP Production Setup Script
# Ensures ALL services are operational - no degradation

set -e  # Exit on any error

echo "🚀 DocXP Production Setup - Complete Installation"
echo "=================================================="

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

# Function to check if service is running
check_service() {
    local service_name=$1
    local port=$2
    
    if nc -z localhost $port 2>/dev/null; then
        print_status "$service_name is running on port $port"
        return 0
    else
        print_warning "$service_name is not running on port $port"
        return 1
    fi
}

# Function to wait for service
wait_for_service() {
    local service_name=$1
    local port=$2
    local max_wait=60
    local wait_time=0
    
    print_info "Waiting for $service_name on port $port..."
    
    while ! nc -z localhost $port 2>/dev/null; do
        if [ $wait_time -ge $max_wait ]; then
            print_error "$service_name failed to start within $max_wait seconds"
            return 1
        fi
        
        sleep 2
        wait_time=$((wait_time + 2))
        echo -n "."
    done
    
    echo ""
    print_status "$service_name is ready!"
    return 0
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

# Check Podman
if command -v podman &> /dev/null; then
    PODMAN_VERSION=$(podman --version | cut -d' ' -f3)
    print_status "Podman found: $PODMAN_VERSION"
else
    print_error "Podman not found. Podman is REQUIRED for production services."
    exit 1
fi

# Check netcat for service checking
if ! command -v nc &> /dev/null; then
    print_error "netcat (nc) not found. Please install netcat for service health checks."
    exit 1
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

# Start PostgreSQL
echo ""
echo "🐘 Starting PostgreSQL Database..."

if ! check_service "PostgreSQL" 5432; then
    print_info "Starting PostgreSQL container..."
    
    podman run -d \
        --name docxp-postgres \
        -p 5432:5432 \
        -e POSTGRES_DB=docxp \
        -e POSTGRES_USER=docxp \
        -e POSTGRES_PASSWORD=docxp-production-2024 \
        -v docxp-postgres-data:/var/lib/postgresql/data \
        postgres:15
    
    if ! wait_for_service "PostgreSQL" 5432; then
        print_error "Failed to start PostgreSQL"
        exit 1
    fi
else
    print_info "PostgreSQL already running"
fi

# Verify PostgreSQL connection
print_info "Verifying PostgreSQL connection..."
sleep 5  # Give PostgreSQL time to fully initialize

if podman exec docxp-postgres pg_isready -U docxp &>/dev/null; then
    print_status "PostgreSQL connection verified"
else
    print_error "PostgreSQL connection failed"
    exit 1
fi

# Start Neo4j
echo ""
echo "🌐 Starting Neo4j Knowledge Graph..."

if ! check_service "Neo4j" 7687; then
    print_info "Starting Neo4j container..."
    
    podman run -d \
        --name docxp-neo4j \
        -p 7474:7474 -p 7687:7687 \
        -e NEO4J_AUTH=neo4j/docxp-production-2024 \
        -v docxp-neo4j-data:/data \
        neo4j:latest
    
    if ! wait_for_service "Neo4j" 7687; then
        print_error "Failed to start Neo4j"
        exit 1
    fi
else
    print_info "Neo4j already running"
fi

# Verify Neo4j connection
print_info "Verifying Neo4j connection..."
sleep 10  # Give Neo4j time to fully initialize

max_attempts=15
attempt=0
while [ $attempt -lt $max_attempts ]; do
    if curl -s http://localhost:7474 &>/dev/null; then
        print_status "Neo4j connection verified"
        break
    fi
    
    attempt=$((attempt + 1))
    if [ $attempt -eq $max_attempts ]; then
        print_error "Neo4j connection failed after $max_attempts attempts"
        exit 1
    fi
    
    sleep 2
done

# Start Redis
echo ""
echo "⚡ Starting Redis Cache/Queue..."

if ! check_service "Redis" 6379; then
    print_info "Starting Redis container..."
    
    podman run -d \
        --name docxp-redis \
        -p 6379:6379 \
        -v docxp-redis-data:/data \
        redis:latest
    
    if ! wait_for_service "Redis" 6379; then
        print_error "Failed to start Redis"
        exit 1
    fi
else
    print_info "Redis already running"
fi

# Verify Redis connection
print_info "Verifying Redis connection..."
if podman exec docxp-redis redis-cli ping &>/dev/null; then
    print_status "Redis connection verified"
else
    print_error "Redis connection failed"
    exit 1
fi

# Create production configuration
echo ""
echo "⚙️ Creating Production Configuration..."

if [ ! -f "backend/.env" ]; then
    print_info "Creating production .env file..."
    cat > backend/.env << EOF
# Production DocXP Configuration
APP_NAME=DocXP
DEBUG=false
APP_ENV=production

# PostgreSQL Database (REQUIRED)
DATABASE_URL=postgresql+asyncpg://docxp:docxp-production-2024@localhost:5432/docxp

# Neo4j Knowledge Graph (REQUIRED)
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=docxp-production-2024
NEO4J_DATABASE=neo4j
NEO4J_ENABLED=true
NEO4J_MAX_CONNECTION_LIFETIME=300
NEO4J_MAX_CONNECTION_POOL_SIZE=50
NEO4J_CONNECTION_ACQUISITION_TIMEOUT=60

# Redis Cache/Queue (REQUIRED)
REDIS_URL=redis://localhost:6379
RQ_REDIS_URL=redis://localhost:6379
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_ENABLED=true

# AWS Bedrock (using msh profile)
AWS_PROFILE=msh
AWS_REGION=us-east-1
BEDROCK_MODEL_ID=us.anthropic.claude-3-5-sonnet-20241022-v2:0

# Production Performance Settings
MAX_CONCURRENT_REPOS=8
BATCH_SIZE=100
MAX_WORKERS=8
PROCESSING_TIMEOUT=1200

# Vector Database
VECTOR_DB_TYPE=chromadb
VECTOR_DB_PATH=./data/vector_db
VECTOR_DB_ENABLED=true

# File Processing
OUTPUT_DIR=./output
TEMP_DIR=./temp
CONFIGS_DIR=./configs
MAX_FILE_SIZE_MB=500

# Logging
LOG_LEVEL=INFO
EOF

    print_status "Production configuration created"
else
    print_info "Configuration file already exists"
fi

# Initialize databases
echo ""
echo "🗃️ Initializing Database Schemas..."

cd backend

# Initialize PostgreSQL
print_info "Initializing PostgreSQL database..."
$PYTHON_CMD -c "
import asyncio
import sys
sys.path.insert(0, '.')

async def init_db():
    try:
        from app.core.database import init_db
        await init_db()
        print('✅ PostgreSQL database initialized successfully')
        return True
    except Exception as e:
        print(f'❌ PostgreSQL initialization failed: {e}')
        return False

result = asyncio.run(init_db())
if not result:
    exit(1)
"

if [ $? -ne 0 ]; then
    print_error "PostgreSQL initialization failed"
    exit 1
fi

# Initialize Neo4j
print_info "Initializing Neo4j indexes..."
$PYTHON_CMD -c "
import asyncio
import sys
sys.path.insert(0, '.')

async def init_neo4j():
    try:
        from app.services.knowledge_graph_service import get_knowledge_graph_service
        kg = await get_knowledge_graph_service()
        await kg.create_indexes()
        print('✅ Neo4j indexes created successfully')
        return True
    except Exception as e:
        print(f'❌ Neo4j initialization failed: {e}')
        return False

result = asyncio.run(init_neo4j())
if not result:
    exit(1)
"

if [ $? -ne 0 ]; then
    print_error "Neo4j initialization failed"
    exit 1
fi

# Run comprehensive validation
echo ""
echo "🧪 Running Production Validation..."

$PYTHON_CMD -c "
import asyncio
import sys
sys.path.insert(0, '.')

async def full_validation():
    print('🔍 Validating Complete DocXP Production Installation...')
    all_passed = True
    
    # Test PostgreSQL
    try:
        from app.core.database import get_async_session
        async with get_async_session() as session:
            result = await session.execute('SELECT 1')
            await session.commit()
        print('✅ PostgreSQL: Connected and operational')
    except Exception as e:
        print(f'❌ PostgreSQL: {e}')
        all_passed = False
    
    # Test Neo4j
    try:
        from app.services.knowledge_graph_service import get_knowledge_graph_service
        kg = await get_knowledge_graph_service()
        stats = await kg.get_graph_statistics()
        print('✅ Neo4j: Connected and operational')
    except Exception as e:
        print(f'❌ Neo4j: {e}')
        all_passed = False
    
    # Test Redis
    try:
        from app.services.project_coordinator_service import get_project_coordinator_service
        pc = await get_project_coordinator_service()
        if pc.redis_client and pc.job_queue:
            pc.redis_client.ping()
            print('✅ Redis: Connected and operational')
        else:
            print('❌ Redis: Not properly initialized')
            all_passed = False
    except Exception as e:
        print(f'❌ Redis: {e}')
        all_passed = False
    
    if all_passed:
        print('🎉 ALL SERVICES OPERATIONAL - DocXP ready for production!')
        return True
    else:
        print('❌ VALIDATION FAILED - Some services are not operational')
        return False

result = asyncio.run(full_validation())
exit(0 if result else 1)
"

if [ $? -ne 0 ]; then
    print_error "Production validation failed"
    exit 1
fi

# Run golden path test
print_info "Running golden path test..."
if $PYTHON_CMD simple_golden_path_test.py; then
    print_status "Golden path test passed"
else
    print_error "Golden path test failed"
    exit 1
fi

cd ..

# Create service management scripts
echo ""
echo "📜 Creating Service Management Scripts..."

# Start script
cat > start-docxp.sh << 'EOF'
#!/bin/bash
echo "🚀 Starting DocXP Production Services..."

# Start all services
podman start docxp-postgres docxp-neo4j docxp-redis

echo "⏳ Waiting for services to be ready..."
sleep 15

# Health check
echo "🔍 Service Health Check:"
if podman exec docxp-postgres pg_isready -U docxp &>/dev/null; then
    echo "✅ PostgreSQL: Healthy"
else
    echo "❌ PostgreSQL: Not healthy"
fi

if curl -s http://localhost:7474 &>/dev/null; then
    echo "✅ Neo4j: Healthy"
else
    echo "❌ Neo4j: Not healthy"
fi

if podman exec docxp-redis redis-cli ping &>/dev/null; then
    echo "✅ Redis: Healthy"
else
    echo "❌ Redis: Not healthy"
fi

echo "🎉 DocXP services started"
EOF

# Stop script
cat > stop-docxp.sh << 'EOF'
#!/bin/bash
echo "🛑 Stopping DocXP Services..."
podman stop docxp-postgres docxp-neo4j docxp-redis
echo "✅ All services stopped"
EOF

# Status script
cat > status-docxp.sh << 'EOF'
#!/bin/bash
echo "📊 DocXP Service Status"
echo "======================"
podman ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" --filter name=docxp
EOF

chmod +x start-docxp.sh stop-docxp.sh status-docxp.sh

print_status "Service management scripts created"

# Final success message
echo ""
echo "=================================================="
print_status "🎉 PRODUCTION SETUP COMPLETE!"
echo ""
echo "DocXP is now fully operational with ALL services running:"
echo "  ✅ PostgreSQL Database"
echo "  ✅ Neo4j Knowledge Graph" 
echo "  ✅ Redis Cache/Queue"
echo "  ✅ Python Environment"
echo "  ✅ All configurations"
echo ""
echo "🔧 Service Management:"
echo "  Start:  ./start-docxp.sh"
echo "  Stop:   ./stop-docxp.sh" 
echo "  Status: ./status-docxp.sh"
echo ""
echo "🚀 Ready for Enterprise Use:"
echo "  cd backend && python analyze_repo.py"
echo "  cd backend && python project.py"
echo ""
echo "📊 Monitoring:"
echo "  Neo4j Browser: http://localhost:7474"
echo "  PostgreSQL: localhost:5432"
echo "  Redis: localhost:6379"
echo ""
echo "=================================================="