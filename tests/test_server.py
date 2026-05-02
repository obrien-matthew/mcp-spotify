"""Tests for MCP server tool functions with mocked SpotifyClient."""

import json
from importlib.metadata import version
from unittest.mock import MagicMock, patch

import pytest

from spotify_mcp import server
from spotify_mcp.client import SpotifyError

# -- Fixtures --

TRACK = {"name": "Bohemian Rhapsody", "id": "4u7EnebtmKWzUH433cf5Qv"}
ARTIST = {"name": "Queen", "id": "1dfeR4HaWDbWqFHLkxsg1d", "genres": ["rock"]}
ALBUM = {"name": "A Night at the Opera", "id": "1GbtB4zTqAsyfZEsm1RZfx"}
PLAYLIST = {"name": "My Playlist", "id": "37i9dQZF1DXcBWIGoYBM5M"}
NOW_PLAYING = {
    "track": "Bohemian Rhapsody",
    "artist": "Queen",
    "is_playing": True,
}


@pytest.fixture(autouse=True)
def mock_client():
    """Replace _get_client with a mock for every test."""
    mock = MagicMock()
    with patch.object(server, "_get_client", return_value=mock):
        yield mock


# -- Discovery --


class TestSearchTracksTool:
    def test_returns_json(self, mock_client):
        mock_client.search_tracks.return_value = [TRACK]
        result = server.search_tracks("bohemian rhapsody")
        parsed = json.loads(result)
        assert len(parsed) == 1
        assert parsed[0]["name"] == "Bohemian Rhapsody"

    def test_passes_limit(self, mock_client):
        mock_client.search_tracks.return_value = []
        server.search_tracks("test", limit=10)
        mock_client.search_tracks.assert_called_once_with("test", 10)

    def test_default_limit(self, mock_client):
        mock_client.search_tracks.return_value = []
        server.search_tracks("test")
        mock_client.search_tracks.assert_called_once_with("test", 20)

    def test_spotify_error(self, mock_client):
        mock_client.search_tracks.side_effect = SpotifyError("Rate limited")
        result = server.search_tracks("test")
        assert result == "Error: Rate limited"

    def test_value_error(self, mock_client):
        mock_client.search_tracks.side_effect = ValueError("bad input")
        result = server.search_tracks("test")
        assert result == "Error: bad input"


class TestSearchArtistsTool:
    def test_returns_json(self, mock_client):
        mock_client.search_artists.return_value = [ARTIST]
        result = server.search_artists("queen")
        parsed = json.loads(result)
        assert parsed[0]["name"] == "Queen"

    def test_passes_args(self, mock_client):
        mock_client.search_artists.return_value = []
        server.search_artists("queen", limit=5)
        mock_client.search_artists.assert_called_once_with("queen", 5)

    def test_error_handling(self, mock_client):
        mock_client.search_artists.side_effect = SpotifyError("Not found")
        assert server.search_artists("x") == "Error: Not found"


class TestSearchAlbumsTool:
    def test_returns_json(self, mock_client):
        mock_client.search_albums.return_value = [ALBUM]
        result = server.search_albums("a night at the opera")
        parsed = json.loads(result)
        assert parsed[0]["name"] == "A Night at the Opera"

    def test_passes_args(self, mock_client):
        mock_client.search_albums.return_value = []
        server.search_albums("test", limit=3)
        mock_client.search_albums.assert_called_once_with("test", 3)

    def test_error_handling(self, mock_client):
        mock_client.search_albums.side_effect = SpotifyError("Oops")
        assert server.search_albums("x") == "Error: Oops"


class TestGetAlbumTracksTool:
    def test_returns_json(self, mock_client):
        mock_client.get_album_tracks.return_value = {"tracks": [TRACK], "total": 12}
        result = server.get_album_tracks("1GbtB4zTqAsyfZEsm1RZfx")
        parsed = json.loads(result)
        assert parsed["total"] == 12
        assert len(parsed["tracks"]) == 1

    def test_passes_args(self, mock_client):
        mock_client.get_album_tracks.return_value = {"tracks": [], "total": 0}
        server.get_album_tracks("abc", limit=10)
        mock_client.get_album_tracks.assert_called_once_with("abc", 10)

    def test_error_handling(self, mock_client):
        mock_client.get_album_tracks.side_effect = SpotifyError("Not found")
        assert server.get_album_tracks("bad") == "Error: Not found"


# -- Library --


