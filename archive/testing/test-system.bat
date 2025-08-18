@echo off
REM ============================================
REM     DocXP Quick Test Suite
REM     Verifies all components are working
REM ============================================

echo ================================================
echo           DocXP System Test Suite
echo ================================================
echo.

REM Test 1: Python Check
echo [TEST 1/10] Python Installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo   FAILED: Python not found
    set /a FAILED+=1
) else (
    echo   PASSED: Python installed
    set /a PASSED+=1
)

REM Test 2: Node Check
echo [TEST 2/10] Node.js Installation...
node --version >nul 2>&1
if errorlevel 1 (
    echo   FAILED: Node.js not found
    set /a FAILED+=1
) else (
    echo   PASSED: Node.js installed
    set /a PASSED+=1
)

REM Test 3: Backend Dependencies
echo [TEST 3/10] Backend Dependencies...
cd backend
python -c "import fastapi, uvicorn, sqlalchemy, pydantic" 2>nul
if errorlevel 1 (
    echo   FAILED: Missing Python packages
    set /a FAILED+=1
) else (
    echo   PASSED: Python packages installed
    set /a PASSED+=1
)

REM Test 4: Frontend Dependencies
echo [TEST 4/10] Frontend Dependencies...
cd ..\frontend
if exist node_modules (
    echo   PASSED: Node modules installed
    set /a PASSED+=1
) else (
    echo   FAILED: Node modules not found
    set /a FAILED+=1
)

REM Test 5: Required Directories
echo [TEST 5/10] Required Directories...
cd ..\backend
set DIRS_OK=1
if not exist output set DIRS_OK=0
if not exist temp set DIRS_OK=0
if not exist logs set DIRS_OK=0
if %DIRS_OK%==1 (
    echo   PASSED: All directories present
    set /a PASSED+=1
) else (
    echo   FAILED: Some directories missing
    set /a FAILED+=1
)

REM Test 6: API Health Check (if running)
echo [TEST 6/10] API Health Check...
curl -s http://localhost:8001/health >nul 2>&1
if errorlevel 1 (
    echo   INFO: API not running (start with enhanced-start.bat)
    set /a SKIPPED+=1
) else (
    echo   PASSED: API is healthy
    set /a PASSED+=1
)

REM Test 7: Database Check
echo [TEST 7/10] Database Check...
if exist docxp.db (
    echo   PASSED: Database exists
    set /a PASSED+=1
) else (
    echo   INFO: Database will be created on first run
    set /a SKIPPED+=1
)

REM Test 8: Port Availability
echo [TEST 8/10] Port Availability...
netstat -an | findstr :8001 >nul 2>&1
if errorlevel 1 (
    echo   PASSED: Port 8001 available
    set /a PASSED+=1
) else (
    echo   INFO: Port 8001 in use
    set /a SKIPPED+=1
)

REM Test 9: AWS Configuration
echo [TEST 9/10] AWS Configuration...
if exist .env (
    findstr "AWS_ACCESS_KEY_ID" .env >nul 2>&1
    if errorlevel 1 (
        echo   INFO: AWS not configured (optional)
        set /a SKIPPED+=1
    ) else (
        echo   PASSED: AWS configured
        set /a PASSED+=1
    )
) else (
    echo   INFO: No .env file (AWS optional)
    set /a SKIPPED+=1
)

REM Test 10: Diagnostic Tool
echo [TEST 10/10] Diagnostic Tool...
if exist diagnose.py (
    echo   PASSED: Diagnostic tool available
    set /a PASSED+=1
) else (
    echo   FAILED: Diagnostic tool not found
    set /a FAILED+=1
)

echo.
echo ================================================
echo              TEST RESULTS SUMMARY
echo ================================================
echo.
echo   PASSED:  %PASSED% tests
echo   FAILED:  %FAILED% tests
echo   SKIPPED: %SKIPPED% tests (not critical)
echo.

if %FAILED% GTR 0 (
    echo ❌ RESULT: Some tests failed. Please fix issues above.
    echo.
    echo Recommended actions:
    echo 1. Run: python startup_check.py
    echo 2. Run: python diagnose.py
    echo 3. Check the documentation
) else (
    echo ✅ RESULT: All critical tests passed!
    echo.
    echo DocXP is ready to use. Start with:
    echo   enhanced-start.bat
)

echo.
echo ================================================
pause
