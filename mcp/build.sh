#!/bin/bash

# Ssky MCP Docker Build Script

set -e

# Requirements check
echo "📋 Checking requirements..."

# Check if Docker is installed and running
if ! command -v docker &> /dev/null; then
    echo "❌ Error: Docker is not installed or not in PATH"
    echo "   Please install Docker first: https://docs.docker.com/get-docker/"
    exit 1
fi

if ! docker info &> /dev/null; then
    echo "❌ Error: Docker daemon is not running"
    echo "   Please start Docker service first"
    exit 1
fi

echo "✅ Docker is available and running"

echo "🐳 Building ssky MCP Docker image..."

# Build Docker image
docker build -t ssky-mcp:latest .

echo "✅ Build completed successfully!"

# Health check test
echo "🔍 Running health check..."
docker run --rm ssky-mcp:latest /app/healthcheck.sh

echo "✅ Health check passed!"

# Basic functionality test (if credentials are available)
if [ ! -z "$SSKY_USER" ]; then
    echo "🧪 Running basic functionality test..."
    echo '{"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2024-11-05", "capabilities": {"tools": {}}, "clientInfo": {"name": "test-client", "version": "1.0.0"}}}' | \
    docker run -i --rm -e SSKY_USER="$SSKY_USER" ssky-mcp:latest | \
    head -1 | grep -q "jsonrpc" && echo "✅ MCP protocol test passed!" || echo "❌ MCP protocol test failed"
else
    echo "⚠️  Skipping functionality test (SSKY_USER not set)"
    echo "   To run full tests, set your Bluesky credentials:"
    echo "   export SSKY_USER='your-handle.bsky.social:your-password'"
fi

echo ""
echo "🎉 Build and test completed!"
echo ""
echo "Next steps:"
echo "1. Update your .cursor/mcp.json to use the Docker image"
echo "2. Make sure your SSKY_USER environment variable is set"
echo "3. Restart Cursor to reload MCP configuration" 