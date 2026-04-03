# spotify-mcp

MCP server for Spotify, focused on playlist building and music discovery. 13 granular tools designed for use with Claude and other LLM agents.

## Prerequisites

- Python 3.14+
- [uv](https://docs.astral.sh/uv/)
- A Spotify account (free or premium)
- A [Spotify Developer](https://developer.spotify.com/) application

## Setup

### 1. Create a Spotify Developer App

1. Go to the [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
2. Click **Create App**
3. Set the **Redirect URI** to `http://127.0.0.1:8888/callback`
4. Note your **Client ID** and **Client Secret**

### 2. Install

```bash
cd spotify-mcp
uv sync
```

### 3. Configure Environment Variables

Set these before running the server:

```bash
export SPOTIFY_CLIENT_ID="your_client_id"
export SPOTIFY_CLIENT_SECRET="your_client_secret"
export SPOTIFY_REDIRECT_URI="http://127.0.0.1:8888/callback"
```

### 4. First Run (Authentication)

```bash
uv run spotify-mcp
```

On first run, a browser window opens for Spotify OAuth authorization. After approving, the token is cached at `~/.spotify_mcp_cache` and subsequent runs authenticate automatically.

## Claude Desktop / Claude Code Configuration

Add to your MCP server config:

```json
{
  "mcpServers": {
    "spotify": {
      "command": "uv",
      "args": ["--directory", "/path/to/spotify-mcp", "run", "spotify-mcp"],
      "env": {
        "SPOTIFY_CLIENT_ID": "your_client_id",
        "SPOTIFY_CLIENT_SECRET": "your_client_secret",
        "SPOTIFY_REDIRECT_URI": "http://127.0.0.1:8888/callback"
      }
    }
  }
}
```

## Tools

### Discovery

| Tool | Parameters | Description |
|------|-----------|-------------|
| `search_tracks` | `query`, `limit=20` | Search for tracks. Supports `genre:`, `year:`, `artist:` filters. |
| `get_artist_top_tracks` | `artist_id` | Get top tracks for an artist (up to 10). *Requires extended quota.* |
| `get_related_artists` | `artist_id` | Get similar artists (up to 20) with genres. *Requires extended quota.* |

> **Note:** `get_artist_top_tracks` and `get_related_artists` require your Spotify app to have extended quota access. Development Mode apps will get 403 errors on these endpoints. See `docs/action-items/002-apply-for-extended-quota.md` for how to apply.

### Playlists

| Tool | Parameters | Description |
|------|-----------|-------------|
| `create_playlist` | `name`, `description=""`, `public=True` | Create a new playlist. |
| `add_tracks_to_playlist` | `playlist_id`, `track_ids` | Add tracks to a playlist (max 100). |
| `remove_tracks_from_playlist` | `playlist_id`, `track_ids` | Remove tracks from a playlist. |
| `get_playlist_tracks` | `playlist_id`, `limit=50`, `offset=0` | List tracks in a playlist. |
| `get_my_playlists` | `limit=50` | List your playlists. |

### Personalization

| Tool | Parameters | Description |
|------|-----------|-------------|
| `get_my_top_tracks` | `time_range="medium_term"`, `limit=20` | Your most-played tracks. |
| `get_my_top_artists` | `time_range="medium_term"`, `limit=20` | Your most-played artists. |

`time_range` options: `short_term` (~4 weeks), `medium_term` (~6 months), `long_term` (all time).

### Playback

| Tool | Parameters | Description |
|------|-----------|-------------|
| `play_track` | `track_uri` | Play a track (requires active Spotify device). |
| `pause_playback` | (none) | Pause playback. |
| `get_now_playing` | (none) | Get current track info. |

## OAuth Scopes

This server requests the minimum scopes needed:

- `user-read-playback-state`, `user-modify-playback-state`, `user-read-currently-playing` -- playback
- `playlist-read-private`, `playlist-read-collaborative`, `playlist-modify-public`, `playlist-modify-private` -- playlists
- `user-top-read` -- personalization

## Development

```bash
uv run spotify-mcp          # Run the server
uv run python -m pytest      # Run tests (when added)
```
