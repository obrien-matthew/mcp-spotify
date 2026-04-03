# mcp-spotify

MCP server for Spotify, focused on playlist building and music discovery. 12 granular tools designed for use with Claude and other LLM agents.

## Prerequisites

- Python 3.14+
- [uv](https://docs.astral.sh/uv/)
- A Spotify Premium account (required by Spotify for Web API access)
- A [Spotify Developer](https://developer.spotify.com/) application

## Setup

### 1. Create a Spotify Developer App

1. Go to the [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
2. Click **Create App**
3. Set the **Redirect URI** to `http://127.0.0.1:8888/callback`
4. Note your **Client ID** and **Client Secret**

### 2. Install

```bash
cd mcp-spotify
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
uv run mcp-spotify
```

On first run, a browser window opens for Spotify OAuth authorization. After approving, the token is cached at `~/.spotify_mcp_cache` and subsequent runs authenticate automatically.

## Claude Desktop / Claude Code Configuration

Add to your MCP server config. If installed from PyPI:

```json
{
  "mcpServers": {
    "spotify": {
      "command": "uvx",
      "args": ["mcp-spotify"],
      "env": {
        "SPOTIFY_CLIENT_ID": "your_client_id",
        "SPOTIFY_CLIENT_SECRET": "your_client_secret",
        "SPOTIFY_REDIRECT_URI": "http://127.0.0.1:8888/callback"
      }
    }
  }
}
```

Or if running from a local clone:

```json
{
  "mcpServers": {
    "spotify": {
      "command": "uv",
      "args": ["--directory", "/path/to/mcp-spotify", "run", "mcp-spotify"],
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

### Playlists

| Tool | Parameters | Description |
|------|-----------|-------------|
| `create_playlist` | `name`, `description=""`, `public=True` | Create a new playlist. |
| `add_tracks_to_playlist` | `playlist_id`, `track_ids` | Add tracks to a playlist (max 100). |
| `remove_tracks_from_playlist` | `playlist_id`, `track_ids` | Remove tracks from a playlist. |
| `get_playlist_tracks` | `playlist_id`, `limit=50`, `offset=0` | List tracks in a playlist. |
| `replace_playlist_tracks` | `playlist_id`, `track_ids` | Replace all tracks in a playlist (for reordering). |
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

## Spotify Web API Restrictions

Spotify has progressively locked down its Web API since late 2024. This section documents what's affected and what it means for this project.

### Removed from the Web API (November 2024)

Spotify removed or restricted these endpoints on November 27, 2024. They are **permanently unavailable** to new apps and Development Mode apps, regardless of quota:

| Endpoint | What It Did | Impact |
|----------|-------------|--------|
| `GET /recommendations` | Algorithmic track recommendations based on seed tracks/artists/genres | Was the best tool for playlist building. No replacement exists in the API. |
| `GET /audio-features` | Tempo, energy, danceability, valence, etc. for tracks | Cannot filter or sort tracks by musical attributes. |
| `GET /audio-analysis` | Detailed audio structure (beats, bars, sections, timbre) | Cannot analyze track structure. |
| `GET /browse/featured-playlists` | Spotify's editorial/algorithmic playlist listings | Cannot browse curated playlists. |
| `GET /browse/categories/{id}/playlists` | Playlists within a browse category | Cannot discover playlists by category. |
| Track `preview_url` field | 30-second audio preview URLs | Preview URLs now return `null` for non-grandfathered apps. |

Apps that had Extended Quota Mode approval **before** November 2024 retained access. New apps cannot get access to these endpoints.

### Gated Behind Extended Quota (Effectively Inaccessible)

These endpoints exist but return **403 Forbidden** in Development Mode. They require Extended Quota Mode, which as of May 2025 requires:

- A legally registered business entity (not individuals)
- 250,000+ monthly active users
- An active, launched service in key Spotify markets

This makes Extended Quota **inaccessible for personal projects, hobby apps, and small tools**.

| Endpoint | What It Did |
|----------|-------------|
| `GET /artists/{id}/related-artists` | Discover similar artists. Returns 403. |
| `GET /artists/{id}/top-tracks` | Get an artist's most popular tracks. Returns 403. |

### February 2026 Development Mode Changes

On February 6, 2026, Spotify overhauled Development Mode itself:

- **Spotify Premium required** for app owners (this is now a prerequisite for all Web API access)
- **1 Client ID per developer**
- **Max 5 authorized users** per app
- **Search results capped at 10** per request (down from 50) for new apps
- Several more endpoints restricted (batch-get endpoints, browse categories, new releases, other-user profiles/playlists)

The `POST /users/{user_id}/playlists` endpoint was also removed in favor of `POST /me/playlists` (this server already uses the `/me` variant).

> **Note:** Endpoint restrictions currently apply to **newly created** apps. Existing Dev Mode apps were temporarily exempted after community backlash, but this may change.

### Not Yet Implemented

Potential tools that could be added within current Development Mode access:

| Tool | Endpoint | Description |
|------|----------|-------------|
| `skip_to_next` | `POST /me/player/next` | Skip to the next track in queue. |
| `skip_to_previous` | `POST /me/player/previous` | Skip to the previous track. |
| `get_queue` | `GET /me/player/queue` | View the current playback queue. |
| `add_to_queue` | `POST /me/player/queue` | Add a track to the end of the queue. |
| `set_volume` | `PUT /me/player/volume` | Set playback volume (Premium only). |
| `set_repeat` | `PUT /me/player/repeat` | Set repeat mode (track/context/off). |
| `set_shuffle` | `PUT /me/player/shuffle` | Toggle shuffle on/off. |
| `get_devices` | `GET /me/player/devices` | List available playback devices. |
| `transfer_playback` | `PUT /me/player` | Transfer playback to a different device. |
| `get_album_tracks` | `GET /albums/{id}/tracks` | List tracks on an album. |
| `search_artists` | `GET /search?type=artist` | Search for artists (currently only track search is implemented). |
| `search_albums` | `GET /search?type=album` | Search for albums. |
| `save_tracks` | `PUT /me/tracks` | Save tracks to the user's library. |
| `get_saved_tracks` | `GET /me/tracks` | List the user's saved/liked tracks. |

### Will Never Be Usable (for New Apps)

These would have been valuable for this project but are permanently out of reach:

| Feature | Why It Matters | Status |
|---------|---------------|--------|
| Algorithmic recommendations | The single best way to discover new music programmatically | Removed Nov 2024, no replacement |
| Audio features (tempo, energy, etc.) | Enables filtering tracks by mood, energy, danceability | Removed Nov 2024 |
| Related artists | Core discovery tool for "if you like X, try Y" workflows | Requires Extended Quota (250k MAU) |
| Artist top tracks | Quick way to sample an artist's most popular work | Requires Extended Quota (250k MAU) |
| Editorial/category playlists | Discover Spotify-curated playlists by genre or mood | Removed Nov 2024 |

The practical effect: playlist building relies entirely on `search_tracks` and the user's own listening history (`get_my_top_tracks`, `get_my_top_artists`) for discovery. Claude's own music knowledge fills the gap that the API no longer provides.

## Development

```bash
uv run mcp-spotify           # Run the server
uv run python -m pytest      # Run tests (when added)
```
