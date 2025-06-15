#!/bin/bash

# Sutra Local Development Setup Script
echo "🚀 Setting up Sutra local development environment..."

# Check prerequisites
echo "📋 Checking prerequisites..."

if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install Node.js 18+ first."
    exit 1
fi

if ! command -v python3 &> /dev/null; then
    echo "❌ Python is not installed. Please install Python 3.12+ first."
    exit 1
fi

if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

if ! command -v func &> /dev/null; then
    echo "❌ Azure Functions Core Tools not found. Installing..."
    npm install -g azure-functions-core-tools@4 --unsafe-perm true
fi

echo "✅ Prerequisites check completed"

# Install frontend dependencies
echo "📦 Installing frontend dependencies..."
npm install

# Set up API local settings
echo "🔧 Setting up API configuration..."
if [ ! -f "api/local.settings.json" ]; then
    cp api/local.settings.json.example api/local.settings.json
    echo "✅ Created api/local.settings.json from example"
else
    echo "ℹ️  api/local.settings.json already exists"
fi

# Install API dependencies
echo "📦 Installing API dependencies..."
cd api
python3 -m pip install -r requirements.txt
cd ..

# Create environment file for frontend
echo "🔧 Creating frontend environment file..."
if [ ! -f ".env.local" ]; then
    cat > .env.local << EOL
VITE_API_BASE_URL=http://localhost:7071/api
VITE_APP_TITLE=Sutra - AI Operations Platform
VITE_APP_VERSION=1.0.0
EOL
    echo "✅ Created .env.local"
else
    echo "ℹ️  .env.local already exists"
fi

# Install Playwright browsers
echo "🎭 Installing Playwright browsers..."
npx playwright install

echo ""
echo "🎉 Local development environment setup completed!"
echo ""
echo "📚 Next steps:"
echo "1. Start local services: npm run dev:local"
echo "2. Run tests: npm run test:e2e"
echo "3. Open http://localhost:3000 in your browser"
echo ""
echo "🔗 Useful local URLs:"
echo "   Frontend: http://localhost:3000"
echo "   API: http://localhost:7071"
echo "   Cosmos DB Emulator: https://localhost:8081/_explorer/index.html"
echo "   Azurite Storage: http://localhost:10000"
