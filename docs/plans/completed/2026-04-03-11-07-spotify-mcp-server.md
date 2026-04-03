# Plan: Spotify MCP Server for Playlist Building

## Context

Building a from-scratch Spotify MCP server in Python, focused on playlist-building workflows with Claude, using the modern `FastMCP` decorator API.

**Target repo:** `/Users/matthew/src/obrien-matthew/spotify-mcp`
**Stack:** Python 3.12+, `mcp` SDK (FastMCP), `spotipy`, `uv` for all Python tooling

---

## Project Structure

```
spotify-mcp/
  pyproject.toml
  .python-version
  .gitignore
  README.md
  src/
    spotify_mcp/
      __init__.py        # Entry point (main)
      server.py          # FastMCP instance + 13 tool definitions
      auth.py            # SpotifyOAuth setup, scopes, client singleton
      client.py          # Thin wrapper over spotipy with validation + error handling
      formatting.py      # LLM-friendly response formatting
      validation.py      # Input validation helpers (IDs, URIs, limits)
```

---

## Phase 1: Project Scaffolding

Create the repo directory and initialize with uv.

- `uv init --lib /Users/matthew/src/obrien-matthew/spotify-mcp`
- Update `pyproject.toml`:
  - Dependencies: `mcp>=1.27.0,<2`, `spotipy>=2.24.0`
  - Entry point: `spotify-mcp = "spotify_mcp:main"`
  - Requires Python >=3.12
- `.python-version`: `3.12`
- `.gitignore`: `.cache`, `__pycache__/`, `.env`, `.spotify_cache`, `*.egg-info/`, `dist/`
- `git init` + initial commit

**Commit 1:** Project scaffolding

---

## Phase 2: Auth + Validation Modules

### `auth.py`
- Read `SPOTIFY_CLIENT_ID`, `SPOTIFY_CLIENT_SECRET`, `SPOTIFY_REDIRECT_URI` from env vars
- Normalize redirect URI (`localhost` -> `127.0.0.1`)
- Minimum OAuth scopes (8 total -- only what the 13 tools need):
  ```
  user-read-playback-state, user-modify-playback-state, user-read-currently-playing,
  playlist-read-private, playlist-read-collaborative, playlist-modify-public,
  playlist-modify-private, user-top-read
  ```
- `get_spotify_client() -> spotipy.Spotify`: lazy singleton, uses `SpotifyOAuth` with `CacheFileHandler(cache_path="~/.spotify_cache")` and `open_browser=True`
- Token refresh handled atomically by spotipy's built-in `validate_token`

### `validation.py`
- `validate_spotify_id(value, label) -> str`: checks 22-char base62 pattern
- `validate_limit(value, max_val=50) -> int`: clamps to 1..max
- `validate_offset(value) -> int`: ensures >= 0
- `extract_id(value) -> str`: accepts bare ID or `spotify:type:id` URI, returns just the ID
- All raise `ValueError` with user-friendly messages (no `assert`)

**Commit 2:** Auth and validation modules

---

## Phase 3: Client Wrapper + Formatting

### `client.py`
- `SpotifyClient` class wrapping `spotipy.Spotify`
- Validates inputs via `validation.py`, calls spotipy, formats via `formatting.py`
- Custom `SpotifyError(message, status_code)` exception -- catches `SpotifyException`, re-raises with clean user-facing message
- Lazy `user_id` property for playlist creation
- Methods:
  - `search_tracks(query, limit) -> list[dict]`
  - `get_artist_top_tracks(artist_id) -> list[dict]`
  - `get_related_artists(artist_id) -> list[dict]`
  - `create_playlist(name, description, public) -> dict`
  - `add_tracks_to_playlist(playlist_id, track_ids) -> None`
  - `remove_tracks_from_playlist(playlist_id, track_ids) -> None`
  - `get_playlist_tracks(playlist_id, limit, offset) -> dict`
  - `get_my_playlists(limit) -> list[dict]`
  - `get_my_top_tracks(time_range, limit) -> list[dict]`
  - `get_my_top_artists(time_range, limit) -> list[dict]`
  - `play_track(track_uri) -> None`
  - `pause_playback() -> None`
  - `get_now_playing() -> dict | None`

