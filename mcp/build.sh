#!/bin/bash

# Ssky MCP Docker Build Script

set -e

# Parse command line arguments
LOCAL_BUILD=false
DOCKERFILE="Dockerfile"
IMAGE_TAG="ssky-mcp:latest"

while [[ $# -gt 0 ]]; do
    case $1 in
        --local)
            LOCAL_BUILD=true
            DOCKERFILE="Dockerfile.dev"
            IMAGE_TAG="ssky-mcp:local"
            shift
            ;;
        -h|--help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --local    Build from local source instead of PyPI"
            echo "  -h, --help Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0                # Build from PyPI (default)"
            echo "  $0 --local        # Build from local source"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use -h or --help for usage information"
            exit 1
            ;;
    esac
done

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

if [ "$LOCAL_BUILD" = true ]; then
    echo "🐳 Building ssky MCP Docker image from local source..."
    echo "   Using Dockerfile: $DOCKERFILE"
    echo "   Image tag: $IMAGE_TAG"
    
    # Check if we're in the mcp directory and need to go up one level
    if [ -f "../pyproject.toml" ]; then
        echo "   Building from parent directory context..."
        cd ..
        docker build -f mcp/$DOCKERFILE -t $IMAGE_TAG .
        cd mcp
    else
        echo "❌ Error: Cannot find pyproject.toml in parent directory"
        echo "   Please run this script from the mcp/ directory"
        exit 1
    fi
else
    echo "🐳 Building ssky MCP Docker image from PyPI..."
    echo "   Using Dockerfile: $DOCKERFILE"
    echo "   Image tag: $IMAGE_TAG"
    
    # Build Docker image
    docker build -f $DOCKERFILE -t $IMAGE_TAG .
fi

echo "✅ Build completed successfully!"

# Health check test
echo "🔍 Running health check..."
docker run --rm $IMAGE_TAG /app/healthcheck.sh

echo "✅ Health check passed!"

# Basic functionality test (if credentials are available)
if [ ! -z "$SSKY_USER" ]; then
    echo "🧪 Running basic functionality test..."
    echo '{"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2024-11-05", "capabilities": {"tools": {}}, "clientInfo": {"name": "test-client", "version": "1.0.0"}}}' | \
    docker run -i --rm -e SSKY_USER="$SSKY_USER" $IMAGE_TAG | \
    head -1 | grep -q "jsonrpc" && echo "✅ MCP protocol test passed!" || echo "❌ MCP protocol test failed"
else
    echo "⚠️  Skipping functionality test (SSKY_USER not set)"
    echo "   To run full tests, set your Bluesky credentials:"
    echo "   export SSKY_USER='your-handle.bsky.social:your-password'"
fi

echo ""
echo "🎉 Build and test completed!"
echo ""
echo "Built image: $IMAGE_TAG"
echo ""
echo "Next steps:"
if [ "$LOCAL_BUILD" = true ]; then
    echo "1. Update your .cursor/mcp.json to use the local Docker image: $IMAGE_TAG"
    echo "2. Make sure your SSKY_USER environment variable is set"
    echo "3. Restart Cursor to reload MCP configuration"
    echo ""
    echo "Note: This image was built from your local source code changes."
else
    echo "1. Update your .cursor/mcp.json to use the Docker image: $IMAGE_TAG"
    echo "2. Make sure your SSKY_USER environment variable is set"
    echo "3. Restart Cursor to reload MCP configuration"
fi 