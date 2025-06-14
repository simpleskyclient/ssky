#!/bin/bash

# Quick MCP Server Test Commands
# Simple one-liner commands for testing MCP server

IMAGE_NAME="ssky-mcp:local"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}🚀 Quick MCP Server Test Commands${NC}"
echo "=================================="
echo ""

# Function to run a command
run_test() {
    local name="$1"
    local message="$2"
    echo -e "${GREEN}$name:${NC}"
    echo "$message" | docker run -i --rm -e SSKY_USER="$SSKY_USER" "$IMAGE_NAME" | jq .
    echo ""
}

# Function to send multiple messages to the same container
send_mcp_session() {
    local messages="$1"
    local with_creds="$2"
    
    echo "Raw output:"
    if [ "$with_creds" = "true" ] && [ ! -z "$SSKY_USER" ]; then
        echo "$messages" | docker run -i --rm -e SSKY_USER="$SSKY_USER" "$IMAGE_NAME"
    else
        echo "$messages" | docker run -i --rm "$IMAGE_NAME"
    fi
    echo ""
    echo "Parsed with jq:"
    if [ "$with_creds" = "true" ] && [ ! -z "$SSKY_USER" ]; then
        echo "$messages" | docker run -i --rm -e SSKY_USER="$SSKY_USER" "$IMAGE_NAME" | jq -s '.'
    else
        echo "$messages" | docker run -i --rm "$IMAGE_NAME" | jq -s '.'
    fi
}

# Test 1: Initialize and List Tools
echo "1. Initialize + List Tools:"
INIT_AND_LIST='{"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2024-11-05", "capabilities": {"tools": {}}, "clientInfo": {"name": "test-client", "version": "1.0.0"}}}
{"jsonrpc": "2.0", "method": "notifications/initialized"}
{"jsonrpc": "2.0", "id": 2, "method": "tools/list"}'

echo "Messages to send:"
echo "$INIT_AND_LIST"
echo ""

send_mcp_session "$INIT_AND_LIST" "false"
echo ""

# Test 2: Initialize and ssky_get with count=1
if [ ! -z "$SSKY_USER" ]; then
    echo "2. Initialize + ssky_get (count=1):"
    INIT_AND_GET='{"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2024-11-05", "capabilities": {"tools": {}}, "clientInfo": {"name": "test-client", "version": "1.0.0"}}}
{"jsonrpc": "2.0", "method": "notifications/initialized"}
{"jsonrpc": "2.0", "id": 2, "method": "tools/call", "params": {"name": "ssky_get", "arguments": {"limit": 1}}}'
    
    echo "Messages to send:"
    echo "$INIT_AND_GET"
    echo ""
    
    send_mcp_session "$INIT_AND_GET" "true"
    echo ""
else
    echo "2. Initialize + ssky_get (no credentials - will show error):"
    INIT_AND_GET_NO_CREDS='{"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2024-11-05", "capabilities": {"tools": {}}, "clientInfo": {"name": "test-client", "version": "1.0.0"}}}
{"jsonrpc": "2.0", "method": "notifications/initialized"}
{"jsonrpc": "2.0", "id": 2, "method": "tools/call", "params": {"name": "ssky_get", "arguments": {"limit": 1}}}'
    
    echo "Messages to send:"
    echo "$INIT_AND_GET_NO_CREDS"
    echo ""
    
    send_mcp_session "$INIT_AND_GET_NO_CREDS" "false"
    echo ""
fi

echo "💡 Manual commands you can run:"
echo ""
echo "# Initialize + List tools:"
echo 'cat << EOF | docker run -i --rm ssky-mcp:local | jq -s "."'
echo '{"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2024-11-05", "capabilities": {"tools": {}}, "clientInfo": {"name": "test-client", "version": "1.0.0"}}}'
echo '{"jsonrpc": "2.0", "method": "notifications/initialized"}'
echo '{"jsonrpc": "2.0", "id": 2, "method": "tools/list"}'
echo 'EOF'
echo ""
echo "# Initialize + Get 1 post (with credentials):"
echo 'cat << EOF | docker run -i --rm -e SSKY_USER="$SSKY_USER" ssky-mcp:local | jq -s "."'
echo '{"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2024-11-05", "capabilities": {"tools": {}}, "clientInfo": {"name": "test-client", "version": "1.0.0"}}}'
echo '{"jsonrpc": "2.0", "method": "notifications/initialized"}'
echo '{"jsonrpc": "2.0", "id": 2, "method": "tools/call", "params": {"name": "ssky_get", "arguments": {"limit": 1}}}'
echo 'EOF' 