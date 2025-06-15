#!/bin/bash

# Sutra Docker Compose Health Check Script
echo "🔍 Checking local development services..."

# Check Cosmos DB Emulator
echo "📊 Checking Cosmos DB Emulator..."
curl -k -s https://localhost:8081/_explorer/index.html > /dev/null
if [ $? -eq 0 ]; then
    echo "✅ Cosmos DB Emulator is running"
else
    echo "❌ Cosmos DB Emulator is not accessible"
fi

# Check Azurite Storage
echo "💾 Checking Azurite Storage..."
curl -s http://localhost:10000 > /dev/null
if [ $? -eq 0 ]; then
    echo "✅ Azurite Storage is running"
else
    echo "❌ Azurite Storage is not accessible"
fi

# Check Azure Functions API
echo "🔌 Checking Azure Functions API..."
curl -s http://localhost:7071 > /dev/null
if [ $? -eq 0 ]; then
    echo "✅ Azure Functions API is running"
else
    echo "❌ Azure Functions API is not accessible"
fi

echo ""
echo "🎯 Health check completed!"
