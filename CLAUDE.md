# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

ssky is a lightweight command-line Bluesky client for terminal interaction with the Bluesky social network. It includes:
- CLI tool (`ssky`) for posting, searching, and managing Bluesky content
- MCP (Model Context Protocol) server for IDE integration (Cursor Agent)
- Support for images, quotes, replies, and rich text features

## Development Commands

### Environment Setup
This project uses Poetry for dependency management. **Always use `poetry run` prefix** to ensure correct virtual environment:

```bash
# Install dependencies
poetry install

# Add new dependency
poetry add package-name

# Add development dependency
poetry add --group dev package-name
```

### Dev Container Environment Variables
When using VS Code Dev Containers, environment variables are loaded from `.env.local`:

```bash
# Create .env.local from sample
cp .env.local.sample .env.local

# Edit .env.local to add your credentials
# SSKY_USER=your-handle.bsky.social:your-password
# SSKY_SKIP_REAL_API_TESTS=1
```

The dev container automatically:
- Loads `.env.local` on container startup (via `runArgs` in `devcontainer.json`)
- Installs Claude Code extension (`anthropic.claude-code`)
- Provides Python 3.12 with Docker-outside-of-Docker support

**Important**: `.env.local` is gitignored and should never be committed.

### Testing
**Important**: All Python commands must run through Poetry to avoid import errors.

```bash
# Run all tests (recommended)
poetry run pytest --tb=short

# Run all tests (verbose)
poetry run python -m pytest

# Run specific test file
poetry run python -m pytest tests/test_login.py -v

# Run specific test method
poetry run python -m pytest tests/test_login.py::TestLoginSequential::test_01_login_with_credentials_parameter

# Disable real API tests (prevents actual Bluesky API calls)
export SSKY_SKIP_REAL_API_TESTS=1
poetry run python -m pytest
```

### Building and Publishing
```bash
# Build package
poetry build

# Check built package
ls -la dist/
```

### MCP Server Development
```bash
# Build Docker image locally
cd mcp && ./build.sh && cd ..

# Build for local development with source code
cd mcp && ./build.sh --local && cd ..

# Test MCP server
cd mcp && ./test_mcp_quick.sh && cd ..
cd mcp && ./test_mcp_full.sh && cd ..
```

## Code Architecture

### Core Package Structure (`src/ssky/`)
The main CLI package follows a modular command pattern:

- **`main.py`** (entry point):
  - Lines 19-89: Argument parsing with parent parsers for common options
  - Lines 99-100: **Dynamic module loading** - `import_module(f'.{subcommand}')` automatically loads command modules
  - Lines 93-97: stdin detection for pipe support (`echo "msg" | ssky post`)
  - To add a new command: just create `new_command.py` with a `new_command()` function

- **`ssky_session.py`** (authentication):
  - Lines 14-15: Session file path `~/.ssky` and singleton instance
  - Lines 31-73: Authentication hierarchy (session file → credentials → env var → error)
  - Lines 76-82: Session persistence via `export_session_string()`
  - Lines 124-125: `ssky_client()` helper returns authenticated atproto client
  - **Important**: All commands should use `SskySession.ssky_client()` not direct Client()

- **`post.py`** (text processing and posting):
  - Lines 150-163: **Facet detection** - regex patterns for links, tags, mentions
  - Lines 132-148: **Byte-level indexing** - AT Protocol requires UTF-8 byte positions, not character positions
  - Lines 317-351: Facet creation with `AppBskyRichtextFacet.Main` objects
  - Lines 24-130: Link card generation (Open Graph fetching)
  - Lines 383-387: Post availability polling (eventual consistency handling)
  - **Critical**: When processing text, always work with byte positions for facets

- **`result.py`** (error handling):
  - Lines 14-80: Result classes (`ErrorResult`, `SuccessResult`, `DryRunResult`)
  - Lines 207-306: Custom exception hierarchy extending `SskyError`
  - Lines 337-362: `handle_atprotocol_error()` converts atproto exceptions to `ErrorResult`
  - **Important**: Always raise `SskyError` subclasses, never generic exceptions

