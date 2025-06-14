#!/bin/bash

# MCP Server Test Script
# Tests the ssky MCP server with sample commands

set -e

# Configuration
IMAGE_NAME="ssky-mcp:local"
CONTAINER_NAME="ssky-mcp-test"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_step() {
    echo -e "${BLUE}📋 $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check if Docker image exists
print_step "Checking if Docker image exists..."
if ! docker image inspect "$IMAGE_NAME" >/dev/null 2>&1; then
    print_error "Docker image '$IMAGE_NAME' not found!"
    echo "Please build the image first:"
    echo "  ./build.sh --local"
    exit 1
fi
print_success "Docker image found: $IMAGE_NAME"

# Check if SSKY_USER is set
if [ -z "$SSKY_USER" ]; then
    print_warning "SSKY_USER environment variable is not set"
    echo "Some tests may fail without Bluesky credentials"
    echo "Set it like: export SSKY_USER='your-handle.bsky.social:your-password'"
    echo ""
fi

echo "🧪 Starting MCP Server Tests"
echo "========================================"
echo ""

# Create a temporary file for the test session
TEMP_INPUT=$(mktemp)
TEMP_OUTPUT=$(mktemp)

# Cleanup function
cleanup() {
    rm -f "$TEMP_INPUT" "$TEMP_OUTPUT"
}
trap cleanup EXIT

# Define test messages with descriptions
declare -a TEST_DESCRIPTIONS=(
    "Initialize MCP Server"
    "Send initialized notification"
    "List available tools"
    "Call ssky_get tool"
)

# Define the actual messages for display
declare -a TEST_MESSAGES=(
    '{"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2024-11-05", "capabilities": {"tools": {}}, "clientInfo": {"name": "test-client", "version": "1.0.0"}}}'
    '{"jsonrpc": "2.0", "method": "notifications/initialized"}'
    '{"jsonrpc": "2.0", "id": 2, "method": "tools/list"}'
    '{"jsonrpc": "2.0", "id": 3, "method": "tools/call", "params": {"name": "ssky_get", "arguments": {"limit": 1}}}'
)

# Prepare all MCP messages
cat > "$TEMP_INPUT" << 'EOF'
{"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2024-11-05", "capabilities": {"tools": {}}, "clientInfo": {"name": "test-client", "version": "1.0.0"}}}
{"jsonrpc": "2.0", "method": "notifications/initialized"}
{"jsonrpc": "2.0", "id": 2, "method": "tools/list"}
{"jsonrpc": "2.0", "id": 3, "method": "tools/call", "params": {"name": "ssky_get", "arguments": {"limit": 1}}}
EOF

print_step "Running MCP session with multiple requests..."
echo "Test sequence:"
for i in "${!TEST_DESCRIPTIONS[@]}"; do
    echo "$((i + 1)). ${TEST_DESCRIPTIONS[$i]}"
done
echo ""

# Run the MCP server with all messages
print_step "Starting Docker container and sending requests..."
if [ ! -z "$SSKY_USER" ]; then
    docker run -i --rm -e SSKY_USER="$SSKY_USER" "$IMAGE_NAME" < "$TEMP_INPUT" > "$TEMP_OUTPUT" 2>&1
else
    docker run -i --rm "$IMAGE_NAME" < "$TEMP_INPUT" > "$TEMP_OUTPUT" 2>&1
fi

print_step "Processing responses..."
echo ""

# Helper function to display test result
display_test_result() {
    local response_id="$1"
    local response_json="$2"
    
    # Map response ID to test number and description
    local test_num description request_msg
    case $response_id in
        1) test_num=1; description="${TEST_DESCRIPTIONS[0]}"; request_msg="${TEST_MESSAGES[0]}" ;;
        2) test_num=3; description="${TEST_DESCRIPTIONS[2]}"; request_msg="${TEST_MESSAGES[2]}" ;;
        3) test_num=4; description="${TEST_DESCRIPTIONS[3]}"; request_msg="${TEST_MESSAGES[3]}" ;;
        *) test_num="?"; description="Unknown request (ID: $response_id)"; request_msg="" ;;
    esac
    
    echo "📋 Test $test_num: $description"
    
    if [[ -n "$request_msg" ]]; then
        echo "Request:"
        echo "$request_msg" | jq .
        echo ""
    fi
    
    echo "Response:"
    echo "$response_json" | jq . 2>/dev/null || echo "$response_json"
    echo "----------------------------------------"
    echo ""
}

# Helper function to display notification status
display_notification_status() {
    echo "📋 Test 2: ${TEST_DESCRIPTIONS[1]}"
    echo "Request:"
    echo "${TEST_MESSAGES[1]}" | jq .
    echo ""
    echo "Status: ✅ Notification sent successfully (no response expected)"
    echo "----------------------------------------"
    echo ""
}

# Parse and display responses
response_count=0
notification_sent=false

while IFS= read -r line; do
    if [[ "$line" =~ ^\{.*\}$ ]]; then
        # JSON response found
        response_count=$((response_count + 1))
        
        if echo "$line" | jq -e '.id' >/dev/null 2>&1; then
            # Response with ID
            response_id=$(echo "$line" | jq -r '.id')
            display_test_result "$response_id" "$line"
            
            # Show notification status after Test 1
            if [[ "$response_id" == "1" && "$notification_sent" == false ]]; then
                display_notification_status
                notification_sent=true
            fi
        else
            # Response without ID (shouldn't happen in our test)
            echo "📋 Unexpected response without ID"
            echo "Response:"
            echo "$line" | jq . 2>/dev/null || echo "$line"
            echo "----------------------------------------"
            echo ""
        fi
    elif [[ -n "$line" ]]; then
        # Non-JSON output (server logs)
        echo "Server output: $line"
    fi
done < "$TEMP_OUTPUT"

# If we didn't get any responses, still show notification status
if [[ $response_count -eq 0 && "$notification_sent" == false ]]; then
    display_notification_status
fi

if [ $response_count -eq 0 ]; then
    print_error "No JSON responses received!"
    echo "Raw output:"
    cat "$TEMP_OUTPUT"
    echo ""
    
    print_step "Testing basic Docker connectivity..."
    echo "Testing if container starts:"
    if docker run --rm "$IMAGE_NAME" --help >/dev/null 2>&1; then
        print_success "Container starts successfully"
    else
        print_error "Container fails to start"
    fi
    
    print_step "Testing simple echo through container..."
    echo '{"test": "message"}' | docker run -i --rm "$IMAGE_NAME" || true
else
    print_success "Received $response_count JSON responses"
fi

print_success "Test completed!"
echo ""
echo "💡 Tips:"
echo "- Set SSKY_USER environment variable to test with real data"
echo "- Check server logs above for any error messages"
echo "- Each response should be a valid JSON-RPC message" 