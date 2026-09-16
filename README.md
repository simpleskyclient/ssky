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

This installs the CLI and nothing else. If you also want the MCP server for IDE
integration, install the optional extra instead:

```bash
pip install 'ssky[mcp]'
```

### Login

```bash
ssky login your-handle.bsky.social:your-password
```

Or set credentials via environment variable:
```bash
export SSKY_USER=your-handle.bsky.social:your-password
```

### Configuration

By default, ssky stores session data in `~/.ssky`. You can customize this location using the `SSKY_CONFIG_PATH` environment variable:

```bash
# Use a custom session file location
export SSKY_CONFIG_PATH=/path/to/custom/session
ssky login your-handle.bsky.social:your-password

# Useful for testing or managing multiple accounts
export SSKY_CONFIG_PATH=~/.ssky-test
```

**Note:** The `SSKY_CONFIG_PATH` must be set before running ssky commands, as it's evaluated when the session module is first loaded.

## 📖 Basic Usage

### Posting

```bash
# Simple post
ssky post "Hello, Bluesky!"

# Post with images (add alt text in the same order as --image)
ssky post "Check out these photos!" --image photo1.jpg --image photo2.jpg --alt "a cat" --alt "a dog"

# Post a video
ssky post "My clip" --video clip.mp4 --video-alt "a short clip"

# Tag the language(s) of the post
ssky post "こんにちは" --lang ja

# Reply to a post
ssky post "Great post!" --reply-to at://did:plc:.../app.bsky.feed.post/...

# Quote a post
ssky post "Interesting!" --quote at://did:plc:.../app.bsky.feed.post/...

# Restrict who can reply (threadgate) and disable quote posts (postgate)
ssky post "Announcement" --allow-reply following --allow-reply mentioned --no-quote
ssky post "Private thought" --allow-reply nobody
```

### Reading

```bash
# View your timeline
ssky get

# View your timeline with full threads
ssky get --thread

# Get specific post with its thread
ssky get at://did:plc:.../app.bsky.feed.post/... --thread

# Get user's posts as threads with custom depth
ssky get user.bsky.social --thread --thread-depth 5 --thread-parent-height 2

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

### Thread Retrieval

Retrieve posts along with their complete conversation threads:

```bash
# Get timeline with full threads (each post expanded to its thread)
ssky get --thread

# Get specific post's thread
ssky get at://did:plc:.../app.bsky.feed.post/... --thread

# Get user's posts as threads
ssky get user.bsky.social --thread

# Control thread depth (default: 10 replies deep)
ssky get --thread --thread-depth 5

# Include parent posts (default: 0 parents)
ssky get --thread --thread-parent-height 2

# Save threads to files
ssky get --thread --output ./threads
```

**Thread Output Formatting:**
- **Short/ID format** (no flag, `-I`): Reply lines prefixed with `"| "`
- **Long/Text format** (`-L`, `-T`): Posts within thread separated by `"|"`, independent threads by `"----------------"`
- **JSON/simple-json**: Cannot be used with `--thread` (returns error)

### Output Formats

```bash
# Get only post IDs
ssky get --id

# Get only text content
ssky get --text

# Get full JSON output
ssky get --json

# Get simplified JSON with facets metadata (ideal for programmatic access)
ssky get --simple-json

# Save posts to files
ssky get --output ./posts
```

📖 **[Output format specification](docs/OUTPUT_FORMATS.md)** — exactly what each format
emits for each kind of result: field sets, delimiters, escaping, empty results, and error
behavior. Read this before scripting against ssky output.

#### Facets Metadata in Simple-JSON

The `--simple-json` format includes structured facets metadata for rich text features:

- **links**: URLs with byte positions and text
- **mentions**: User mentions with handles, DIDs, and byte positions
- **tags**: Hashtags with byte positions and text

Example output:
```json
{
  "status": "success",
  "data": [{
    "uri": "at://...",
    "cid": "...",
    "author": {
      "did": "did:plc:...",
      "handle": "user.bsky.social",
      "display_name": "User Name",
      "avatar": "https://..."
    },
    "text": "Check out https://example.com @user.bsky.social #bluesky",
    "created_at": "2024-01-01T00:00:00.000Z",
    "facets": {
      "links": [
        {
          "url": "https://example.com",
          "byte_start": 10,
          "byte_end": 30,
          "text": "https://example.com"
        }
      ],
      "mentions": [
        {
          "handle": "user.bsky.social",
          "did": "did:plc:...",
          "byte_start": 31,
          "byte_end": 49,
          "text": "@user.bsky.social"
        }
      ],
      "tags": [
        {
          "tag": "bluesky",
          "byte_start": 50,
          "byte_end": 58,
          "text": "#bluesky"
        }
      ]
    }
  }]
}
```

### Useful Examples

```bash
# Reply to your last post
ssky post "Update!" --reply-to $(ssky get myself --limit 1 --id)

# Search your own posts
ssky search "keyword" --author myself

# Save your timeline to files
ssky get --output ./timeline

# `get` has no time filter, since the AT Protocol feed APIs it uses
# (getAuthorFeed/getTimeline) don't support one. `search` does, so use it
# for time-bounded lookups instead (note: search doesn't guarantee returning
# every post from an account, and it excludes reposts).
ssky search "*" --author myself --since 2026-09-01
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
# Install ssky with the MCP extra
pip install 'ssky[mcp]'

# Copy the sample configuration
mkdir -p .cursor
cp mcp/mcp.sample.json .cursor/mcp.json

# Set your Bluesky credentials
export SSKY_USER=your-handle.bsky.social:your-password

# Restart Cursor to load the MCP tools
```

The MCP server is a Python process that runs over stdio, so `uvx` works without
installing anything permanently — see `mcp/mcp.sample.json`.

**Alternative Setup:**
- **Docker**: `cp mcp/mcp.docker.sample.json .cursor/mcp.json` uses the pre-built
  `ghcr.io/simpleskyclient/ssky-mcp` image, which is pulled automatically on first use.
  Useful if you would rather not have a Python environment involved.
- **For existing MCP setup**: Add the ssky server to your `.cursor/mcp.json` (see the
  sample files above)
- **For local development**: Use `cd mcp && ./build.sh && cd ..` to build the image locally
- **Complete guide**: See [MCP Documentation](mcp/SSKY_MCP_GUIDE.md)

**Available Tools:**
- `ssky_get`, `ssky_search`, `ssky_user`, `ssky_profile` - Content retrieval
- `ssky_post` - Content creation with images/quotes/replies
- `ssky_follow`, `ssky_unfollow`, `ssky_repost`, `ssky_unrepost` - Social actions
- `ssky_delete` - Content management

📖 **[Complete MCP Documentation](mcp/SSKY_MCP_GUIDE.md)**

## 🤝 Contributing

Contributions are welcome. **[CONTRIBUTING.md](CONTRIBUTING.md)** covers development
setup, the Dev Container, running the tests, and how to open a pull request.

Please read the claiming convention there before you start work: comment on an issue to
claim it, and check whether an open pull request already references it.

## 📝 Requirements

- Python 3.12 or later

## 📜 License

[MIT License](LICENSE)

## 👥 Author

[SimpleSkyClient Project](https://github.com/simpleskyclient)