- **Command modules**: Each subcommand (`get.py`, `post.py`, `search.py`, etc.) is a standalone module with a function matching its name
  - Standard pattern: validate args → get client → call API → return `PostDataList`/`ProfileList`
  - All commands return result objects with `.print()` method for formatting

- **Data structures**:
  - **`post_data_list.py`** (Lines 32-61): URL restoration from facets (processes in reverse order to avoid index shifting)
  - **`post_data_list.py`** (Lines 67-119): `_extract_facets_data()` extracts structured facets metadata (links, mentions, tags)
  - **`post_data_list.py`** (Lines 154-174): `get_simple_data()` returns simplified post data with facets field
  - **`profile_list.py`** (Lines 118-129): Lazy loading - only fetches profiles when printing

- **`util.py`**:
  - Lines 15-23: URI/CID handling (`join_uri_cid`, `disjoin_uri_cid`)
  - Lines 25-101: Standardized JSON response builders for MCP

### MCP Server (`src/ssky_mcp/`)

**Architecture: Subprocess Wrapper Pattern**

- **`server.py`**: FastMCP-based server exposing 10 tools for Bluesky operations
- **Key Design**: MCP tools call `ssky` CLI via subprocess, NOT via Python imports
- **Benefit**: CLI and MCP behavior guaranteed identical; no shared state issues
- **Example pattern** (all tools follow this):
  ```python
  args = ["ssky", "get", "-N", str(limit), "--simple-json"]
  result = subprocess.run(args, capture_output=True, timeout=30)
  return format_success_response(result.stdout)
  ```
- Uses Docker for deployment (see `mcp/Dockerfile` and `mcp/Dockerfile.dev`)
- **Important**: Changes to CLI commands automatically apply to MCP tools

### Authentication Flow

**Hierarchy** (ssky_session.py:31-73):
1. Try session file (`~/.ssky`) with persisted session_string (most efficient)
2. If session invalid/missing, try explicit credentials from command args
3. If not provided, try `SSKY_USER` environment variable (format: `handle:password`)
4. If still unavailable, raise `SessionError`
5. On successful login, automatically persist to `~/.ssky` (lines 56-57, 65-67)

**Singleton Pattern**: `SskySession.session` is class-level and shared across all operations in the same process

### Output Formats
All retrieval commands support multiple output formats via `-I/-J/-L/-T` flags:
- **`id`**: URIs/IDs only (for scripting)
- **`json`**: Full JSON format
- **`long`**: Detailed human-readable format (default for MCP)
- **`simple_json`**: Simplified JSON for MCP consumption **with facets metadata**
  - Includes structured arrays for links, mentions, and tags
  - Each facet entry contains URL/handle/tag, byte positions, and text segment
  - Example: `{"facets": {"links": [...], "mentions": [...], "tags": [...]}}`
- **`text`**: Text content only

### Testing Architecture
- **`test_00_ssky_session.py`**: ONLY tests making real API calls
- All other tests use mocked `SskySession` for speed and safety
- Session file (`~/.ssky`) preservation: never deleted by tests
- Fixtures in `conftest.py` manage test session lifecycle
- Real API tests marked with `[TEST timestamp]` and can be disabled via `SSKY_SKIP_REAL_API_TESTS=1`

## GitHub Repository Information

This project has two repositories:
- **Upstream**: `simpleskyclient/ssky` (for issues and pull requests)
- **Local fork**: `mkyutani/ssky`

**Always confirm repository ownership before GitHub operations** using MCP GitHub tools or `gh` command.

## Git Commit Message Policy

**Commit messages should be a single-line summary only. Do NOT include:**
- Multi-line body text
- "Generated with Claude Code" footer
- "Co-Authored-By: Claude" footer
- Emoji or decorative elements

**Example**:
```
✅ GOOD: feat: add facets to simple-json output
❌ BAD:  feat: add facets to simple-json output

         All tests pass. Backward compatible.

         🤖 Generated with [Claude Code](https://claude.com/claude-code)

         Co-Authored-By: Claude <noreply@anthropic.com>
```

