# Ssky MCP Server

MCP (Model Context Protocol) server for the ssky Bluesky client.

## Building Docker Images

This directory contains scripts and Dockerfiles for building the ssky MCP server as a Docker image.

### Build Options

#### 1. Build from PyPI (Default)

Builds the Docker image using the published ssky package from PyPI:

```bash
./build.sh
```

This creates the image `ssky-mcp:latest` using `Dockerfile`.

#### 2. Build from Local Source

Builds the Docker image using your local source code changes:

```bash
./build.sh --local
```

This creates the image `ssky-mcp:local` using `Dockerfile.dev`.

**Use this option when:**
- Testing local changes before publishing
- Developing new features
- Debugging issues with your modifications

### Usage Examples

```bash
# Build from PyPI (production)
./build.sh

# Build from local source (development)
./build.sh --local

# Show help
./build.sh --help
```

### Docker Images

- **`ssky-mcp:latest`**: Built from PyPI package (stable)
- **`ssky-mcp:local`**: Built from local source (development)

### Files

- `Dockerfile`: Builds from PyPI package
- `Dockerfile.dev`: Builds from local source code
- `build.sh`: Build script with options
- `ssky_server.py`: MCP server implementation

### Testing Local Changes

1. Make your changes to the ssky source code
2. Build the local Docker image:
   ```bash
   ./build.sh --local
   ```
3. Update your `.cursor/mcp.json` to use `ssky-mcp:local`
4. Restart Cursor to test your changes

### Environment Variables

- `SSKY_USER`: Your Bluesky credentials in format `handle:password`

### Testing the MCP Server

#### Comprehensive Tests

Run the full test suite:

```bash
./test_mcp_full.sh
```

This will test:
- MCP server initialization
- List available tools
- Call ssky_get tool (with and without credentials)
- Error handling

#### Quick Tests

Run quick tests with immediate results:

```bash
./test_mcp_quick.sh
```

#### Manual Commands

You can also test individual commands manually:

```bash
# Initialize + List all available tools
cat << EOF | docker run -i --rm ssky-mcp:local | jq -s "."
{"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2024-11-05", "capabilities": {"tools": {}}, "clientInfo": {"name": "test-client", "version": "1.0.0"}}}
{"jsonrpc": "2.0", "method": "notifications/initialized"}
{"jsonrpc": "2.0", "id": 2, "method": "tools/list"}
EOF

# Initialize + Get 1 post from timeline (requires SSKY_USER)
cat << EOF | docker run -i --rm -e SSKY_USER="$SSKY_USER" ssky-mcp:local | jq -s "."
{"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2024-11-05", "capabilities": {"tools": {}}, "clientInfo": {"name": "test-client", "version": "1.0.0"}}}
{"jsonrpc": "2.0", "method": "notifications/initialized"}
{"jsonrpc": "2.0", "id": 2, "method": "tools/call", "params": {"name": "ssky_get", "arguments": {"count": "1"}}}
EOF

# Initialize + Search for posts
cat << EOF | docker run -i --rm -e SSKY_USER="$SSKY_USER" ssky-mcp:local | jq -s "."
{"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2024-11-05", "capabilities": {"tools": {}}, "clientInfo": {"name": "test-client", "version": "1.0.0"}}}
{"jsonrpc": "2.0", "method": "notifications/initialized"}
{"jsonrpc": "2.0", "id": 3, "method": "tools/call", "params": {"name": "ssky_search", "arguments": {"query": "bluesky", "count": "2"}}}
EOF
```

### Health Check

Both Docker images include health checks to verify:
- ssky package is available
- MCP dependencies are installed
- Basic functionality works 