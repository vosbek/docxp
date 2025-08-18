#!/bin/bash

echo "========================================"
echo "   DocXP to Sourcebot Setup Script"
echo "========================================"
echo ""

# Create new directory structure
echo "Creating Sourcebot directory structure..."
mkdir -p sourcebot/packages/{shared,backend,web}
cd sourcebot

# Create basic config.json
echo "Creating initial configuration..."
cat > config.json << 'EOF'
{
  "$schema": "https://raw.githubusercontent.com/sourcebot-dev/sourcebot/main/schemas/v3/index.json",
  "connections": {
    "local-dev": {
      "type": "github",
      "repos": [
        "sourcebot-dev/sourcebot"
      ]
    }
  }
}
EOF

# Create docker-compose.yml
echo "Creating Docker Compose configuration..."
cat > docker-compose.yml << 'EOF'
version: '3.8'

services:
  zoekt:
    image: sourcegraph/zoekt-webserver:latest
    ports:
      - "6070:6070"
    volumes:
      - zoekt-index:/data
    environment:
      - GOGC=50

  postgres:
    image: postgres:15-alpine
    environment:
      - POSTGRES_DB=sourcebot
      - POSTGRES_USER=sourcebot
      - POSTGRES_PASSWORD=sourcebot
    volumes:
      - postgres-data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    volumes:
      - redis-data:/data

volumes:
  zoekt-index:
  postgres-data:
  redis-data:
EOF

# Create backend package.json
cd packages/backend
echo "Creating backend package.json..."
cat > package.json << 'EOF'
{
  "name": "@docxp/backend",
  "version": "1.0.0",
  "description": "DocXP Sourcebot Backend Services",
  "main": "dist/index.js",
  "scripts": {
    "dev": "tsx watch src/index.ts",
    "build": "tsc",
    "start": "node dist/index.js"
  },
  "dependencies": {
    "@apollo/server": "^4.9.5",
    "graphql": "^16.8.1",
    "express": "^4.18.2",
    "axios": "^1.6.2",
    "bullmq": "^5.1.0",
    "pg": "^8.11.3",
    "node-cron": "^3.0.3",
    "@google/generative-ai": "^0.1.3"
  },
  "devDependencies": {
    "@types/node": "^20.10.5",
    "typescript": "^5.3.3",
    "tsx": "^4.6.2"
  }
}
EOF

# Create TypeScript config
echo "Creating TypeScript configuration..."
cat > tsconfig.json << 'EOF'
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "commonjs",
    "lib": ["ES2022"],
    "outDir": "./dist",
    "rootDir": "./src",
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "forceConsistentCasingInFileNames": true,
    "resolveJsonModule": true,
    "moduleResolution": "node"
  },
  "include": ["src/**/*"],
  "exclude": ["node_modules", "dist"]
}
EOF

cd ../..

# Create README for the new structure
echo "Creating Sourcebot README..."
cat > README.md << 'EOF'
# DocXP Sourcebot Implementation

This is the new Sourcebot-based implementation of DocXP, combining:
- Lightning-fast code search using Zoekt
- AI-powered Q&A with Gemini
- Legacy DocXP documentation generation features

## Quick Start

1. Install dependencies:
   ```
   cd packages/backend
   npm install
   cd ../web
   npm install
   ```

2. Start services:
   ```
   docker-compose up -d
   ```

3. Start development servers:
   ```
   # Terminal 1 - Backend
   cd packages/backend
   npm run dev

   # Terminal 2 - Frontend
   cd packages/web
   npm run dev
   ```

4. Access the application:
   - Frontend: http://localhost:3000
   - GraphQL: http://localhost:4000/graphql
   - Zoekt: http://localhost:6070
EOF

cd ..

echo ""
echo "========================================"
echo "   Setup Complete!"
echo "========================================"
echo ""
echo "Next steps:"
echo "1. cd sourcebot"
echo "2. Install Go and Node.js dependencies"
echo "3. docker-compose up -d (to start services)"
echo "4. Begin implementing services as per roadmap"
echo ""
echo "The implementation roadmap has been saved to your artifacts."
echo ""