class TestGetSavedTracksTool:
    def test_returns_json(self, mock_client):
        mock_client.get_saved_tracks.return_value = {
            "tracks": [TRACK],
            "total": 100,
            "offset": 0,
            "limit": 20,
        }
        result = server.get_saved_tracks()
        parsed = json.loads(result)
        assert parsed["total"] == 100
        assert len(parsed["tracks"]) == 1

    def test_passes_args(self, mock_client):
        mock_client.get_saved_tracks.return_value = {
            "tracks": [],
            "total": 0,
            "offset": 10,
            "limit": 5,
        }
        server.get_saved_tracks(limit=5, offset=10)
        mock_client.get_saved_tracks.assert_called_once_with(5, 10)

    def test_error_handling(self, mock_client):
        mock_client.get_saved_tracks.side_effect = SpotifyError("Auth failed")
        assert server.get_saved_tracks() == "Error: Auth failed"


# -- Playlists --


class TestCreatePlaylistTool:
    def test_returns_json(self, mock_client):
        mock_client.create_playlist.return_value = PLAYLIST
        result = server.create_playlist("My Playlist")
        parsed = json.loads(result)
        assert parsed["name"] == "My Playlist"

    def test_passes_all_args(self, mock_client):
        mock_client.create_playlist.return_value = PLAYLIST
        server.create_playlist("Test", description="desc", public=False)
        mock_client.create_playlist.assert_called_once_with("Test", "desc", False)

    def test_error_handling(self, mock_client):
        mock_client.create_playlist.side_effect = SpotifyError("No auth manager")
        assert server.create_playlist("Test") == "Error: No auth manager"


class TestAddTracksToPlaylistTool:
    def test_success_message_singular(self, mock_client):
        result = server.add_tracks_to_playlist("pid", ["tid"])
        assert result == "Added 1 track to playlist."

    def test_success_message_plural(self, mock_client):
        result = server.add_tracks_to_playlist("pid", ["a", "b", "c"])
        assert result == "Added 3 tracks to playlist."
        mock_client.add_tracks_to_playlist.assert_called_once_with(
            "pid", ["a", "b", "c"]
        )

    def test_error_handling(self, mock_client):
        mock_client.add_tracks_to_playlist.side_effect = SpotifyError("Not found")
        result = server.add_tracks_to_playlist("pid", ["tid"])
        assert result == "Error: Not found"


class TestRemoveTracksFromPlaylistTool:
    def test_success_message_singular(self, mock_client):
        result = server.remove_tracks_from_playlist("pid", ["tid"])
        assert result == "Removed 1 track from playlist."

    def test_success_message_plural(self, mock_client):
        result = server.remove_tracks_from_playlist("pid", ["a", "b"])
        assert result == "Removed 2 tracks from playlist."

    def test_error_handling(self, mock_client):
        mock_client.remove_tracks_from_playlist.side_effect = SpotifyError("Denied")
        result = server.remove_tracks_from_playlist("pid", ["tid"])
        assert result == "Error: Denied"


class TestReplacePlaylistTracksTool:
    def test_success_message(self, mock_client):
        result = server.replace_playlist_tracks("pid", ["a", "b", "c"])
        assert result == "Replaced playlist with 3 tracks in the specified order."
        mock_client.replace_playlist_tracks.assert_called_once_with(
            "pid", ["a", "b", "c"]
        )

    def test_error_handling(self, mock_client):
        mock_client.replace_playlist_tracks.side_effect = SpotifyError("Failed")
        result = server.replace_playlist_tracks("pid", ["a"])
        assert result == "Error: Failed"


class TestFollowPlaylistTool:
    def test_success_message(self, mock_client):
        result = server.follow_playlist("pid")
        assert result == "Playlist followed."
        mock_client.follow_playlist.assert_called_once_with("pid")

    def test_error_handling(self, mock_client):
        mock_client.follow_playlist.side_effect = SpotifyError("Not found")
        assert server.follow_playlist("pid") == "Error: Not found"


class TestUnfollowPlaylistTool:
    def test_success_message(self, mock_client):
        result = server.unfollow_playlist("pid")
        assert result == "Playlist unfollowed."
        mock_client.unfollow_playlist.assert_called_once_with("pid")

    def test_error_handling(self, mock_client):
        mock_client.unfollow_playlist.side_effect = SpotifyError("Denied")
        assert server.unfollow_playlist("pid") == "Error: Denied"


class TestGetPlaylistTracksTool:
    def test_returns_json(self, mock_client):
        mock_client.get_playlist_tracks.return_value = {
            "tracks": [TRACK],
            "total": 80,
            "offset": 0,
            "limit": 50,
        }
        result = server.get_playlist_tracks("pid")
        parsed = json.loads(result)
        assert parsed["total"] == 80

    def test_passes_args(self, mock_client):
        mock_client.get_playlist_tracks.return_value = {
            "tracks": [],
            "total": 0,
            "offset": 20,
            "limit": 10,
        }
        server.get_playlist_tracks("pid", limit=10, offset=20)
        mock_client.get_playlist_tracks.assert_called_once_with("pid", 10, 20)

    def test_error_handling(self, mock_client):
        mock_client.get_playlist_tracks.side_effect = SpotifyError("Not found")
        assert server.get_playlist_tracks("pid") == "Error: Not found"


