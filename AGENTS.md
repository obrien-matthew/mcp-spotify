# mcp-spotify

MCP server for Spotify.

## Conventions

Follows the shared conventions from [mcp-template](https://github.com/obrien-matthew/mcp-template) (see its AGENTS.md for full rationale): data tools return real `dict`/`list[dict]` directly (never `json.dumps`); action/status tools may return a human-readable `-> str`, as may tools whose result is genuinely a single string (IDs, versions); errors are raised, never caught and returned as strings; empty results are empty containers (`{}`, `[]`), not sentinel messages.

## Layout

- `src/spotify_mcp/server.py` -- MCP tool definitions
- `src/spotify_mcp/client.py` -- HTTP/API client wrapper
- `src/spotify_mcp/formatting.py` -- response formatters that produce LLM-friendly dicts (no `json.dumps`)
- `src/spotify_mcp/validation.py` -- input validators
- `src/spotify_mcp/auth.py` -- credential loading

## Workflow

```bash
uv sync                       # install deps
uv run pytest -q              # run tests
uv run ruff check .           # lint
uv run ruff format .          # format
uv run pyright src/           # typecheck
lefthook install              # set up git hooks (one-time)
```