## Important Architectural Patterns

### 1. Dynamic Command Registration
**Pattern**: Commands auto-register by filename (main.py:99-100)
```python
module = import_module(f'.{subcommand}', f'{__package__}')
func = getattr(module, f'{subcommand}')
```
**To add a new command**: Create `src/ssky/mycommand.py` with a `mycommand()` function. No registration needed.

### 2. Byte-Level Text Processing (Critical for Facets)
**Why**: AT Protocol requires UTF-8 byte positions, not character indices
**Location**: post.py:132-148
**Challenge**: Emoji and multibyte characters have different byte/character lengths

**Example**:
```python
text = "Hello 👋 @user.bsky.social"
# Character position: @ is at index 9
# Byte position: @ is at index 11 (emoji is 4 bytes)
```
**Always use**: `byte_len(text[:position])` when creating facets

### 3. Facet Processing Order
**Pattern**: Process facets in reverse order (post_data_list.py:43-45)
```python
sorted_facets = sorted(facets, key=lambda f: f.index.byte_start, reverse=True)
```
**Why**: Prevents index shifting when replacing/restoring URLs in text

### 4. MCP Subprocess Isolation
**Pattern**: MCP calls CLI via subprocess, not Python imports
**Benefit**: No state pollution between MCP calls; CLI and MCP guaranteed identical
**Implication**: If you fix a bug in CLI, MCP automatically inherits the fix

### 5. Result Object Pattern
**All commands return**: `PostDataList`, `ProfileList`, `SuccessResult`, or `ErrorResult`
**All have**: `.print(format, output, delimiter)` method
**Formats handled**: `id`, `text`, `long`, `json`, `simple_json`

### 6. Lazy Data Loading
**ProfileList pattern** (profile_list.py:118-129):
- Stores DIDs initially
- Only fetches full profiles when `.print()` called
- Fetches in batches of 25
**Benefit**: Avoids unnecessary API calls

### 7. Post Availability Polling
**Pattern**: Wait for eventual consistency (post.py:383-387)
```python
post = get_post(result.uri)
while post is None:
    warnings.append('Waiting for post to become available')
    sleep(1)
    post = get_post(result.uri)
```
**Why**: Bluesky posts may not be immediately available after creation

## Key Implementation Details

### Message Processing (post.py)
When posting, ssky automatically detects and handles:

1. **Links** (Lines 150-151):
   - Regex: `r'https?://[\w/:%#\$&\?\(\)~\.=\+\-]+'`
   - Generates link cards via Open Graph (lines 24-130)
   - Downloads thumbnails and attaches to post

2. **Hashtags** (Lines 153-154):
   - Regex: `r'#\S+'`
   - Strips `#` when creating facet
   - Preserves `#` in displayed text

3. **Mentions** (Lines 156-163):
   - Regex: `r'@[\w.]+'`
   - Resolves handle to DID via `IdResolver`
   - Creates `AppBskyRichtextFacet.Mention` with DID

**All facets** include byte-level `index.byte_start` and `index.byte_end` positions.

### Session Persistence
- Session stored in `~/.ssky` as JSON with `session_string`
- Format: `{"session_string": "..."}`
- Session refresh handled automatically by atproto client
- Environment variable format: `SSKY_USER=handle:password`
- **Never delete session file in production code** (tests preserve it via conftest.py)

### stdin Support
The `post` command reads from stdin when no message argument provided (main.py:93-97):
```bash
echo "Hello Bluesky" | ssky post
cat message.txt | ssky post
```
**Pattern**: `if not sys.stdin.isatty()` detects pipe input

### MCP Docker Images
- **Pre-built**: `ghcr.io/simpleskyclient/ssky-mcp:latest` (auto-built via GitHub Actions)
- **Local**: `ssky-mcp:latest` (built via `mcp/build.sh`)
- **Development**: `ssky-mcp:local` (built via `mcp/build.sh --local` with local source)