class TestGetMyPlaylistsTool:
    def test_returns_json(self, mock_client):
        mock_client.get_my_playlists.return_value = [PLAYLIST]
        result = server.get_my_playlists()
        parsed = json.loads(result)
        assert len(parsed) == 1
        assert parsed[0]["name"] == "My Playlist"

    def test_passes_limit(self, mock_client):
        mock_client.get_my_playlists.return_value = []
        server.get_my_playlists(limit=10)
        mock_client.get_my_playlists.assert_called_once_with(10)

    def test_error_handling(self, mock_client):
        mock_client.get_my_playlists.side_effect = SpotifyError("Oops")
        assert server.get_my_playlists() == "Error: Oops"


# -- Personalization --


class TestGetMyTopTracksTool:
    def test_returns_json(self, mock_client):
        mock_client.get_my_top_tracks.return_value = [TRACK]
        result = server.get_my_top_tracks()
        parsed = json.loads(result)
        assert parsed[0]["name"] == "Bohemian Rhapsody"

    def test_passes_args(self, mock_client):
        mock_client.get_my_top_tracks.return_value = []
        server.get_my_top_tracks(time_range="short_term", limit=5)
        mock_client.get_my_top_tracks.assert_called_once_with("short_term", 5)

    def test_error_handling(self, mock_client):
        mock_client.get_my_top_tracks.side_effect = ValueError("Invalid time_range")
        assert server.get_my_top_tracks(time_range="bad") == "Error: Invalid time_range"


class TestGetMyTopArtistsTool:
    def test_returns_json(self, mock_client):
        mock_client.get_my_top_artists.return_value = [ARTIST]
        result = server.get_my_top_artists()
        parsed = json.loads(result)
        assert parsed[0]["name"] == "Queen"

    def test_passes_args(self, mock_client):
        mock_client.get_my_top_artists.return_value = []
        server.get_my_top_artists(time_range="long_term", limit=10)
        mock_client.get_my_top_artists.assert_called_once_with("long_term", 10)

    def test_error_handling(self, mock_client):
        mock_client.get_my_top_artists.side_effect = SpotifyError("Auth error")
        assert server.get_my_top_artists() == "Error: Auth error"


# -- Playback --


class TestPlayTrackTool:
    def test_success_message(self, mock_client):
        result = server.play_track("spotify:track:4u7EnebtmKWzUH433cf5Qv")
        assert result == "Playback started."
        mock_client.play_track.assert_called_once_with(
            "spotify:track:4u7EnebtmKWzUH433cf5Qv"
        )

    def test_error_handling(self, mock_client):
        mock_client.play_track.side_effect = SpotifyError("No active device")
        assert server.play_track("id") == "Error: No active device"


class TestPausePlaybackTool:
    def test_success_message(self, mock_client):
        result = server.pause_playback()
        assert result == "Playback paused."
        mock_client.pause_playback.assert_called_once()

    def test_error_handling(self, mock_client):
        mock_client.pause_playback.side_effect = SpotifyError("No active device")
        assert server.pause_playback() == "Error: No active device"


class TestAddToQueueTool:
    def test_success_message(self, mock_client):
        result = server.add_to_queue("4u7EnebtmKWzUH433cf5Qv")
        assert result == "Track added to queue."
        mock_client.add_to_queue.assert_called_once_with("4u7EnebtmKWzUH433cf5Qv")

    def test_error_handling(self, mock_client):
        mock_client.add_to_queue.side_effect = SpotifyError("Not found")
        assert server.add_to_queue("bad") == "Error: Not found"


class TestGetNowPlayingTool:
    def test_returns_json(self, mock_client):
        mock_client.get_now_playing.return_value = NOW_PLAYING
        result = server.get_now_playing()
        parsed = json.loads(result)
        assert parsed["track"] == "Bohemian Rhapsody"
        assert parsed["is_playing"] is True

    def test_nothing_playing(self, mock_client):
        mock_client.get_now_playing.return_value = None
        assert server.get_now_playing() == "Nothing is currently playing."

    def test_error_handling(self, mock_client):
        mock_client.get_now_playing.side_effect = SpotifyError("API error")
        assert server.get_now_playing() == "Error: API error"


# -- Diagnostics --


class TestGetServerVersionTool:
    def test_returns_installed_version(self):
        assert server.get_server_version() == version("mcp-spotify")
