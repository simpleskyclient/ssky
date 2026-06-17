# CLAUDE.md

Guidance for Claude Code when working in this repository.

## Project Overview

ssky is a lightweight command-line Bluesky client. It ships:
- The `ssky` CLI for posting, searching, and managing Bluesky content (images, quotes, replies, rich text)
- An MCP server (`src/ssky_mcp/`) for IDE integration

Requires Python 3.12+. Uses Poetry. Key deps: `atproto`, `beautifulsoup4`, `requests`, `fastmcp` (see `pyproject.toml`).

## Commands

**Always prefix Python/tool commands with `poetry run`** to use the correct venv.

```bash
poetry install                                   # install deps
poetry run pytest --tb=short                     # run tests
poetry run pytest tests/test_login.py -v         # single file
SSKY_SKIP_REAL_API_TESTS=1 poetry run pytest     # skip real Bluesky API calls
poetry build                                     # build package

cd mcp && ./build.sh [--local] && cd ..          # build MCP Docker image
cd mcp && ./test_mcp_quick.sh && cd ..           # test MCP server
```

Dev Container loads env from `.env.local` (gitignored; copy from `.env.local.sample`).
`SSKY_USER` format is `handle:password`.

## Architecture

### CLI (`src/ssky/`)
Modular command pattern. Each subcommand is a standalone module (`post.py`, `get.py`,
`search.py`, `follow.py`, ...) exporting a function with the same name as the file.

- **`main.py`**: arg parsing (parent parsers for shared options) and **dynamic command
  loading** — `import_module(f'.{subcommand}')`. To add a command, just create
  `src/ssky/<name>.py` with a `<name>()` function and add its arg parser; no registration.
  Also handles stdin/pipe input (`echo "msg" | ssky post`).
- **`ssky_session.py`**: auth singleton. Always get the client via
  `SskySession.ssky_client()`, never construct `Client()` directly.
- **`post.py`**: text processing, facet detection (links/tags/mentions), link cards.
- **`result.py`**: result types (`PostDataList`, `ProfileList`, `SuccessResult`,
  `ErrorResult`, ...) and the `SskyError` exception hierarchy.
- Data wrappers: `post_data_list.py`, `profile_list.py`, `thread_data.py`,
  `thread_data_list.py`. `util.py` holds URI/CID helpers and MCP JSON builders.

All command functions return a result object with a `.print(format, output, delimiter)`
method. Output formats: `id` (-I), `json` (-J), `long` (-L), `simple_json` (-S),
`text` (-T), short (default).

### MCP server (`src/ssky_mcp/server.py`)
FastMCP server. **Each tool shells out to the `ssky` CLI via `subprocess`**, not Python
imports — so CLI and MCP behavior are guaranteed identical and a CLI fix is inherited
automatically. Deployed via Docker (`mcp/`).

### Authentication
`ssky_client()` resolves auth in order: session file `~/.ssky` (persisted
`session_string`) → command-line credentials → `SSKY_USER` env var → raise `SessionError`.
On successful login it persists the session to `~/.ssky`. The session is a class-level
singleton shared within a process. **Never delete `~/.ssky` in production code** (tests
preserve it via `conftest.py`).

## Critical gotchas

- **Facets use UTF-8 byte positions, not character indices.** Emoji/multibyte chars shift
  positions. Always compute `index.byte_start`/`byte_end` from byte lengths. Facets must
  not overlap. Detection regexes and creation live in `post.py`.
- **Process facets in reverse byte order** when restoring/replacing URLs in text, to avoid
  index shifting.
- **Post availability is eventually consistent** — `post.py` polls `get_post()` after
  creating a post until it becomes available.
- **`--thread` cannot be combined with `--json`/`--simple-json`** (raises
  `InvalidOptionCombinationError`). With `--thread`, `get()`/`search()` return
  `ThreadDataList` and deduplicate posts that belong to the same thread (processed
  oldest-first; default `--thread-parent-height=10`).
- Raise `SskyError` subclasses, never generic exceptions. Convert atproto errors with
  `handle_atprotocol_error()`.

## Conventions

- **Commit messages: single-line summary only.** No body, no emoji, no
  "Generated with Claude Code" / "Co-Authored-By" footers.
- **Repositories**: upstream is `simpleskyclient/ssky`; `mkyutani/ssky` is the dev fork.
  File **issues** and **PRs** against upstream (push to fork first). Confirm repo
  ownership before any GitHub operation.

## Safety for posting features

Use dry run first (`--dry` / `dry_run=True`), never post without user approval in
automated flows, check auth before operating, respect the 30s per-operation timeout, and
mark test posts with `[TEST <timestamp>]`. Never post credentials or sensitive data.
