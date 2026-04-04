"""Tests for SpotifyClient with mocked spotipy backend."""

from unittest.mock import MagicMock, patch

import pytest
from spotipy.exceptions import SpotifyException

from spotify_mcp.client import SpotifyClient, SpotifyError

# -- Fixtures --

TRACK_DATA = {
    "name": "Bohemian Rhapsody",
    "id": "4u7EnebtmKWzUH433cf5Qv",
    "uri": "spotify:track:4u7EnebtmKWzUH433cf5Qv",
    "artists": [{"name": "Queen"}],
    "duration_ms": 354947,
    "album": {"name": "A Night at the Opera"},
}

ARTIST_DATA = {
    "name": "Queen",
    "id": "1dfeR4HaWDbWqFHLkxsg1d",
    "uri": "spotify:artist:1dfeR4HaWDbWqFHLkxsg1d",
    "genres": ["classic rock", "rock"],
}

ALBUM_DATA = {
    "name": "A Night at the Opera",
    "id": "1GbtB4zTqAsyfZEsm1RZfx",
    "uri": "spotify:album:1GbtB4zTqAsyfZEsm1RZfx",
    "artists": [{"name": "Queen"}],
    "release_date": "1975-11-21",
    "total_tracks": 12,
}

PLAYLIST_DATA = {
    "name": "My Playlist",
    "id": "37i9dQZF1DXcBWIGoYBM5M",
    "uri": "spotify:playlist:37i9dQZF1DXcBWIGoYBM5M",
    "owner": {"display_name": "testuser"},
    "tracks": {"total": 5},
    "public": True,
}


@pytest.fixture
def client():
    """Create a SpotifyClient with a mocked spotipy instance."""
    with patch("spotify_mcp.client.get_spotify_client") as mock_get:
        mock_sp = MagicMock()
        mock_get.return_value = mock_sp
        c = SpotifyClient()
        yield c, mock_sp


# -- Discovery --


class TestSearchTracks:
    def test_returns_formatted_tracks(self, client):
        c, mock_sp = client
        mock_sp.search.return_value = {"tracks": {"items": [TRACK_DATA]}}
        result = c.search_tracks("bohemian rhapsody")
        assert len(result) == 1
        assert result[0]["name"] == "Bohemian Rhapsody"
        mock_sp.search.assert_called_once_with(
            q="bohemian rhapsody", type="track", limit=20
        )

    def test_clamps_limit(self, client):
        c, mock_sp = client
        mock_sp.search.return_value = {"tracks": {"items": []}}
        c.search_tracks("test", limit=200)
        mock_sp.search.assert_called_once_with(q="test", type="track", limit=50)

    def test_returns_empty_on_none(self, client):
        c, mock_sp = client
        mock_sp.search.return_value = None
        assert c.search_tracks("nothing") == []

    def test_raises_on_api_error(self, client):
        c, mock_sp = client
        mock_sp.search.side_effect = SpotifyException(429, "", msg="rate limited")
        with pytest.raises(SpotifyError, match="Rate limited"):
            c.search_tracks("test")


class TestSearchArtists:
    def test_returns_formatted_artists(self, client):
        c, mock_sp = client
        mock_sp.search.return_value = {"artists": {"items": [ARTIST_DATA]}}
        result = c.search_artists("queen")
        assert len(result) == 1
        assert result[0]["name"] == "Queen"
        assert result[0]["genres"] == ["classic rock", "rock"]

    def test_returns_empty_on_none(self, client):
        c, mock_sp = client
        mock_sp.search.return_value = None
        assert c.search_artists("nothing") == []


class TestSearchAlbums:
    def test_returns_formatted_albums(self, client):
        c, mock_sp = client
        mock_sp.search.return_value = {"albums": {"items": [ALBUM_DATA]}}
        result = c.search_albums("a night at the opera")
        assert len(result) == 1
        assert result[0]["name"] == "A Night at the Opera"
        assert result[0]["release_date"] == "1975-11-21"

    def test_returns_empty_on_none(self, client):
        c, mock_sp = client
        mock_sp.search.return_value = None
        assert c.search_albums("nothing") == []


