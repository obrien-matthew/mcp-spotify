"""MCP server with Spotify tools for playlist building and playback."""

import json
from importlib.metadata import PackageNotFoundError, version

from mcp.server.fastmcp import FastMCP

from .client import SpotifyClient, SpotifyError

mcp = FastMCP("mcp-spotify")


@mcp.tool()
def get_server_version() -> str:
    """Return the installed version of the mcp-spotify server."""
    try:
        return version("mcp-spotify")
    except PackageNotFoundError:
        return "unknown"


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
def search_artists(query: str, limit: int = 20) -> str:
    """Search for artists on Spotify.

    Supports the same query syntax as search_tracks. Returns artist names,
    genres, and IDs. Useful for finding an artist ID to explore their catalog.
    """
    try:
        results = _get_client().search_artists(query, limit)
        return json.dumps(results, indent=2)
    except (SpotifyError, ValueError) as e:
        return f"Error: {e}"


@mcp.tool()
def search_albums(query: str, limit: int = 20) -> str:
    """Search for albums on Spotify.

    Returns album names, artists, release dates, and IDs. Use get_album_tracks
    to list the tracks on a found album.
    """
    try:
        results = _get_client().search_albums(query, limit)
        return json.dumps(results, indent=2)
    except (SpotifyError, ValueError) as e:
        return f"Error: {e}"


@mcp.tool()
def get_album_tracks(album_id: str, limit: int = 50) -> str:
    """Get all tracks on a Spotify album.

    Accepts a Spotify album ID or full URI. Returns track names, artists,
    and IDs. Useful for adding an entire album to a playlist.
    """
    try:
        result = _get_client().get_album_tracks(album_id, limit)
        return json.dumps(result, indent=2)
    except (SpotifyError, ValueError) as e:
        return f"Error: {e}"


# ---------------------------------------------------------------------------
# Library
# ---------------------------------------------------------------------------


@mcp.tool()
def get_saved_tracks(limit: int = 20, offset: int = 0) -> str:
    """Get the current user's saved (liked) tracks.

    Returns tracks from the user's library, sorted by most recently saved.
    Supports pagination via limit (max 50) and offset. A rich signal for
    playlist building since liked songs reflect explicit user preference.
    """
    try:
        result = _get_client().get_saved_tracks(limit, offset)
        return json.dumps(result, indent=2)
    except (SpotifyError, ValueError) as e:
        return f"Error: {e}"


# ---------------------------------------------------------------------------
# Playlists
# ---------------------------------------------------------------------------


@mcp.tool()
def create_playlist(name: str, description: str = "", public: bool = True) -> str:
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
def remove_tracks_from_playlist(playlist_id: str, track_ids: list[str]) -> str:
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
def replace_playlist_tracks(playlist_id: str, track_ids: list[str]) -> str:
    """Replace all tracks in a playlist with the given list, in order.

    This is useful for reordering a playlist. First get the current tracks
    with get_playlist_tracks, reorder the IDs as desired, then pass the
    full ordered list here. The playlist will contain exactly these tracks
    in exactly this order.

    Accepts track IDs or URIs. No limit on total tracks (batched internally).
    """
    try:
        _get_client().replace_playlist_tracks(playlist_id, track_ids)
        count = len(track_ids)
        return f"Replaced playlist with {count} tracks in the specified order."
    except (SpotifyError, ValueError) as e:
        return f"Error: {e}"


@mcp.tool()
def follow_playlist(playlist_id: str) -> str:
    """Follow (save) a Spotify playlist to your library.

    Accepts a playlist ID or URI. Use this to save playlists found via
    search or shared by others.
    """
    try:
        _get_client().follow_playlist(playlist_id)
        return "Playlist followed."
    except (SpotifyError, ValueError) as e:
        return f"Error: {e}"


@mcp.tool()
def unfollow_playlist(playlist_id: str) -> str:
    """Unfollow (remove) a Spotify playlist from your library.

    For playlists you own, this is the only way to 'delete' them --
    Spotify has no true delete. The playlist will no longer appear in
    your library or profile.
    """
    try:
        _get_client().unfollow_playlist(playlist_id)
        return "Playlist unfollowed."
    except (SpotifyError, ValueError) as e:
        return f"Error: {e}"


@mcp.tool()
def get_playlist_tracks(playlist_id: str, limit: int = 50, offset: int = 0) -> str:
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
def get_my_top_tracks(time_range: str = "medium_term", limit: int = 20) -> str:
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
def get_my_top_artists(time_range: str = "medium_term", limit: int = 20) -> str:
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
def add_to_queue(track_uri: str) -> str:
    """Add a track to the end of the playback queue.

    Requires an active Spotify device. Accepts a track URI or bare track ID.
    """
    try:
        _get_client().add_to_queue(track_uri)
        return "Track added to queue."
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
