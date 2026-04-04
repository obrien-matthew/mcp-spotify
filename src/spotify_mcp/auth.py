"""Spotify OAuth setup and authenticated client singleton."""

import os
import sys
from pathlib import Path

import spotipy
from spotipy.oauth2 import CacheFileHandler, SpotifyOAuth

SCOPES = " ".join(
    [
        # Playback
        "user-read-playback-state",
        "user-modify-playback-state",
        "user-read-currently-playing",
        # Playlists
        "playlist-read-private",
        "playlist-read-collaborative",
        "playlist-modify-public",
        "playlist-modify-private",
        # Personalization
        "user-top-read",
        # Library
        "user-library-read",
    ]
)

_client: spotipy.Spotify | None = None


def _normalize_redirect_uri(uri: str) -> str:
    """Replace 'localhost' with '127.0.0.1' -- required by Spotify."""
    return uri.replace("localhost", "127.0.0.1")


def get_spotify_client() -> spotipy.Spotify:
    """Return a cached, authenticated Spotify client.

    Reads SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET, and SPOTIFY_REDIRECT_URI
    from environment variables. Token is cached at ~/.spotify_mcp_cache.

    Raises RuntimeError if required env vars are missing.
    """
    global _client
    if _client is not None:
        return _client

    client_id = os.environ.get("SPOTIFY_CLIENT_ID")
    client_secret = os.environ.get("SPOTIFY_CLIENT_SECRET")
    redirect_uri = os.environ.get(
        "SPOTIFY_REDIRECT_URI", "http://127.0.0.1:8888/callback"
    )

    if not client_id or not client_secret:
        raise RuntimeError(
            "SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET environment variables "
            "are required. See README.md for setup instructions."
        )

    redirect_uri = _normalize_redirect_uri(redirect_uri)
    cache_path = Path.home() / ".spotify_mcp_cache"

    auth_manager = SpotifyOAuth(
        client_id=client_id,
        client_secret=client_secret,
        redirect_uri=redirect_uri,
        scope=SCOPES,
        cache_handler=CacheFileHandler(cache_path=str(cache_path)),
        open_browser=True,
    )

    _client = spotipy.Spotify(auth_manager=auth_manager)

    # Verify auth works by fetching current user
    try:
        _client.current_user()
    except spotipy.SpotifyException as e:
        _client = None
        print(f"Spotify auth failed: {e}", file=sys.stderr)
        raise RuntimeError(
            "Failed to authenticate with Spotify. "
            "Please check your credentials and try again."
        ) from e

    return _client