class TestGetAlbumTracks:
    def test_returns_tracks_and_total(self, client):
        c, mock_sp = client
        mock_sp.album_tracks.return_value = {"items": [TRACK_DATA], "total": 12}
        result = c.get_album_tracks("1GbtB4zTqAsyfZEsm1RZfx")
        assert result["total"] == 12
        assert len(result["tracks"]) == 1

    def test_extracts_id_from_uri(self, client):
        c, mock_sp = client
        mock_sp.album_tracks.return_value = {"items": [], "total": 0}
        c.get_album_tracks("spotify:album:1GbtB4zTqAsyfZEsm1RZfx")
        mock_sp.album_tracks.assert_called_once_with("1GbtB4zTqAsyfZEsm1RZfx", limit=50)

    def test_returns_empty_on_none(self, client):
        c, mock_sp = client
        mock_sp.album_tracks.return_value = None
        result = c.get_album_tracks("1GbtB4zTqAsyfZEsm1RZfx")
        assert result == {"tracks": [], "total": 0}


# -- Library --


class TestGetSavedTracks:
    def test_returns_tracks_with_pagination(self, client):
        c, mock_sp = client
        mock_sp.current_user_saved_tracks.return_value = {
            "items": [{"track": TRACK_DATA}],
            "total": 100,
        }
        result = c.get_saved_tracks(limit=20, offset=0)
        assert result["total"] == 100
        assert len(result["tracks"]) == 1
        assert result["offset"] == 0
        assert result["limit"] == 20

    def test_filters_none_tracks(self, client):
        c, mock_sp = client
        mock_sp.current_user_saved_tracks.return_value = {
            "items": [{"track": TRACK_DATA}, {"track": None}, {}],
            "total": 3,
        }
        result = c.get_saved_tracks()
        assert len(result["tracks"]) == 1

    def test_returns_empty_on_none(self, client):
        c, mock_sp = client
        mock_sp.current_user_saved_tracks.return_value = None
        result = c.get_saved_tracks()
        assert result == {"tracks": [], "total": 0, "offset": 0, "limit": 20}


# -- Playlists --


class TestCreatePlaylist:
    def test_creates_via_me_endpoint(self, client):
        c, mock_sp = client
        mock_sp.auth_manager = MagicMock()
        mock_sp.auth_manager.get_access_token.return_value = "fake-token"
        with patch("requests.post") as mock_post:
            mock_resp = MagicMock()
            mock_resp.status_code = 201
            mock_resp.json.return_value = PLAYLIST_DATA
            mock_post.return_value = mock_resp
            result = c.create_playlist("My Playlist")
            assert result["name"] == "My Playlist"
            mock_post.assert_called_once()
            call_url = mock_post.call_args[0][0]
            assert call_url == "https://api.spotify.com/v1/me/playlists"

    def test_raises_on_failure(self, client):
        c, mock_sp = client
        mock_sp.auth_manager = MagicMock()
        mock_sp.auth_manager.get_access_token.return_value = "fake-token"
        with patch("requests.post") as mock_post:
            mock_resp = MagicMock()
            mock_resp.status_code = 403
            mock_post.return_value = mock_resp
            with pytest.raises(SpotifyError, match="403"):
                c.create_playlist("Blocked Playlist")

    def test_raises_without_auth_manager(self, client):
        c, mock_sp = client
        mock_sp.auth_manager = None
        with pytest.raises(SpotifyError, match="No auth manager"):
            c.create_playlist("Test")


class TestAddTracksToPlaylist:
    def test_converts_ids_to_uris(self, client):
        c, mock_sp = client
        c.add_tracks_to_playlist(
            "37i9dQZF1DXcBWIGoYBM5M",
            ["4u7EnebtmKWzUH433cf5Qv"],
        )
        mock_sp.playlist_add_items.assert_called_once_with(
            "37i9dQZF1DXcBWIGoYBM5M",
            ["spotify:track:4u7EnebtmKWzUH433cf5Qv"],
        )

    def test_raises_on_api_error(self, client):
        c, mock_sp = client
        mock_sp.playlist_add_items.side_effect = SpotifyException(
            404, "", msg="not found"
        )
        with pytest.raises(SpotifyError, match="Not found"):
            c.add_tracks_to_playlist(
                "37i9dQZF1DXcBWIGoYBM5M", ["4u7EnebtmKWzUH433cf5Qv"]
            )


