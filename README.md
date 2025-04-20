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
ssky login your-handle.bsky.social your-password
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

## 📝 Requirements

- Python 3.12 or later

## 📜 License

[MIT License](LICENSE)

## 👥 Author

[SimpleSkyClient Project](https://github.com/simpleskyclient)
