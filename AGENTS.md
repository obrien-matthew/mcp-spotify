# mcp-spotify

MCP server for Spotify.

## Conventions

### Tool return types: real dicts/lists, not stringified JSON

FastMCP populates the `structuredContent` field of a tool result from the tool's
return value. When a tool is annotated `-> str` and returns `json.dumps(data,
indent=2)`, FastMCP wraps the string as `{"result": "<the json.dumps string>"}` --
clients see an escape-laden blob instead of structured data.

- **Data tools** (search, list, get, paginated results): annotate `-> dict` or
  `-> list[dict]` and return the value directly. Do not call `json.dumps()`.
- **Action/status tools** (delete-confirmation, scan, restart): `-> str` is fine
  when the result is inherently a human-readable confirmation message.
- **Errors:** raise the underlying exception. FastMCP catches it and emits a proper
  MCP error response with `isError=true`. Do not wrap tools in
  `try: ... except Exception: return f"Error: {e}"` -- that hides failures inside
  successful responses.
- **Empty data:** prefer empty containers (`{}`, `[]`) over sentinel strings like
  `"No data available."` so downstream callers can treat absence-of-data uniformly.

### When you must keep `-> str`

Some tools genuinely return a single string (e.g. resolving a vanity URL to an ID,
`get_server_version` returning a semver string). FastMCP wraps these as
`{"result": "value"}` -- still proper JSON, no escaping. That's fine and idiomatic.

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