class TestRemoveTracksFromPlaylist:
    def test_converts_ids_to_uris(self, client):
        c, mock_sp = client
        c.remove_tracks_from_playlist(
            "37i9dQZF1DXcBWIGoYBM5M",
            ["4u7EnebtmKWzUH433cf5Qv"],
        )
        mock_sp.playlist_remove_all_occurrences_of_items.assert_called_once_with(
            "37i9dQZF1DXcBWIGoYBM5M",
            ["spotify:track:4u7EnebtmKWzUH433cf5Qv"],
        )


class TestReplacePlaylistTracks:
    def test_single_batch(self, client):
        c, mock_sp = client
        ids = ["4u7EnebtmKWzUH433cf5Qv"] * 50
        c.replace_playlist_tracks("37i9dQZF1DXcBWIGoYBM5M", ids)
        mock_sp.playlist_replace_items.assert_called_once()
        mock_sp.playlist_add_items.assert_not_called()

    def test_multi_batch(self, client):
        c, mock_sp = client
        ids = ["4u7EnebtmKWzUH433cf5Qv"] * 150
        c.replace_playlist_tracks("37i9dQZF1DXcBWIGoYBM5M", ids)
        mock_sp.playlist_replace_items.assert_called_once()
        mock_sp.playlist_add_items.assert_called_once()


class TestGetPlaylistTracks:
    def test_returns_tracks_with_pagination(self, client):
        c, mock_sp = client
        mock_sp.playlist_items.return_value = {
            "items": [{"track": TRACK_DATA}],
            "total": 80,
        }
        result = c.get_playlist_tracks("37i9dQZF1DXcBWIGoYBM5M")
        assert result["total"] == 80
        assert len(result["tracks"]) == 1
        assert result["offset"] == 0

    def test_handles_item_key(self, client):
        c, mock_sp = client
        mock_sp.playlist_items.return_value = {
            "items": [{"item": TRACK_DATA}],
            "total": 1,
        }
        result = c.get_playlist_tracks("37i9dQZF1DXcBWIGoYBM5M")
        assert len(result["tracks"]) == 1

    def test_returns_empty_on_none(self, client):
        c, mock_sp = client
        mock_sp.playlist_items.return_value = None
        result = c.get_playlist_tracks("37i9dQZF1DXcBWIGoYBM5M")
        assert result["tracks"] == []


class TestGetMyPlaylists:
    def test_returns_formatted_playlists(self, client):
        c, mock_sp = client
        mock_sp.current_user_playlists.return_value = {"items": [PLAYLIST_DATA]}
        result = c.get_my_playlists()
        assert len(result) == 1
        assert result[0]["name"] == "My Playlist"

    def test_returns_empty_on_none(self, client):
        c, mock_sp = client
        mock_sp.current_user_playlists.return_value = None
        assert c.get_my_playlists() == []


# -- Personalization --


class TestGetMyTopTracks:
    def test_returns_formatted_tracks(self, client):
        c, mock_sp = client
        mock_sp.current_user_top_tracks.return_value = {"items": [TRACK_DATA]}
        result = c.get_my_top_tracks()
        assert len(result) == 1
        assert result[0]["name"] == "Bohemian Rhapsody"

    def test_invalid_time_range(self, client):
        c, _ = client
        with pytest.raises(ValueError, match="Invalid time_range"):
            c.get_my_top_tracks(time_range="invalid")

    def test_returns_empty_on_none(self, client):
        c, mock_sp = client
        mock_sp.current_user_top_tracks.return_value = None
        assert c.get_my_top_tracks() == []


