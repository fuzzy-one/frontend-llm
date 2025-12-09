#!/bin/bash

# 1. Start the Backend (Docker)
if [ -f "docker-compose.api.yml" ]; then
    echo "🐳 Starting Backend (Search API)..."
    docker compose -f docker-compose.api.yml up -d search-api
else
    echo "⚠️  docker-compose.api.yml not found, skipping backend start."
fi

# 2. Load NVM (Node Version Manager)
export NVM_DIR="$HOME/.config/nvm"
if [ -s "$NVM_DIR/nvm.sh" ]; then
    . "$NVM_DIR/nvm.sh"
    echo "✅ NVM loaded: $(node -v)"
else
    echo "❌ Error: nvm not found at $NVM_DIR"
    echo "Please ensure nvm is installed."
    exit 1
fi

# 3. Navigate to Frontend Directory
FRONTEND_DIR="frontend-repo/fe"
if [ -d "$FRONTEND_DIR" ]; then
    cd "$FRONTEND_DIR" || exit
else
    echo "❌ Error: Frontend directory '$FRONTEND_DIR' not found."
    exit 1
fi

# 4. Start Frontend Applications
echo "🚀 Starting Frontend Microfrontends..."
npm run run:all
