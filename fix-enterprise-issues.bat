@echo off
echo ============================================================================
echo  DocXP Enterprise Machine Diagnostic and Fix
echo ============================================================================

echo [1/4] Checking actual container names...
echo Available containers with 'postgres' in name:
podman ps -a --filter name=postgres --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
echo.
echo Available containers with 'docxp' in name:  
podman ps -a --filter name=docxp --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
echo.

echo [2/4] Testing AWS Bedrock access with msh profile...
aws bedrock list-foundation-models --profile msh --region us-east-1 --max-items 1 2>nul && (
    echo ✅ AWS Bedrock access working with msh profile
) || (
    echo ❌ AWS Bedrock access failing with msh profile
    echo Checking if profile is set in environment...
    echo AWS_PROFILE=%AWS_PROFILE%
    echo.
)

echo [3/4] Checking PostgreSQL connectivity...
powershell -c "Test-NetConnection -ComputerName localhost -Port 5432 -WarningAction SilentlyContinue" | findstr "TcpTestSucceeded"

echo [4/4] Checking application environment variables...
echo Checking if AWS_PROFILE is set for the application...
cd backend
python -c "import os; print('AWS_PROFILE in env:', os.getenv('AWS_PROFILE', 'NOT SET')); print('AWS_REGION in env:', os.getenv('AWS_REGION', 'NOT SET'))"

echo.
echo ============================================================================
echo  Analysis Complete
echo ============================================================================
pause