class TestGetMyTopArtists:
    def test_returns_formatted_artists(self, client):
        c, mock_sp = client
        mock_sp.current_user_top_artists.return_value = {"items": [ARTIST_DATA]}
        result = c.get_my_top_artists()
        assert len(result) == 1
        assert result[0]["name"] == "Queen"

    def test_invalid_time_range(self, client):
        c, _ = client
        with pytest.raises(ValueError, match="Invalid time_range"):
            c.get_my_top_artists(time_range="invalid")


# -- Playback --


class TestPlayTrack:
    def test_converts_id_to_uri(self, client):
        c, mock_sp = client
        c.play_track("4u7EnebtmKWzUH433cf5Qv")
        mock_sp.start_playback.assert_called_once_with(
            uris=["spotify:track:4u7EnebtmKWzUH433cf5Qv"]
        )

    def test_accepts_uri(self, client):
        c, mock_sp = client
        c.play_track("spotify:track:4u7EnebtmKWzUH433cf5Qv")
        mock_sp.start_playback.assert_called_once_with(
            uris=["spotify:track:4u7EnebtmKWzUH433cf5Qv"]
        )

    def test_raises_on_api_error(self, client):
        c, mock_sp = client
        mock_sp.start_playback.side_effect = SpotifyException(403, "", msg="forbidden")
        with pytest.raises(SpotifyError, match="Permission denied"):
            c.play_track("4u7EnebtmKWzUH433cf5Qv")


class TestAddToQueue:
    def test_converts_id_to_uri(self, client):
        c, mock_sp = client
        c.add_to_queue("4u7EnebtmKWzUH433cf5Qv")
        mock_sp.add_to_queue.assert_called_once_with(
            "spotify:track:4u7EnebtmKWzUH433cf5Qv"
        )

    def test_raises_on_api_error(self, client):
        c, mock_sp = client
        mock_sp.add_to_queue.side_effect = SpotifyException(404, "", msg="no device")
        with pytest.raises(SpotifyError, match="Not found"):
            c.add_to_queue("4u7EnebtmKWzUH433cf5Qv")


class TestPausePlayback:
    def test_calls_pause(self, client):
        c, mock_sp = client
        c.pause_playback()
        mock_sp.pause_playback.assert_called_once()


class TestGetNowPlaying:
    def test_returns_formatted_playback(self, client):
        c, mock_sp = client
        mock_sp.current_playback.return_value = {
            "item": TRACK_DATA,
            "device": {"name": "MacBook"},
            "progress_ms": 60000,
            "is_playing": True,
        }
        result = c.get_now_playing()
        assert result is not None
        assert result["track"] == "Bohemian Rhapsody"
        assert result["is_playing"] is True

    def test_returns_none_when_nothing_playing(self, client):
        c, mock_sp = client
        mock_sp.current_playback.return_value = None
        assert c.get_now_playing() is None

    def test_returns_none_when_no_item(self, client):
        c, mock_sp = client
        mock_sp.current_playback.return_value = {"item": None}
        assert c.get_now_playing() is None


# -- Error handling --


class TestHandleError:
    def test_404_message(self, client):
        c, mock_sp = client
        mock_sp.search.side_effect = SpotifyException(404, "", msg="not found")
        with pytest.raises(SpotifyError, match="Not found"):
            c.search_tracks("test")

    def test_403_message(self, client):
        c, mock_sp = client
        mock_sp.search.side_effect = SpotifyException(403, "", msg="forbidden")
        with pytest.raises(SpotifyError, match="Permission denied"):
            c.search_tracks("test")

    def test_429_message(self, client):
        c, mock_sp = client
        mock_sp.search.side_effect = SpotifyException(429, "", msg="rate limited")
        with pytest.raises(SpotifyError, match="Rate limited"):
            c.search_tracks("test")

    def test_generic_error(self, client):
        c, mock_sp = client
        mock_sp.search.side_effect = SpotifyException(500, "", msg="server error")
        with pytest.raises(SpotifyError, match="Spotify API error"):
            c.search_tracks("test")

    def test_preserves_status_code(self, client):
        c, mock_sp = client
        mock_sp.search.side_effect = SpotifyException(429, "", msg="rate limited")
        with pytest.raises(SpotifyError) as exc_info:
            c.search_tracks("test")
        assert exc_info.value.status_code == 429