### URI and CID Format
**Format**: `at://did:plc:abc123/app.bsky.feed.post/xyz789::bafy...`
**Components**:
- `at://...`: AT Protocol URI
- `::`: Delimiter (util.py:15-23)
- `bafy...`: Content ID (CID)

**Helpers**:
- `join_uri_cid(uri, cid)` → combined string
- `disjoin_uri_cid(combined)` → (uri, cid) tuple

## Common Development Scenarios

### Adding a New CLI Command

1. Create `src/ssky/mycommand.py`:
```python
from ssky.ssky_session import ssky_client, SskySession
from ssky.result import ErrorResult, SuccessResult, SskyError

def mycommand(arg1, arg2, format='', delimiter=' ', output=None):
    """Your command implementation."""
    try:
        client = ssky_client()  # Get authenticated client
        # Your logic here
        result = client.some_api_call()
        return SomeResultList(result)  # Must have .print() method
    except Exception as e:
        from ssky.result import handle_atprotocol_error
        return handle_atprotocol_error(e)
```

2. Add argument parser in `main.py`:
```python
mycommand_parser = sp.add_parser('mycommand',
    formatter_class=SortingHelpFormatter,
    parents=[delimiter_options, format_options],
    help='Description')
mycommand_parser.add_argument('arg1', type=str, help='Help text')
```

3. No registration needed - dynamic loading handles it

### Modifying Text Processing for Posts

**Important locations**:
- `post.py:150-163`: Facet detection regex patterns
- `post.py:317-351`: Facet creation
- `post.py:132-148`: Byte-level indexing

**Remember**:
- Always work with byte positions, not character positions
- Test with emoji and multibyte characters
- Facets must not overlap

### Adding a New Output Format

1. Add to `main.py` format options group
2. Implement in result classes:
   - `PostDataList`: Add new format method
   - `ProfileList`: Add new format method
3. Update `.print()` method to handle new format
4. Update MCP server if needed for programmatic access

### Debugging Authentication Issues

**Check in order**:
1. Session file exists: `ls -la ~/.ssky`
2. Session file valid: `cat ~/.ssky` (should have session_string)
3. Environment variable set: `echo $SSKY_USER`
4. API connectivity: Try `ssky profile myself`

**Force re-authentication**: `rm ~/.ssky && ssky login`

### Testing Changes

**Before committing**:
```bash
# Run fast tests (mocked)
poetry run pytest -k "not real" --tb=short

# Run all tests including real API (if safe)
export SSKY_SKIP_REAL_API_TESTS=0
poetry run pytest --tb=short

# Test specific functionality
poetry run pytest tests/test_post_and_delete.py -v

# Test MCP server
cd mcp && ./test_mcp_quick.sh
```

**Adding new tests**:
- Use mocked `SskySession` for speed (see `conftest.py`)
- Only add real API tests if absolutely necessary
- Mark real API tests with `[TEST timestamp]` in post content
- Add cleanup logic for real API tests

## Safety Guidelines for Automated Operations

When implementing features that post to Bluesky:
1. **Always use dry run first** (`--dry` flag or `dry_run=True` in MCP)
2. **Never post without user approval** in automated workflows
3. **Check authentication** before operations
4. **Respect rate limits** (30-second timeout per operation)
5. **Mark test posts** with identifiable tags like `[TEST]`

### Content Safety
- Validate message length (Bluesky has limits)
- Check image file sizes and formats before uploading
- Sanitize user input to prevent injection attacks
- Never post credentials or sensitive information

## Data Flow Overview

