# Ssky MCP Tools for Cursor Agent

This directory contains MCP (Model Context Protocol) tools that enable Cursor agent to interact with Bluesky using the `ssky` command-line client.

## Overview

The MCP server provides **10 comprehensive tools** for Bluesky interaction:
- 📋 **Content Retrieval**: Get posts, search posts/users, view profiles
- ✍️ **Content Creation**: Post with images/quotes/replies
- 🤝 **Social Actions**: Follow, unfollow, repost, unrepost
- 🗑️ **Content Management**: Delete posts

## Setup

### 1. Requirements
Before starting, ensure you have the following installed:

#### Docker
Docker is required to run the MCP server. Install Docker for your platform:
- **Linux**: Follow the [official Docker installation guide](https://docs.docker.com/engine/install/)
- **macOS**: Download [Docker Desktop for Mac](https://docs.docker.com/desktop/install/mac-install/)
- **Windows**: Download [Docker Desktop for Windows](https://docs.docker.com/desktop/install/windows-install/)

After installation, verify Docker is running:
```bash
docker --version
docker info
```

#### Python Package
Ensure the `ssky` package is installed and available in your PATH:
```bash
pip install ssky
```

### 2. Configure Bluesky Authentication
Set up your Bluesky credentials using one of these methods:

#### Option A: Login Command
```bash
ssky login your-handle.bsky.social:your-password
```

#### Option B: Environment Variable
```bash
export SSKY_USER=your-handle.bsky.social:your-password
```

#### Option C: .env file
Create a `.env` file in your project root:
```
SSKY_USER=your-handle.bsky.social:your-password
```

### 3. Configure Cursor

#### Option A: Quick Setup (Recommended - No build required)
If you don't have an existing `.cursor/mcp.json` file, this is the simplest approach using the pre-built Docker image:

1. **Copy the sample configuration:**
   ```bash
   # Create .cursor directory if it doesn't exist
   mkdir -p .cursor
   
   # Copy sample as your MCP configuration
   cp mcp/mcp.sample.json .cursor/mcp.json
   ```

2. **Restart Cursor** to load the MCP tools

✅ **That's it!** Docker will automatically pull the pre-built image (`ghcr.io/simpleskyclient/ssky-mcp:latest`) when first used.

💡 **Note:** The first use may take a moment for Docker to pull the image (~276MB).

**Available Docker Images:**
- `ghcr.io/simpleskyclient/ssky-mcp:latest` - Latest stable version (auto-built from main branch)
- `ghcr.io/simpleskyclient/ssky-mcp:v0.1.2` - Specific version (auto-built from tags)
- **Source**: [GitHub Container Registry](https://github.com/simpleskyclient/ssky-mcp/pkgs/container/ssky-mcp)
- **CI/CD**: Automatically built via [GitHub Actions](https://github.com/simpleskyclient/ssky/actions)

#### Option B: Add to Existing MCP Configuration
If you already have `.cursor/mcp.json` with other MCP servers (e.g., GitHub):

1. **Back up your existing configuration:**
   ```bash
   cp .cursor/mcp.json .cursor/mcp.json.backup
   ```

2. **Add the ssky server to your `.cursor/mcp.json`:**
   
   Open `.cursor/mcp.json` in your editor and add the `"ssky"` section inside `"mcpServers"`:
   ```json
   {
       "mcpServers": {
           "your-existing-server": {
               // ... your existing configuration
           },
           "ssky": {
               "command": "docker",
               "args": [
                   "run",
                   "-i",
                   "--rm",
                   "-e",
                   "SSKY_USER",
                   "ghcr.io/simpleskyclient/ssky-mcp:latest"
               ]
           }
       }
   }
   ```
   
   💡 **Tip:** You can copy the exact configuration from `mcp/mcp.sample.json`

3. **Restart Cursor** to reload the configuration

#### Option C: Local Build (For Developers)
If you prefer to build the Docker image locally or need to modify the MCP server:

1. **Build the Docker image:**
   ```bash
   cd mcp
   ./build.sh
   cd ..
   ```
   
   The script will:
   - Check Docker requirements
   - Build the Docker image (`ssky-mcp:latest`)
   - Run health checks
   - Test MCP protocol compatibility

2. **Update the sample configuration for local image:**
   ```bash
   # Create .cursor directory if it doesn't exist
   mkdir -p .cursor
   
   # Copy and modify for local image
   sed 's|ghcr.io/simpleskyclient/ssky-mcp:latest|ssky-mcp:latest|' mcp/mcp.sample.json > .cursor/mcp.json
   ```

3. **Restart Cursor** to load the MCP tools

**Notes:**
- Use this option if you want to customize the MCP server
- Local builds use the tag `ssky-mcp:latest`
- Make sure your `SSKY_USER` environment variable is set before testing

## Available Tools

### Content Retrieval Tools

#### 1. `ssky_get`
Get posts from Bluesky timeline or specific user.

**Parameters:**
- `param` (optional): Target to get posts from
  - Empty: Your timeline
  - Handle: `user.bsky.social`
  - DID: `did:plc:...`
  - URI: `at://...`
  - Special: `"myself"` for your own posts
- `limit` (optional): Maximum number of posts (default: 25)
- `output_format` (optional): Output format (default: "long" for AI readability)
  - `"long"`: Detailed format with metadata
  - `"text"`: Text content only
  - `"json"`: JSON format
  - `"id"`: IDs only
- `delimiter` (optional): Custom delimiter string
- `output_dir` (optional): Output to files in specified directory

**Examples:**
```python
# Get your timeline (default)
ssky_get()

# Get specific user's posts in detail
ssky_get(param="user.bsky.social", limit=10)

# Get your own posts
ssky_get(param="myself", limit=5)

# Get specific post by URI
ssky_get(param="at://did:plc:.../app.bsky.feed.post/...")
```

#### 2. `ssky_search`
Search posts on Bluesky.

**Parameters:**
- `query` (required): Search query string
- `limit` (optional): Maximum number of results (default: 25)
- `author` (optional): Filter by author handle or DID
- `since` (optional): Since timestamp (ex. "2001-01-01T00:00:00Z")
- `until` (optional): Until timestamp (ex. "2099-12-31T23:59:59Z")
- `output_format` (optional): Output format (default: "long")
- `delimiter` (optional): Custom delimiter string
- `output_dir` (optional): Output to files in specified directory

**Examples:**
```python
# Search for posts containing "bluesky"
ssky_search(query="bluesky")

# Search your own posts about specific topic
ssky_search(query="LLM", author="myself")

# Search with date range
ssky_search(query="AI", since="2024-01-01T00:00:00Z", limit=10)
```

#### 3. `ssky_user`
Search users on Bluesky.

**Parameters:**
- `query` (required): Search query for users
- `limit` (optional): Maximum number of results (default: 25)
- `output_format` (optional): Output format (default: "long")
- `delimiter` (optional): Custom delimiter string
- `output_dir` (optional): Output to files in specified directory

**Examples:**
```python
# Search for users
ssky_user(query="researcher")

# Get detailed user information
ssky_user(query="AI expert", output_format="long")
```

#### 4. `ssky_profile`
Show user profile information.

**Parameters:**
- `handle` (required): User handle or DID
- `output_format` (optional): Output format (default: "long")
- `delimiter` (optional): Custom delimiter string
- `output_dir` (optional): Output to files in specified directory

**Examples:**
```python
# Get user profile
ssky_profile(handle="user.bsky.social")

# Get profile in JSON format
ssky_profile(handle="user.bsky.social", output_format="json")
```

### Content Creation Tools

#### 5. `ssky_post`
Post a message to Bluesky.

**Parameters:**
- `message` (optional): The message to post
- `dry_run` (optional): If true, shows what would be posted without posting
- `images` (optional): Comma-separated list of image file paths
- `quote_uri` (optional): URI of post to quote (at://...)
- `reply_to_uri` (optional): URI of post to reply to (at://...)
- `output_format` (optional): Output format (default: "text")
- `delimiter` (optional): Custom delimiter string
- `output_dir` (optional): Output to files in specified directory

**Examples:**
```python
# Simple post
ssky_post(message="Hello, Bluesky!")

# Post with images
ssky_post(message="Check out these photos!", images="/path/to/photo1.jpg,/path/to/photo2.jpg")

# Reply to a post
ssky_post(message="Great post!", reply_to_uri="at://did:plc:.../app.bsky.feed.post/...")

# Quote a post
ssky_post(message="Interesting perspective!", quote_uri="at://did:plc:.../app.bsky.feed.post/...")

# Dry run (preview without posting)
ssky_post(message="Test message", dry_run=True)
```

### Social Action Tools

#### 6. `ssky_follow`
Follow a user on Bluesky.

**Parameters:**
- `handle` (required): User handle or DID to follow
- `output_format` (optional): Output format (default: "text")
- `delimiter` (optional): Custom delimiter string
- `output_dir` (optional): Output to files in specified directory

#### 7. `ssky_unfollow`
Unfollow a user on Bluesky.

**Parameters:**
- `handle` (required): User handle or DID to unfollow
- `output_format` (optional): Output format (default: "text")
- `delimiter` (optional): Custom delimiter string
- `output_dir` (optional): Output to files in specified directory

#### 8. `ssky_repost`
Repost a post on Bluesky.

**Parameters:**
- `post_uri` (required): URI of the post to repost (at://...)
- `output_format` (optional): Output format (default: "text")
- `delimiter` (optional): Custom delimiter string
- `output_dir` (optional): Output to files in specified directory

#### 9. `ssky_unrepost`
Remove a repost on Bluesky.

**Parameters:**
- `post_uri` (required): URI of the post to unrepost (at://...)
- `output_format` (optional): Output format (default: "text")
- `delimiter` (optional): Custom delimiter string
- `output_dir` (optional): Output to files in specified directory

### Content Management Tools

#### 10. `ssky_delete`
Delete a post on Bluesky.

**Parameters:**
- `post_uri` (required): URI of the post to delete (at://...)

**Example:**
```python
# Delete a specific post
ssky_delete(post_uri="at://did:plc:.../app.bsky.feed.post/...")
```

## Key Features

### AI-Optimized Defaults
- **Long format default**: Content retrieval tools default to "long" format for better AI understanding
- **Comprehensive metadata**: Detailed information including timestamps, DIDs, and URIs
- **Structured output**: Consistent formatting across all tools

### Message Features
When posting messages, `ssky` automatically detects and handles:
- **Mentions**: `@username.bsky.social`
- **Hashtags**: `#bluesky #socialmedia`
- **Links**: `https://example.com` (automatically creates link cards)

### Flexible Output
All tools support multiple output formats:
- `"long"`: Detailed format with full metadata (default for retrieval)
- `"text"`: Clean text content only
- `"json"`: Structured JSON format
- `"id"`: IDs only for efficient processing

## Example Workflows

### Content Research
```python
# Search for recent posts about a topic
posts = ssky_search(query="government", author="myself")

# Get detailed information about a specific post
detail = ssky_get(param="at://did:plc:.../app.bsky.feed.post/...")

# Find users discussing the topic
users = ssky_user(query="transportation policy")
```

### Social Engagement
```python
# Follow interesting users found in search
ssky_follow(handle="researcher.bsky.social")

# Repost interesting content
ssky_repost(post_uri="at://did:plc:.../app.bsky.feed.post/...")

# Reply to discussions
ssky_post(
    message="Thanks for sharing this research!",
    reply_to_uri="at://did:plc:.../app.bsky.feed.post/..."
)
```

### Content Creation
```python
# Draft a post (dry run first)
draft = ssky_post(
    message="Excited about new developments in public transportation! #policy", 
    dry_run=True
)

# Post with image
ssky_post(
    message="New research findings on mobility solutions",
    images="/path/to/chart.png"
)

# Quote an interesting post with commentary
ssky_post(
    message="This aligns with our recent findings on urban mobility",
    quote_uri="at://did:plc:.../app.bsky.feed.post/..."
)
```

## Security Notes

- Never commit your Bluesky credentials to version control
- Use environment variables or the `ssky login` command for authentication
- The `dry_run` option is useful for testing posts before publishing
- Social actions (follow, repost) are immediately executed - use with care

## Troubleshooting

1. **Docker not found**: Ensure Docker is installed and running
   - Install Docker from [official website](https://docs.docker.com/get-docker/)
   - Start Docker service: `sudo systemctl start docker` (Linux) or start Docker Desktop
   - Verify: `docker --version` and `docker info`

2. **Command not found**: Ensure `ssky` is installed and in your PATH
   - Install: `pip install ssky`
   - Verify: `ssky --help`

3. **Authentication failed**: Check your credentials and network connection
   - Verify credentials: `ssky login your-handle.bsky.social:your-password`
   - Check environment variable: `echo $SSKY_USER`

4. **Docker build failed**: Check Docker daemon and permissions
   - Ensure Docker daemon is running
   - Check user permissions for Docker (may need `sudo` or add user to docker group)

5. **Permission denied**: Ensure proper file permissions
   - Make build script executable: `chmod +x mcp/build.sh`

6. **Timeout errors**: Operations have a 30-second timeout; network issues may cause delays

7. **MCP connection issues**: Restart Cursor to reload the MCP server configuration
   - Verify Docker image exists: `docker images | grep ssky-mcp`
   - Check `.cursor/mcp.json` configuration format

## Advanced Usage

### Batch Operations
```python
# Get multiple users' profiles
profiles = [
    ssky_profile(handle="user1.bsky.social"),
    ssky_profile(handle="user2.bsky.social"),
    ssky_profile(handle="user3.bsky.social")
]

# Search multiple topics
topics = ["AI", "climate", "technology"]
results = [ssky_search(query=topic, limit=5) for topic in topics]
```

### Output Management
```python
# Save timeline to files
ssky_get(output_dir="./timeline_backup", limit=100)

# Custom delimiter for CSV processing
data = ssky_search(query="data science", delimiter=",", output_format="text")
```

This comprehensive toolset enables rich interaction with Bluesky directly from Cursor, supporting both automated workflows and interactive social media management. 