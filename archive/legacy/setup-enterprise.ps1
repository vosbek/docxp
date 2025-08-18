# DocXP Enterprise Setup Script
# Sets up PostgreSQL + AWS Bedrock architecture

Write-Host "🚀 DocXP Enterprise Architecture Setup" -ForegroundColor Green
Write-Host "================================================" -ForegroundColor Green

# Check if in virtual environment
if (-not $env:VIRTUAL_ENV) {
    Write-Host "❌ Please activate your virtual environment first:" -ForegroundColor Red
    Write-Host "   venv\Scripts\activate" -ForegroundColor Yellow
    exit 1
}

Write-Host "✅ Virtual environment detected: $env:VIRTUAL_ENV" -ForegroundColor Green

# Install required packages
Write-Host "`n📦 Installing enterprise dependencies..." -ForegroundColor Blue

$packages = @(
    "pgvector==0.2.4",
    "asyncpg==0.29.0", 
    "sqlalchemy[asyncio]==2.0.23",
    "boto3==1.34.0",
    "numpy==1.24.3"
)

foreach ($package in $packages) {
    Write-Host "Installing $package..." -ForegroundColor Cyan
    pip install $package
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Failed to install $package" -ForegroundColor Red
        exit 1
    }
}

# Setup PostgreSQL pgvector extension
Write-Host "`n🗄️ Setting up PostgreSQL vector extension..." -ForegroundColor Blue

$sqlCommands = @"
-- Connect to your PostgreSQL database and run these commands:
-- psql -U docxp_user -d docxp_enterprise -h localhost

-- Create vector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Verify extension
SELECT * FROM pg_extension WHERE extname = 'vector';

-- Create test vector table
CREATE TABLE IF NOT EXISTS test_vectors (
    id SERIAL PRIMARY KEY,
    content TEXT,
    embedding vector(1024)
);

-- Test vector operations
INSERT INTO test_vectors (content, embedding) 
VALUES ('test', '[1,2,3,4,5,6,7,8,9,10]'::vector);

SELECT content, embedding <-> '[1,2,3,4,5,6,7,8,9,10]'::vector as distance 
FROM test_vectors 
ORDER BY distance LIMIT 5;

-- Clean up test
DROP TABLE test_vectors;
"@

Write-Host $sqlCommands -ForegroundColor Yellow

# Copy enterprise environment file
Write-Host "`n⚙️ Setting up enterprise configuration..." -ForegroundColor Blue

if (Test-Path "backend\.env.enterprise") {
    Copy-Item "backend\.env.enterprise" "backend\.env" -Force
    Write-Host "✅ Enterprise .env file configured" -ForegroundColor Green
} else {
    Write-Host "❌ Enterprise .env file not found" -ForegroundColor Red
}

# Test AWS credentials
Write-Host "`n🔑 Testing AWS credentials..." -ForegroundColor Blue
try {
    aws sts get-caller-identity --profile msh | Out-Null
    Write-Host "✅ AWS credentials working" -ForegroundColor Green
} catch {
    Write-Host "❌ AWS credentials not configured or profile 'msh' not found" -ForegroundColor Red
    Write-Host "   Please configure AWS SSO login: aws sso login --profile msh" -ForegroundColor Yellow
}

# Display next steps
Write-Host "`n🎯 Enterprise Setup Complete!" -ForegroundColor Green
Write-Host "================================================" -ForegroundColor Green
Write-Host "Next Steps:" -ForegroundColor White
Write-Host "1. Run the PostgreSQL commands shown above" -ForegroundColor Cyan
Write-Host "2. Test the application:" -ForegroundColor Cyan  
Write-Host "   cd backend && python main.py" -ForegroundColor Yellow
Write-Host "3. Check logs for 'PostgreSQL vector database initialized'" -ForegroundColor Cyan
Write-Host "4. Verify Bedrock embeddings are being used" -ForegroundColor Cyan
Write-Host "`nConfiguration:" -ForegroundColor White
Write-Host "• Vector Storage: PostgreSQL pgvector" -ForegroundColor Green
Write-Host "• Embeddings: AWS Bedrock Titan Text v2 (1024 dimensions)" -ForegroundColor Green  
Write-Host "• Chat: AWS Bedrock Claude 3.5 Sonnet" -ForegroundColor Green
Write-Host "• Database: PostgreSQL with full ACID compliance" -ForegroundColor Green