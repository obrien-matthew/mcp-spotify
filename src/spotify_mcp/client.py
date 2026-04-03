"""Thin wrapper over spotipy with input validation and clean error handling."""

import sys
from typing import NoReturn

from spotipy.exceptions import SpotifyException

from .auth import get_spotify_client
from .formatting import (
    format_artist_list,
    format_now_playing,
    format_playlist,
    format_playlist_list,
    format_track_list,
)
from .validation import extract_id, validate_limit, validate_offset


class SpotifyError(Exception):
    """User-facing Spotify API error."""

    def __init__(self, message: str, status_code: int | None = None):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class SpotifyClient:
    """Validated, formatted interface to the Spotify API."""

    def __init__(self) -> None:
        self._sp = get_spotify_client()
        self._user_id: str | None = None

    @property
    def user_id(self) -> str:
        if self._user_id is None:
            user = self._sp.current_user()
            if user is None:
                raise SpotifyError("Failed to fetch current user")
            self._user_id = str(user["id"])
        return self._user_id

    def _handle_error(self, e: SpotifyException, action: str) -> NoReturn:
        msg = f"Spotify API error while {action}"
        if e.http_status == 404:
            msg = f"Not found while {action}"
        elif e.http_status == 403:
            msg = f"Permission denied while {action}"
        elif e.http_status == 429:
            msg = f"Rate limited while {action}. Please try again shortly."
        print(f"{msg}: {e}", file=sys.stderr)
        raise SpotifyError(msg, e.http_status) from e

    # -- Discovery --

    def search_tracks(self, query: str, limit: int = 20) -> list[dict]:
        limit = validate_limit(limit)
        try:
            results = self._sp.search(q=query, type="track", limit=limit)
            if results is None:
                return []
            tracks = results["tracks"]["items"]
            return format_track_list(tracks, include_album=True)
        except SpotifyException as e:
            self._handle_error(e, "searching tracks")

    # -- Playlists --

    def create_playlist(
        self,
        name: str,
        description: str = "",
        public: bool = True,
    ) -> dict:
        try:
            # Use /me/playlists endpoint directly -- the /users/{id}/playlists
            # endpoint is blocked for Development Mode apps.
            import requests

            if self._sp.auth_manager is None:
                raise SpotifyError("No auth manager configured")
            token = self._sp.auth_manager.get_access_token(as_dict=False)
            resp = requests.post(
                "https://api.spotify.com/v1/me/playlists",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                },
                json={
                    "name": name,
                    "public": public,
                    "description": description,
                },
            )
            if resp.status_code != 201:
                raise SpotifyError(
                    f"Failed to create playlist (HTTP {resp.status_code})",
                    resp.status_code,
                )
            return format_playlist(resp.json())
        except SpotifyError:
            raise
        except Exception as e:
            raise SpotifyError(f"Failed to create playlist: {e}") from e

    def add_tracks_to_playlist(self, playlist_id: str, track_ids: list[str]) -> None:
        playlist_id = extract_id(playlist_id)
        track_uris = [f"spotify:track:{extract_id(t)}" for t in track_ids]
        try:
            self._sp.playlist_add_items(playlist_id, track_uris)
        except SpotifyException as e:
            self._handle_error(e, "adding tracks to playlist")

    def remove_tracks_from_playlist(
        self, playlist_id: str, track_ids: list[str]
    ) -> None:
        playlist_id = extract_id(playlist_id)
        track_uris = [f"spotify:track:{extract_id(t)}" for t in track_ids]
        try:
            self._sp.playlist_remove_all_occurrences_of_items(playlist_id, track_uris)
        except SpotifyException as e:
            self._handle_error(e, "removing tracks from playlist")

    def replace_playlist_tracks(self, playlist_id: str, track_ids: list[str]) -> None:
        """Replace all tracks in a playlist with the given list, in order."""
        playlist_id = extract_id(playlist_id)
        track_uris = [f"spotify:track:{extract_id(t)}" for t in track_ids]
        try:
            # playlist_replace_items only accepts up to 100 URIs
            self._sp.playlist_replace_items(playlist_id, track_uris[:100])
            # Add remaining tracks in batches of 100
            for i in range(100, len(track_uris), 100):
                batch = track_uris[i : i + 100]
                self._sp.playlist_add_items(playlist_id, batch)
        except SpotifyException as e:
            self._handle_error(e, "replacing playlist tracks")

    def get_playlist_tracks(
        self, playlist_id: str, limit: int = 50, offset: int = 0
    ) -> dict:
        playlist_id = extract_id(playlist_id)
        limit = validate_limit(limit, max_val=100)
        offset = validate_offset(offset)
        try:
            results = self._sp.playlist_items(playlist_id, limit=limit, offset=offset)
            if results is None:
                return {"tracks": [], "total": 0, "offset": offset, "limit": limit}
            tracks = []
            for entry in results.get("items", []):
                track = entry.get("item") or entry.get("track")
                if isinstance(track, dict):
                    tracks.append(track)
            return {
                "tracks": format_track_list(tracks, include_album=True),
                "total": results.get("total", 0),
                "offset": offset,
                "limit": limit,
            }
        except SpotifyException as e:
            self._handle_error(e, "fetching playlist tracks")

    def get_my_playlists(self, limit: int = 50) -> list[dict]:
        limit = validate_limit(limit)
        try:
            results = self._sp.current_user_playlists(limit=limit)
            if results is None:
                return []
            return format_playlist_list(results.get("items", []))
        except SpotifyException as e:
            self._handle_error(e, "fetching playlists")

    # -- Personalization --

    def get_my_top_tracks(
        self, time_range: str = "medium_term", limit: int = 20
    ) -> list[dict]:
        limit = validate_limit(limit)
        if time_range not in ("short_term", "medium_term", "long_term"):
            raise ValueError(
                f"Invalid time_range: '{time_range}'. "
                f"Must be 'short_term', 'medium_term', or 'long_term'."
            )
        try:
            results = self._sp.current_user_top_tracks(
                time_range=time_range, limit=limit
            )
            if results is None:
                return []
            return format_track_list(results.get("items", []), include_album=True)
        except SpotifyException as e:
            self._handle_error(e, "fetching top tracks")

    def get_my_top_artists(
        self, time_range: str = "medium_term", limit: int = 20
    ) -> list[dict]:
        limit = validate_limit(limit)
        if time_range not in ("short_term", "medium_term", "long_term"):
            raise ValueError(
                f"Invalid time_range: '{time_range}'. "
                f"Must be 'short_term', 'medium_term', or 'long_term'."
            )
        try:
            results = self._sp.current_user_top_artists(
                time_range=time_range, limit=limit
            )
            if results is None:
                return []
            return format_artist_list(results.get("items", []))
        except SpotifyException as e:
            self._handle_error(e, "fetching top artists")

    # -- Playback --

    def play_track(self, track_uri: str) -> None:
        track_id = extract_id(track_uri)
        uri = f"spotify:track:{track_id}"
        try:
            self._sp.start_playback(uris=[uri])
        except SpotifyException as e:
            self._handle_error(e, "starting playback")

    def pause_playback(self) -> None:
        try:
            self._sp.pause_playback()
        except SpotifyException as e:
            self._handle_error(e, "pausing playback")

    def get_now_playing(self) -> dict | None:
        try:
            playback = self._sp.current_playback()
            if not playback or not playback.get("item"):
                return None
            return format_now_playing(playback)
        except SpotifyException as e:
            self._handle_error(e, "fetching current playback")
