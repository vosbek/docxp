@echo off
echo DocXP Knowledge Graph Startup Script
echo =====================================

echo.
echo Step 1: Starting Neo4j and Backend Services...
docker-compose up -d neo4j

echo.
echo Step 2: Waiting for Neo4j to be ready...
timeout /t 30 /nobreak > nul

echo.
echo Step 3: Setting up Neo4j database...
cd backend
python scripts\setup-neo4j.py
if errorlevel 1 (
    echo Failed to setup Neo4j database
    pause
    exit /b 1
)

echo.
echo Step 4: Running integration tests...
python test_knowledge_graph_integration.py
if errorlevel 1 (
    echo Integration tests failed
    pause
    exit /b 1
)

echo.
echo Step 5: Starting all services...
cd ..
docker-compose up -d

echo.
echo =====================================
echo DocXP Knowledge Graph is now running!
echo =====================================
echo.
echo Access points:
echo - Neo4j Browser: http://localhost:7474
echo - DocXP Backend: http://localhost:8000
echo - DocXP Frontend: http://localhost:80
echo.
echo Login credentials for Neo4j:
echo - Username: neo4j
echo - Password: docxp-neo4j-2024
echo.
pause