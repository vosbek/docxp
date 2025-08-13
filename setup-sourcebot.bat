@echo off
echo ========================================
echo    DocXP to Sourcebot Setup Script
echo ========================================
echo.

REM Create new directory structure
echo Creating Sourcebot directory structure...
if not exist sourcebot mkdir sourcebot
cd sourcebot

if not exist packages mkdir packages
if not exist packages\shared mkdir packages\shared
if not exist packages\backend mkdir packages\backend
if not exist packages\web mkdir packages\web

REM Create basic config.json
echo Creating initial configuration...
(
echo {
echo   "$schema": "https://raw.githubusercontent.com/sourcebot-dev/sourcebot/main/schemas/v3/index.json",
echo   "connections": {
echo     "local-dev": {
echo       "type": "github",
echo       "repos": [
echo         "sourcebot-dev/sourcebot"
echo       ]
echo     }
echo   }
echo }
) > config.json

REM Create docker-compose.yml
echo Creating Docker Compose configuration...
(
echo version: '3.8'
echo.
echo services:
echo   zoekt:
echo     image: sourcegraph/zoekt-webserver:latest
echo     ports:
echo       - "6070:6070"
echo     volumes:
echo       - zoekt-index:/data
echo     environment:
echo       - GOGC=50
echo.
echo   postgres:
echo     image: postgres:15-alpine
echo     environment:
echo       - POSTGRES_DB=sourcebot
echo       - POSTGRES_USER=sourcebot
echo       - POSTGRES_PASSWORD=sourcebot
echo     volumes:
echo       - postgres-data:/var/lib/postgresql/data
echo.
echo   redis:
echo     image: redis:7-alpine
echo     volumes:
echo       - redis-data:/data
echo.
echo volumes:
echo   zoekt-index:
echo   postgres-data:
echo   redis-data:
) > docker-compose.yml

REM Create backend package.json
cd packages\backend
echo Creating backend package.json...
(
echo {
echo   "name": "@docxp/backend",
echo   "version": "1.0.0",
echo   "description": "DocXP Sourcebot Backend Services",
echo   "main": "dist/index.js",
echo   "scripts": {
echo     "dev": "tsx watch src/index.ts",
echo     "build": "tsc",
echo     "start": "node dist/index.js"
echo   },
echo   "dependencies": {
echo     "@apollo/server": "^4.9.5",
echo     "graphql": "^16.8.1",
echo     "express": "^4.18.2",
echo     "axios": "^1.6.2",
echo     "bullmq": "^5.1.0",
echo     "pg": "^8.11.3",
echo     "node-cron": "^3.0.3",
echo     "@google/generative-ai": "^0.1.3"
echo   },
echo   "devDependencies": {
echo     "@types/node": "^20.10.5",
echo     "typescript": "^5.3.3",
echo     "tsx": "^4.6.2"
echo   }
echo }
) > package.json

REM Create TypeScript config
echo Creating TypeScript configuration...
(
echo {
echo   "compilerOptions": {
echo     "target": "ES2022",
echo     "module": "commonjs",
echo     "lib": ["ES2022"],
echo     "outDir": "./dist",
echo     "rootDir": "./src",
echo     "strict": true,
echo     "esModuleInterop": true,
echo     "skipLibCheck": true,
echo     "forceConsistentCasingInFileNames": true,
echo     "resolveJsonModule": true,
echo     "moduleResolution": "node"
echo   },
echo   "include": ["src/**/*"],
echo   "exclude": ["node_modules", "dist"]
echo }
) > tsconfig.json

cd ..\..

REM Create README for the new structure
echo Creating Sourcebot README...
(
echo # DocXP Sourcebot Implementation
echo.
echo This is the new Sourcebot-based implementation of DocXP, combining:
echo - Lightning-fast code search using Zoekt
echo - AI-powered Q&A with Gemini
echo - Legacy DocXP documentation generation features
echo.
echo ## Quick Start
echo.
echo 1. Install dependencies:
echo    ```
echo    cd packages/backend
echo    npm install
echo    cd ../web
echo    npm install
echo    ```
echo.
echo 2. Start services:
echo    ```
echo    docker-compose up -d
echo    ```
echo.
echo 3. Start development servers:
echo    ```
echo    # Terminal 1 - Backend
echo    cd packages/backend
echo    npm run dev
echo.
echo    # Terminal 2 - Frontend
echo    cd packages/web
echo    npm run dev
echo    ```
echo.
echo 4. Access the application:
echo    - Frontend: http://localhost:3000
echo    - GraphQL: http://localhost:4000/graphql
echo    - Zoekt: http://localhost:6070
) > README.md

cd ..

echo.
echo ========================================
echo    Setup Complete!
echo ========================================
echo.
echo Next steps:
echo 1. cd sourcebot
echo 2. Install Go and Node.js dependencies
echo 3. docker-compose up -d (to start services)
echo 4. Begin implementing services as per roadmap
echo.
echo The implementation roadmap has been saved to your artifacts.
echo.
pause