### CLI Execution Flow
```
User runs: ssky post "Hello @user.bsky.social #test"
    ↓
main.py:parse() - Parse arguments
    ↓
main.py:execute() - Dynamic import of 'post' module
    ↓
post.py:post() - Called with message and args
    ↓
SskySession.ssky_client() - Get authenticated client
    ├─ Try ~/.ssky session file
    ├─ Try command line credentials
    └─ Try SSKY_USER env var
    ↓
post.py:get_mentions/get_links/get_tags() - Extract facets
    ├─ Regex matching: @user.bsky.social → resolve to DID
    ├─ Regex matching: #test → create tag facet
    └─ No links in this example
    ↓
post.py:Lines 317-351 - Build AT Protocol facets array
    ├─ AppBskyRichtextFacet.Mention(did=...)
    └─ AppBskyRichtextFacet.Tag(tag="test")
    ↓
client.send_post(text, facets) - POST to Bluesky API
    ↓
post.py:383-387 - Poll for post availability
    ↓
Return PostDataList(post)
    ↓
result.print(format='', delimiter=' ', output=None)
    ↓
stdout: Formatted post output
```

### MCP Tool Execution Flow
```
Cursor Agent calls: ssky_post(message="Hello")
    ↓
ssky_mcp/server.py:ssky_post() - MCP tool handler
    ↓
Build subprocess args: ["ssky", "post", "Hello", "--simple-json"]
    ↓
subprocess.run(args, timeout=30) - Execute CLI
    ↓
[SAME CLI FLOW AS ABOVE]
    ↓
Capture stdout with simple_json format
    ↓
format_success_response(stdout) - Wrap in MCP response
    ↓
Return to Cursor Agent
```

### Authentication State Diagram
```
[No session] → login_internal()
    ↓
Check ~/.ssky exists?
    ├─ YES → Try session_string → SUCCESS → [Authenticated]
    │                           → FAIL ↓
    └─ NO → Try command args → SUCCESS → persist_internal() → [Authenticated]
                             → FAIL ↓
            Try SSKY_USER env → SUCCESS → persist_internal() → [Authenticated]
                              → FAIL ↓
            Raise SessionError
```

## File Organization

```
ssky/
├── src/
│   ├── ssky/                    # Main CLI package
│   │   ├── main.py             # Entry point, arg parsing
│   │   ├── ssky_session.py     # Authentication singleton
│   │   ├── result.py           # Result types, exceptions
│   │   ├── util.py             # Shared utilities
│   │   ├── post.py             # Post creation, facet processing
│   │   ├── get.py              # Timeline/post retrieval
│   │   ├── search.py           # Search posts
│   │   ├── user.py             # Search users
│   │   ├── profile.py          # Profile display
│   │   ├── follow.py           # Follow users
│   │   ├── unfollow.py         # Unfollow users
│   │   ├── repost.py           # Repost posts
│   │   ├── unrepost.py         # Unrepost posts
│   │   ├── delete.py           # Delete posts
│   │   ├── login.py            # Login command
│   │   ├── post_data_list.py   # Post collection wrapper
│   │   └── profile_list.py     # Profile collection wrapper
│   └── ssky_mcp/               # MCP server package
│       ├── server.py           # FastMCP server (10 tools)
│       └── __init__.py
├── tests/                      # Test suite
│   ├── conftest.py            # Pytest fixtures, session management
│   ├── test_00_ssky_session.py # ONLY real API tests
│   └── test_*.py              # Mocked tests
├── mcp/                        # MCP deployment
│   ├── Dockerfile             # Production image
│   ├── Dockerfile.dev         # Development image
│   ├── build.sh               # Build script
│   ├── test_mcp_quick.sh      # Quick tests
│   ├── test_mcp_full.sh       # Full tests
│   └── mcp.sample.json        # Configuration sample
├── pyproject.toml             # Poetry configuration
└── README.md                  # User documentation
```

## Python Version
Requires Python 3.12 or later (specified in `pyproject.toml`).

## Dependencies
Key dependencies (see `pyproject.toml`):
- `atproto` (>=0.0.60): AT Protocol client for Bluesky
- `beautifulsoup4` (^4.12.3): HTML parsing for link cards
- `requests` (^2.32.3): HTTP operations
- `fastmcp` (^2.10.0): MCP server framework
- `pytest` (^8.3.4): Testing framework
- `python-dotenv` (^1.0.1): Environment variable management
