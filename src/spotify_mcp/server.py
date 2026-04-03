"""MCP server with 13 Spotify tools for playlist building and playback."""

import json

from mcp.server.fastmcp import FastMCP

from .client import SpotifyClient, SpotifyError

mcp = FastMCP("spotify-mcp")

_client: SpotifyClient | None = None


def _get_client() -> SpotifyClient:
    global _client
    if _client is None:
        _client = SpotifyClient()
    return _client


# ---------------------------------------------------------------------------
# Discovery
# ---------------------------------------------------------------------------


@mcp.tool()
def search_tracks(query: str, limit: int = 20) -> str:
    """Search for tracks on Spotify.

    Supports Spotify query syntax for filtering:
      - genre: "genre:rock"
      - year: "year:2020" or "year:2018-2022"
      - artist: "artist:radiohead"
      - combined: "genre:indie year:2020-2024"

    Returns track names, artists, albums, and IDs.
    """
    try:
        results = _get_client().search_tracks(query, limit)
        return json.dumps(results, indent=2)
    except (SpotifyError, ValueError) as e:
        return f"Error: {e}"


@mcp.tool()
def get_artist_top_tracks(artist_id: str) -> str:
    """Get the top tracks for a Spotify artist.

    Accepts a Spotify artist ID (22-char alphanumeric) or full URI
    (spotify:artist:<id>). Returns up to 10 tracks with album info.
    """
    try:
        results = _get_client().get_artist_top_tracks(artist_id)
        return json.dumps(results, indent=2)
    except (SpotifyError, ValueError) as e:
        return f"Error: {e}"


@mcp.tool()
def get_related_artists(artist_id: str) -> str:
    """Get artists similar to a given artist.

    Useful for music discovery when building playlists. Accepts a Spotify
    artist ID or full URI. Returns up to 20 related artists with genres.
    """
    try:
        results = _get_client().get_related_artists(artist_id)
        return json.dumps(results, indent=2)
    except (SpotifyError, ValueError) as e:
        return f"Error: {e}"


# ---------------------------------------------------------------------------
# Playlists
# ---------------------------------------------------------------------------


@mcp.tool()
def create_playlist(
    name: str, description: str = "", public: bool = True
) -> str:
    """Create a new Spotify playlist for the current user.

    Returns the playlist ID and URI for use with other playlist tools.
    """
    try:
        result = _get_client().create_playlist(name, description, public)
        return json.dumps(result, indent=2)
    except (SpotifyError, ValueError) as e:
        return f"Error: {e}"


@mcp.tool()
def add_tracks_to_playlist(playlist_id: str, track_ids: list[str]) -> str:
    """Add tracks to a Spotify playlist.

    Accepts a list of track IDs or URIs (max 100 per call). Tracks are
    appended to the end of the playlist.
    """
    try:
        _get_client().add_tracks_to_playlist(playlist_id, track_ids)
        count = len(track_ids)
        return f"Added {count} track{'s' if count != 1 else ''} to playlist."
    except (SpotifyError, ValueError) as e:
        return f"Error: {e}"


@mcp.tool()
def remove_tracks_from_playlist(
    playlist_id: str, track_ids: list[str]
) -> str:
    """Remove tracks from a Spotify playlist.

    Removes all occurrences of each track. Accepts track IDs or URIs
    (max 100 per call).
    """
    try:
        _get_client().remove_tracks_from_playlist(playlist_id, track_ids)
        count = len(track_ids)
        return f"Removed {count} track{'s' if count != 1 else ''} from playlist."
    except (SpotifyError, ValueError) as e:
        return f"Error: {e}"


@mcp.tool()
def get_playlist_tracks(
    playlist_id: str, limit: int = 50, offset: int = 0
) -> str:
    """Get the tracks in a Spotify playlist.

    Supports pagination via limit (max 100) and offset. Returns track
    names, artists, IDs, and total count.
    """
    try:
        result = _get_client().get_playlist_tracks(playlist_id, limit, offset)
        return json.dumps(result, indent=2)
    except (SpotifyError, ValueError) as e:
        return f"Error: {e}"


@mcp.tool()
def get_my_playlists(limit: int = 50) -> str:
    """List the current user's Spotify playlists.

    Returns playlist names, IDs, track counts, and ownership info.
    """
    try:
        results = _get_client().get_my_playlists(limit)
        return json.dumps(results, indent=2)
    except (SpotifyError, ValueError) as e:
        return f"Error: {e}"


# ---------------------------------------------------------------------------
# Personalization
# ---------------------------------------------------------------------------


@mcp.tool()
def get_my_top_tracks(
    time_range: str = "medium_term", limit: int = 20
) -> str:
    """Get the current user's top tracks on Spotify.

    time_range options:
      - "short_term": approximately last 4 weeks
      - "medium_term": approximately last 6 months (default)
      - "long_term": all time

    Useful as a seed for building personalized playlists.
    """
    try:
        results = _get_client().get_my_top_tracks(time_range, limit)
        return json.dumps(results, indent=2)
    except (SpotifyError, ValueError) as e:
        return f"Error: {e}"


@mcp.tool()
def get_my_top_artists(
    time_range: str = "medium_term", limit: int = 20
) -> str:
    """Get the current user's top artists on Spotify.

    time_range options:
      - "short_term": approximately last 4 weeks
      - "medium_term": approximately last 6 months (default)
      - "long_term": all time

    Useful for discovering related artists when building playlists.
    """
    try:
        results = _get_client().get_my_top_artists(time_range, limit)
        return json.dumps(results, indent=2)
    except (SpotifyError, ValueError) as e:
        return f"Error: {e}"


# ---------------------------------------------------------------------------
# Playback
# ---------------------------------------------------------------------------


@mcp.tool()
def play_track(track_uri: str) -> str:
    """Start playing a track on Spotify.

    Requires an active Spotify device (open Spotify on any device first).
    Accepts a Spotify track URI (spotify:track:<id>) or bare track ID.
    """
    try:
        _get_client().play_track(track_uri)
        return "Playback started."
    except (SpotifyError, ValueError) as e:
        return f"Error: {e}"


@mcp.tool()
def pause_playback() -> str:
    """Pause the current Spotify playback."""
    try:
        _get_client().pause_playback()
        return "Playback paused."
    except (SpotifyError, ValueError) as e:
        return f"Error: {e}"


@mcp.tool()
def get_now_playing() -> str:
    """Get information about the currently playing track on Spotify.

    Returns track name, artist, album, progress, and playback state.
    Returns a message if nothing is currently playing.
    """
    try:
        result = _get_client().get_now_playing()
        if result is None:
            return "Nothing is currently playing."
        return json.dumps(result, indent=2)
    except (SpotifyError, ValueError) as e:
        return f"Error: {e}"
