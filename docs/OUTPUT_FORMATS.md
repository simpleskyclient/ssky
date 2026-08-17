# ssky output formats

Normative specification of what ssky writes, for every combination of result type and
output format.

This document is the source of truth. Where the README, `CLAUDE.md`, the MCP tool
docstrings, or the code disagree with it, they are wrong and should be fixed. Golden-file
tests are expected to be generated against this document so that any accidental change to
output shape fails loudly.

**Status:** the format set is described here as it behaves today, plus the corrections
listed in [Known divergences](#known-divergences). Which formats carry a stability
guarantee is decided separately in #86; until then, treat everything here as descriptive
and provisional.

---

## 1. Selecting a format

Format flags are mutually exclusive and are defined once in `main.py` as a shared parent
parser, so every subcommand accepts the same set.

| Flag | Long form | `format` value | Name used here |
| --- | --- | --- | --- |
| `-I` | `--id` | `id` | ID |
| `-J` | `--json` | `json` | JSON |
| `-L` | `--long` | `long` | Long |
| `-S` | `--simple-json` | `simple_json` | Simple JSON |
| `-T` | `--text` | `text` | Text |
| *(none)* | | `''` | Short |

`-S` is **Simple JSON**; Short has no flag of its own and is what you get when no format
flag is given. `tests/test_format_flags.py` pins this mapping so the documentation cannot
drift away from the parser again (#77).

Two more options affect output:

- `-D STRING` / `--delimiter STRING` — field separator, default a single space. Only the
  Short format and the human-readable Dry-run format consult it.
- `-O DIR` / `--output DIR` — write to files under `DIR` instead of stdout. See
  [§7](#7-file-output--o).

## 2. Result types

Every command function returns one result object carrying a
`.print(format, output, delimiter)` method. Which type you get is a property of the
command, not of the flags:

| Result type | Produced by |
| --- | --- |
| `PostDataList` | `get`, `search`, `post`, `repost`, `unrepost` |
| `ProfileList` | `profile`, `user`, `follow`, `unfollow`, `login` |
| `ThreadDataList` | `get --thread`, `search --thread` |
| `DryRunResult` | `post --dry` |
| `SuccessResult` | `delete` |
| `ErrorResult` | any command that raises `SskyError`; constructed in `main.execute()` |

## 3. Streams, exit codes, and encoding

- stdout and stderr are both wrapped in UTF-8 `TextIOWrapper`s with `line_buffering=False`
  (block buffered). Output is therefore **not** flushed per record.
- Exit code is `0` on success and `1` on any failure. There is no finer classification
  today; defining one is #82.
- Human-readable formats write errors to **stderr**. JSON formats write errors to
  **stdout** — see [Known divergences](#known-divergences) and #83.
- A closed downstream pipe (`ssky … | head`) restores default `SIGPIPE` handling and
  exits with `128 + SIGPIPE` (typically `141`) without a traceback. `BrokenPipeError`
  in the entry point is handled the same way as a fallback.

## 4. The matrix

Per result type, what one record looks like and how records are separated.

| | Short (default) | `-I` id | `-T` text | `-L` long | `-S` simple_json | `-J` json |
| --- | --- | --- | --- | --- | --- | --- |
| **`PostDataList`** | 1 line/post, delimiter-joined | 1 line/post, `uri::cid` | post text, **multi-line** | labelled block, **multi-line** | **one envelope object** for the whole list | **one JSON object per line** (JSONL) |
| **`ProfileList`** | 1 line/profile, delimiter-joined | 1 line/profile, DID | description, **multi-line** | labelled block, **multi-line** | **one envelope object** for the whole list | **one JSON object per line** (JSONL) |
| **`ThreadDataList`** | posts as Short, replies prefixed `\| ` | same, prefixed `\| ` | posts as Text, `\|` between | posts as Long, `\|` between | **rejected** (#81) | **rejected** (#81) |
| **`DryRunResult`** | labelled lines | *same as Short* | *same as Short* | *same as Short* | **bare object**, no envelope | envelope object |
| **`SuccessResult`** | message text | *same as Short* | *same as Short* | *same as Short* | envelope object | envelope object |
| **`ErrorResult`** | message to stderr | *same* | *same* | *same* | envelope to **stdout** | envelope to **stdout** |

Cells reading *same as Short* mean the format argument is ignored for that result type.

### 4.1 The JSON envelope

`-S` on list types, and both `-S` and `-J` on `SuccessResult` / `ErrorResult` /
`DryRunResult`, emit a single object built by `util.create_json_response()`:

```json
{"status":"ok","http_code":200,"message":"Retrieved 3 item(s)","timestamp":"2026-08-02T07:17:00.429887Z","data":[...]}
```

Field order is fixed as `status`, `http_code`, `message`, `timestamp`, `data`. Serialized
with `ensure_ascii=False` and `separators=(',', ':')` — no spaces, non-ASCII emitted raw.

- `status` — `"ok"` or `"error"`. **Not** `"success"`.
- `http_code` — 200 on success; on error the code carried by the `SskyError` subclass.
- `message` — human-readable summary. For `PostDataList` the verb reflects the operation:
  `Posted N item(s)` from `post`, `Retrieved N item(s)` from `get` and `search`. Not
  machine-stable; do not parse it.
- `timestamp` — UTC ISO-8601 with `Z`, generated at print time. **Non-deterministic**, so
  golden-file tests must mask this field.
- `data` — payload; `null` on error.

`-J` on `PostDataList` / `ProfileList` does *not* use the envelope. It emits the raw
atproto model per line via `models.utils.get_model_as_json()`, with upstream's camelCase
key names, and follows upstream's schema — not ours.

### 4.2 Why the two JSON formats differ

The asymmetry is deliberate. They serve different consumers and should not be made to
converge:

- **`-J` is a passthrough for pipelines.** One upstream record per line, produced by
  looping and printing, which is line-delimited JSON by construction. It streams, composes
  with `head` / `jq` / `while read`, and carries no ssky-owned framing — which is also why
  its stability follows upstream's, not ours.
- **`-S` is ssky's own format, and the envelope is the point.** It is what the MCP server
  passes to a model, and a single object is what an MCP tool returns. `status`,
  `http_code`, and `message` are context the model can reason about — "this succeeded and
  returned nothing" is a different signal from "this failed" — and that context would be
  lost in a bare stream of records.

So `-J` is the pipe format and `-S` is the agent format. Neither should grow the other's
framing.

## 5. Per-format detail

### 5.1 `PostDataList`

**Short.** One line per post, fields joined with the delimiter:

```
<uri>::<cid> <author_did> <author_handle> <display_name> <text_summary>
```

`display_name` and `text_summary` pass through `util.summarize()`, which replaces every
whitespace and control character with `_`. `text_summary` is truncated to 40 characters
with a trailing `..`; `display_name` is not truncated. A record is therefore always
exactly one line.

```
at://did:plc:pkyp…/app.bsky.feed.post/3ms3fyqygpw2b::bafyreicysce6… did:plc:pkyp… nikkei.com 日経電子版 胃がん・食道がんの患者、術後に約8割が仕事に復帰_www.nikkei.co..
```

**ID.** One line per post: `<uri>::<cid>`, joined by `::` (`util.join_uri_cid`). This is
the form other ssky commands accept as input, and the form `goat` accepts as a bare URI
once the `::<cid>` suffix is stripped.

**Text.** The post's `record.text`, with any link facets restored to their full URLs
(Bluesky stores a display-truncated form in the text and the real target in the facet).
Emitted **raw**: newlines, delimiters, and control characters in the post are reproduced
as authored, so one post can span many lines and there is no record separator. Not
parseable; use `-S` or `-J` for that.

**Long.** A labelled block per post, fields in this order:

```
Author-DID: <did>
Author-Display-Name: <display name>
Author-Handle: <handle>
Created-At: <created_at>
Record-CID: <cid>
Record-URI: <uri>
Repost-URI: <uri>        # only when post.viewer.repost is set
<blank line>
<post text, links restored, raw>
```

Consecutive posts are separated by a line of exactly sixteen hyphens, `----------------`.

**Simple JSON.** One envelope for the whole list; `data` is an array of:

| Field | Notes |
| --- | --- |
| `uri` | |
| `cid` | |
| `author` | object: `did`, `handle`, `display_name`, `avatar` |
| `text` | raw post text, **not** URL-restored (unlike `-T`) |
| `created_at` | |
| `reply_count`, `repost_count`, `like_count` | `0` when absent |
| `indexed_at` | `null` when absent |
| `facets` | object with `links[]`, `mentions[]`, `tags[]` |

Each facet entry carries `byte_start` and `byte_end`, which are **UTF-8 byte offsets into
`text`**, not character indices, plus the matched `text` segment. `links[]` adds `url`,
`mentions[]` adds `handle` and `did`, `tags[]` adds `tag`.

**JSON.** One raw atproto `PostView` per line. Upstream shape, upstream stability.

### 5.2 `ProfileList`

**Short.** `<did> <handle> <display_name> <description_summary>`, same `summarize()`
treatment, description truncated to 40 characters.

**ID.** The DID, one per line.

**Text.** The profile description, raw and possibly multi-line. Empty string when the
profile has no description.

**Long.**

```
Created-At: <created_at>
DID: <did>
Display-Name: <display name>
Handle: <handle>
<blank line>
<description>
```

Separated by `----------------` between profiles.

**Simple JSON.** Envelope with `data` as an array of: `did`, `handle`, `display_name`,
`description` (`""` when absent), `avatar`, `banner`, `followers_count`, `follows_count`,
`posts_count`, `created_at`, `indexed_at`.

Note `follows_count`, not `following_count` — the MCP docstrings say the latter.

**JSON.** One raw atproto `ProfileViewDetailed` per line.

### 5.3 `ThreadDataList`

A thread is flattened depth-first into `(post, depth)` pairs; `NotFoundPost` and
`BlockedPost` nodes are skipped silently. Threads are fetched once per root URI, oldest
first, then reversed so the list order matches the underlying feed order.

Each post is rendered exactly as the corresponding `PostDataList` format, then decorated:

- **Short / ID**: every line of a post at `depth > 0` is prefixed with `"| "`.
- **Text / Long**: posts within a thread are separated by a line containing `|`.
  Depth is **not** indicated.
- Between threads, `ThreadDataList` prints `----------------`, for Text and Long only.

`-S` and `-J` raise `InvalidOptionCombinationError` with
`--thread cannot be used with --json or --simple-json`, exit 1. Lifting this is #80/#81.

### 5.4 `DryRunResult`

**Short / ID / Text / Long** are identical — labelled lines, one per present element,
omitted entirely when empty:

```
Message: <text as it would be posted>
Tags: <comma-joined>
Links: <comma-joined>
Mentions: <comma-joined>
Images: <path> (alt: <alt>), …
Video: <path> (alt: <alt>)
Card: <title>
Reply to: <uri>
Quote: <uri>
Languages: <comma-joined>
Allow reply: <who, or "nobody">
Quote posts: disabled
```

Joined with newlines when the delimiter is the default space, and with the delimiter
otherwise — the inverse of how the delimiter behaves everywhere else.

**JSON.** Envelope with `message: "Dry run completed"` and `data` holding the full
detail: `message`, `tags[]`, `links[]`, `mentions[]`, `images[]` (`path`, `alt_text`,
`size`, `mime_type`), `card`, `reply_to`, `quote`, `langs[]`, `video`, `video_alt`,
`allow_reply`, `no_quote`.

**Simple JSON.** A **bare object with no envelope**, and lossy — the arrays are replaced
by their lengths:

```json
{"message":"hello #tag example.com","tags":1,"links":1,"mentions":0,"images":0,"has_card":true,"has_reply_to":false,"has_quote":false,"langs":[],"has_video":false,"allow_reply":null,"no_quote":false}
```

This is the only place in ssky where `-S` is not enveloped and `-J` is. See
[Known divergences](#known-divergences).

### 5.5 `SuccessResult`

Only `delete` returns this. Short, ID, Text and Long all print the plain message
(`Post deleted successfully`). `-S` and `-J` both emit the envelope with `data` carrying
the operation payload, e.g. `{"deleted": "at://…"}`.

Warnings, if any, are printed to stderr as `Warning: <text>` in non-JSON formats, and
folded into the envelope's `message` as `… (Warnings: a; b)` in JSON formats.

### 5.6 `ErrorResult`

Constructed in `main.execute()` from a raised `SskyError`, carrying that exception's
`message` and `http_code`.

- Human formats: the bare message to **stderr**, nothing on stdout, exit 1.
- `-S` / `-J`: the error envelope (`status: "error"`, `data: null`) to **stdout**,
  nothing on stderr, exit 1.

## 6. Empty results

An empty result is **not** an error. Exit code is 0.

| Format | Output for an empty list |
| --- | --- |
| Short, ID, Text, Long | nothing at all — zero bytes |
| `-J` | nothing at all — zero bytes |
| `-S` | envelope with `"data":[]` |

Scripts must therefore not distinguish "no results" from "failed" by looking at stdout
alone under `-J`. Whether an empty result should get its own exit code is #82.

## 7. File output (`-O`)

`-O DIR` writes one file per item instead of writing to stdout.

- `PostDataList`: `<author_handle>.<YYYYMMDDhhmmss>.txt`, the timestamp taken from
  `record.created_at` with all separators stripped.
- `ProfileList`: `<handle>.txt`.
- `ThreadDataList`: one file per **thread**, named after the thread's root post using the
  `PostDataList` rule.

Each file holds that item's rendering in the selected format plus a trailing newline.
Consequences worth knowing:

- Separators (`----------------`) are not written; each file stands alone.
- Under `-S`, each file gets **its own envelope** wrapping that single item, unlike the
  single whole-list envelope on stdout.
- `PostDataList` and `ProfileList` do **not** create `DIR`; a missing directory surfaces
  as `[Errno 2] No such file or directory: …` on stderr with exit 1. `ThreadDataList`
  creates it. See [Known divergences](#known-divergences).
- Two posts by the same author in the same second collide and the later one wins.

## 8. Known divergences

Places where the current implementation is internally inconsistent. This section records
the intended behavior; the spec above describes what happens today, so these are the
deltas to work through.

| # | Divergence | Intended | Tracked by |
| --- | --- | --- | --- |
| 1 | `--thread` refuses `-J`/`-S` | structured output for threads | #80, #81 |
| 2 | Errors go to stdout under `-J`/`-S` | payload-only stdout, or an explicit documented exception | #83 |
| 3 | A custom delimiter is not escaped in Short; `-D ,` on a display name containing `,` produces an unparseable line | specified escaping, or a NUL-delimited mode | #85 |
| 4 | An absent `display_name` yields an empty field, so a space-delimited Short line silently loses a column | a placeholder, or a documented rule | #85 |
| 5 | `DryRunResult` inverts the convention: `-S` bare and lossy, `-J` enveloped | `-S` enveloped like every other type | #94 |
| 6 | `SuccessResult` ignores `-I`/`-T`/`-L`, so `ssky delete <uri> -I` prints prose instead of the URI | `-I` yields the affected identifier | #95 |
| 7 | `-O` creates the directory for threads but not for posts or profiles | create it in all cases, or fail the same way in all cases | #96 |
| 8 | Dead branch: `ThreadData._print_to_stdout` tests `format in ('long','text')` inside the branch that only runs for `''` and `'id'` | remove, or restore the intended separator | #96 |

Two further notes that are documentation rather than code:

- #72's issue body describes the envelope as `{"status": "success", "data": [...]}`. The
  actual status value is `"ok"` and the envelope also carries `http_code`, `message`, and
  `timestamp`.
- MCP tool docstrings in `src/ssky_mcp/server.py` describe a `following_count` field and a
  flat post shape that do not match `-S`. Since each MCP tool shells out to the CLI with
  `--simple-json`, the docstrings should be regenerated from this document.

## 9. Interop

`-I` emits `at://…::<cid>`. Stripping the `::<cid>` suffix gives a plain AT-URI, which
other atproto tooling consumes directly:

```sh
ssky search 'bluesky' -I | awk -F'::' '{print $1}' | xargs -n1 goat get
```

Positioning ssky as the ergonomic front end to that tooling is cheaper than reimplementing
it.
