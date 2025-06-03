# 🐦 ssky - Simple Bluesky Client

A lightweight, command-line Bluesky client that makes it easy to interact with the Bluesky social network from your terminal.

## ✨ Features

- 🔑 Simple authentication and session management
- 📝 Post, reply, quote, and repost content
- 🔍 Search posts and users
- 👥 Follow/unfollow users
- 📊 View timelines and profiles
- 🖼️ Support for images and link cards
- 📦 Linux shell friendly output formats

## 🚀 Quick Start

### Installation

```bash
pip install ssky
```

### Login

```bash
ssky login your-handle.bsky.social:your-password
```

Or set credentials via environment variable:
```bash
export SSKY_USER=your-handle.bsky.social:your-password
```

## 📖 Basic Usage

### Posting

```bash
# Simple post
ssky post "Hello, Bluesky!"

# Post with images
ssky post "Check out these photos!" --image photo1.jpg --image photo2.jpg

# Reply to a post
ssky post "Great post!" --reply-to at://did:plc:.../app.bsky.feed.post/...

# Quote a post
ssky post "Interesting!" --quote at://did:plc:.../app.bsky.feed.post/...
```

### Reading

```bash
# View your timeline
ssky get

# View someone's profile
ssky profile user.bsky.social

# Search posts
ssky search "keyword"

# Search users
ssky user "username"
```

### Social Actions

```bash
# Follow a user
ssky follow user.bsky.social

# Repost a post
ssky repost at://did:plc:.../app.bsky.feed.post/...

# Delete a post
ssky delete at://did:plc:.../app.bsky.feed.post/...
```

## 🔧 Advanced Usage

### Output Formats

```bash
# Get only post IDs
ssky get --id

# Get only text content
ssky get --text

# Get full JSON output
ssky get --json

# Save posts to files
ssky get --output ./posts
```

### Useful Examples

```bash
# Reply to your last post
ssky post "Update!" --reply-to $(ssky get myself --limit 1 --id)

# Search your own posts
ssky search "keyword" --author myself

# Save your timeline to files
ssky get --output ./timeline
```

## 🤖 IDE Integration

### Cursor Agent MCP Tools

`ssky` provides comprehensive MCP (Model Context Protocol) tools for seamless integration with Cursor Agent, enabling AI-powered Bluesky interactions directly in your development environment.

**Features:**
- 📋 **10 comprehensive tools**: Complete Bluesky functionality
- 🤖 **AI-optimized**: Long format defaults for better AI understanding  
- 🔧 **Full feature support**: Posts with images, quotes, replies, search, social actions
- ⚡ **Real-time integration**: Direct Bluesky interaction from Cursor

**Quick Setup:**
```bash
# For new MCP setup: copy sample configuration (no build required!)
mkdir -p .cursor
cp mcp/mcp.sample.json .cursor/mcp.json

# Set your Bluesky credentials
export SSKY_USER=your-handle.bsky.social:your-password

# Restart Cursor to load the MCP tools
```

✨ **Docker will automatically pull the pre-built image on first use!**

**Advanced Setup:**
- **For existing MCP setup**: Add ssky server to your `.cursor/mcp.json` (see `mcp/mcp.sample.json`)
- **For local development**: Use `cd mcp && ./build.sh && cd ..` to build locally
- **Complete guide**: See [MCP Documentation](mcp/SSKY_MCP_GUIDE.md)

**Available Tools:**
- `ssky_get`, `ssky_search`, `ssky_user`, `ssky_profile` - Content retrieval
- `ssky_post` - Content creation with images/quotes/replies
- `ssky_follow`, `ssky_unfollow`, `ssky_repost`, `ssky_unrepost` - Social actions
- `ssky_delete` - Content management

📖 **[Complete MCP Documentation](mcp/SSKY_MCP_GUIDE.md)**

## 🧪 Testing

To run the tests in the `tests/` directory:

1. Copy the environment configuration file and set your Bluesky credentials:
   ```bash
   cp tests/_env tests/.env
   ```
   Edit `tests/.env` and add your Bluesky handle and password.

2. Run tests using pytest:
   ```bash
   # Run all tests
   pytest tests/ -v
   
   # Run individual feature tests
   pytest tests/test_login.py -v              # Login functionality
   pytest tests/test_post_and_delete.py -v    # Post and delete operations
   pytest tests/test_search.py -v             # Search functionality
   pytest tests/test_follow_unfollow.py -v    # Follow/unfollow operations
   pytest tests/test_get.py -v                # Timeline retrieval
   pytest tests/test_profile.py -v            # Profile display
   pytest tests/test_repost_unrepost.py -v    # Repost/unrepost operations
   pytest tests/test_user.py -v               # User functionality
   ```

## 📝 Requirements

- Python 3.12 or later

## 📜 License

[MIT License](LICENSE)

## 👥 Author

[SimpleSkyClient Project](https://github.com/simpleskyclient)
