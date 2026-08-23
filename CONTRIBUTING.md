# Contributing to ssky

Thanks for your interest. Please read [Claiming an issue](#claiming-an-issue) before you
write any code — it is the part that saves everyone wasted work.

## Claiming an issue

Two contributors recently built the same fix for the same issue in parallel, and one of
them had to be turned away. That is our fault for not writing this down, so here it is.

Before you start work:

1. **Check the issue is open.** A closed issue is done; offering to take it means the fix
   already shipped.
2. **Check nobody is already on it.** A **`claimed`** label means someone has said they
   are working on it. The label is a convenience, not the record, so also look at:
   - the issue's comments, and
   - **open pull requests that reference it** — the issue page lists linked PRs, or run
     `gh pr list --repo simpleskyclient/ssky --search 84`.

   An open PR is a claim even if nobody commented on the issue and the label is missing.
3. **Comment on the issue** saying you'd like to take it. A maintainer will reply to
   confirm, and that reply is the record that the issue is yours.

You don't have to wait for the confirmation to start — but do comment *before* you start,
so the next person can see the issue is taken. Opening a PR without commenting first is
what caused the collision above.

**Don't read anything into the assignee field.** GitHub only allows assigning people who
already have access to the repository, so an issue claimed by an outside contributor will
still show no assignee. An empty assignee field does not mean an issue is free — the
comments are what count.

If someone else has already claimed an issue, ask in the thread before starting parallel
work.

Maintainers: reply promptly when someone claims an issue, and add the `claimed` label so
the state is visible from the issue list. Remove it if the claim is withdrawn or goes
stale. A claim left without an answer is the state that causes duplicated work.

## Development setup

ssky requires Python 3.12 or later and uses [Poetry](https://python-poetry.org/).

```bash
poetry install --extras mcp    # dependencies, including the MCP server
poetry install                 # CLI dependencies only, as end users get them
```

`fastmcp` is an optional extra (`ssky[mcp]`), not a core dependency — a plain
`pip install ssky` must not pull it in.

**Prefix Python and tool commands with `poetry run`** so they use the project virtualenv.

### Dev Container

For development using VS Code Dev Containers:

1. Copy the environment configuration file and set your Bluesky credentials:
   ```bash
   cp .env.local.sample .env.local
   ```
   Edit `.env.local` and add your Bluesky handle and password:
   ```bash
   SSKY_USER=your-handle.bsky.social:your-password
   SSKY_SKIP_REAL_API_TESTS=1
   ```

2. The dev container automatically:
   - Loads environment variables from `.env.local`
   - Installs Claude Code extension
   - Sets up Python 3.14 environment with Docker support

## Running the tests

1. Copy the environment configuration file and set your Bluesky credentials:
   ```bash
   cp tests/_env tests/.env
   ```
   Edit `tests/.env` and add your Bluesky handle and password.

2. Run the tests:
   ```bash
   poetry run pytest --tb=short             # the default tier
   poetry run pytest tests/test_login.py -v # a single file
   ```

### Test tiers

The default run needs no credentials and no network, and it never touches a live
account. Tests that do are marked and excluded unless you ask for them:

```bash
poetry run pytest                                  # default: no network, no writes
poetry run pytest -m 'real_api and not write_api'  # reads from the live API
poetry run pytest -m write_api                     # creates and deletes real records
poetry run pytest -m real_api                      # both
```

`write_api` tests really post, follow, and repost. Selecting them is not enough to run
them: they also require `SSKY_TEST_ACCOUNT_DID` in `tests/.env` to match the DID of the
account you are logged in as, and they skip otherwise. Set it to a dedicated test
account, never your own. The follow test additionally needs `SSKY_TEST_FOLLOW_TARGET`,
which it really follows and then unfollows — point it at another account you control,
because the target gets a notification on every run.

`SSKY_SKIP_REAL_API_TESTS=1` still suppresses the whole real-API tier and will keep
working for one release, but the markers are the mechanism now.

### Running the write tier as the test account

Which account the tests authenticate as is decided by the session file, not by
`tests/.env`: `login_internal()` tries `~/.ssky` first and only falls back to
credentials. So putting the test account in `tests/.env` is not enough — the session
file for your own account still wins, and the guard will refuse to run.

Point `SSKY_CONFIG_PATH` at a separate session file so the test account gets its own:

```bash
SSKY_CONFIG_PATH=~/.ssky-test poetry run pytest -m write_api
```

It has to be set in the environment before pytest starts, because `SskySession` reads it
once at import. The first run logs in with the credentials from `tests/.env` and persists
the session there; later runs reuse it, which is what keeps repeated real logins from
being rate-limited.

Note that the test harness itself still hardcodes `~/.ssky` for its backup and restore
(#108), so under `SSKY_CONFIG_PATH` it manages a file the tests are not using.

Real logins are rate-limited by Bluesky, so the suite logs in once and reuses the
session: `conftest.py` backs up and restores your `~/.ssky` file. Never delete it from
production code.

### What CI covers

Nothing yet — there is no workflow running the tests, so a pull request gets no
automated signal. Adding one, and gating releases on it, is tracked in #107; the default
tier above is what it will run. Until then, run the tests locally before opening a PR.

## Pull requests

- Reference the issue in the PR body with `Fixes #<number>` so it closes on merge, and so
  the issue page shows your PR to the next person checking whether it is taken.
- **Commit messages are a single-line summary.** No body, no emoji, and no
  `Generated with …` / `Co-Authored-By` footers.

A few project rules worth knowing before you change behaviour:

- **[`docs/OUTPUT_FORMATS.md`](docs/OUTPUT_FORMATS.md) is the normative spec** for CLI
  output. If your change alters what a command prints, update the spec in the same PR —
  including its "Known divergences" table, not just the prose.
- **Facet positions are UTF-8 byte offsets, not character indices.** Multibyte text shifts
  them, and facets must not overlap. See `src/ssky/post.py`.
- **The MCP server shells out to the `ssky` CLI on purpose**, so CLI and MCP behaviour
  cannot drift. Don't refactor it into library imports, and don't add MCP-only features —
  capability follows the CLI.
- Raise `SskyError` subclasses rather than generic exceptions.