### `formatting.py`
- `format_track(track, include_album=False) -> dict`: `{name, id, uri, artists, duration_ms, album?}`
- `format_artist(artist) -> dict`: `{name, id, uri, genres}`
- `format_playlist(playlist) -> dict`: `{name, id, uri, owner, total_tracks, public, description?}`
- `format_now_playing(playback) -> dict`: `{track, artist, album, progress_ms, duration_ms, is_playing, device}`
- List variants for batch formatting
- Only fields useful to an LLM -- no images, external URLs, or href links

**Commit 3:** Client wrapper and formatting

---

## Phase 4: MCP Server + Entry Point

### `server.py`
- `mcp = FastMCP("spotify-mcp")`
- Module-level `_client` singleton, initialized on first tool call
- 13 tools via `@mcp.tool()` decorators with full type hints and docstrings (FastMCP auto-generates JSON schema)
- Each tool: try/except, returns JSON string on success, `"Error: ..."` string on failure, never raises
- Tool list:

| Tool | Key params | Purpose |
|------|-----------|---------|
| `search_tracks` | query, limit=20 | Find tracks (supports `genre:`, `year:`, `artist:` filters) |
| `get_artist_top_tracks` | artist_id | Top 10 tracks for an artist |
| `get_related_artists` | artist_id | Up to 20 similar artists |
| `create_playlist` | name, description="", public=True | Create playlist, returns ID |
| `add_tracks_to_playlist` | playlist_id, track_ids (max 100) | Append tracks |
| `remove_tracks_from_playlist` | playlist_id, track_ids (max 100) | Remove tracks |
| `get_playlist_tracks` | playlist_id, limit=50, offset=0 | List tracks with pagination |
| `get_my_playlists` | limit=50 | User's playlists |
| `get_my_top_tracks` | time_range="medium_term", limit=20 | Personalization seed |
| `get_my_top_artists` | time_range="medium_term", limit=20 | Personalization seed |
| `play_track` | track_uri | Start playback |
| `pause_playback` | (none) | Pause |
| `get_now_playing` | (none) | Current track info |

### `__init__.py`
```python
from .server import mcp

def main():
    mcp.run(transport="stdio")
```

**Commit 4:** MCP server with all 13 tools

---

## Phase 5: README + Action Items

### `README.md`
- Overview and tool reference table
- Prerequisites (Spotify Developer account + app)
- Installation: `uv sync`
- Configuration: env vars (CLIENT_ID, CLIENT_SECRET, REDIRECT_URI)
- Claude Desktop config snippet (using `uv run spotify-mcp`)
- First-time auth walkthrough
- Development: `uv run spotify-mcp`

### Action item for user
- Register a Spotify Developer account and create an app at https://developer.spotify.com
- Set redirect URI to `http://127.0.0.1:8888/callback` in the app dashboard
- Note the client ID and secret

**Commit 5:** README and documentation

---

## Verification

1. `uv run python -c "from spotify_mcp.server import mcp; print(mcp)"` -- import works
2. `uv run python -c "from spotify_mcp.server import mcp; print([t for t in mcp._tool_manager._tools.keys()])"` -- all 13 tools registered
3. With env vars set: `uv run spotify-mcp` -- should open browser for OAuth on first run
4. `npx @modelcontextprotocol/inspector` -- connect over stdio, test tools interactively
5. Add to Claude Desktop/Code config and verify tools appear

---

## Key Design Decisions

| Aspect | Decision |
|--------|----------|
| Tool design | 13 granular tools (focused scope) |
| Validation | Dedicated module, `ValueError` |
| Error handling | Clean user messages, stderr logging |
| OAuth scopes | 8 (minimum needed) |
| Token refresh | spotipy built-in (atomic) |
| Response format | Structured dicts (JSON) |
| Tooling | uv |
