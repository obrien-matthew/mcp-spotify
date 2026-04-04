"""Tests for LLM-friendly response formatters."""

from spotify_mcp.formatting import (
    format_album,
    format_album_list,
    format_artist,
    format_artist_list,
    format_now_playing,
    format_playlist,
    format_track,
    format_track_list,
)

# -- Fixtures (minimal Spotify API response shapes) --

TRACK = {
    "name": "Bohemian Rhapsody",
    "id": "4u7EnebtmKWzUH433cf5Qv",
    "uri": "spotify:track:4u7EnebtmKWzUH433cf5Qv",
    "artists": [{"name": "Queen"}],
    "duration_ms": 354947,
    "album": {"name": "A Night at the Opera"},
}

ARTIST = {
    "name": "Queen",
    "id": "1dfeR4HaWDbWqFHLkxsg1d",
    "uri": "spotify:artist:1dfeR4HaWDbWqFHLkxsg1d",
    "genres": ["classic rock", "glam rock", "rock"],
}

ALBUM = {
    "name": "A Night at the Opera",
    "id": "1GbtB4zTqAsyfZEsm1RZfx",
    "uri": "spotify:album:1GbtB4zTqAsyfZEsm1RZfx",
    "artists": [{"name": "Queen"}],
    "release_date": "1975-11-21",
    "total_tracks": 12,
}

PLAYLIST = {
    "name": "Classic Rock",
    "id": "37i9dQZF1DXcBWIGoYBM5M",
    "uri": "spotify:playlist:37i9dQZF1DXcBWIGoYBM5M",
    "owner": {"display_name": "Spotify"},
    "tracks": {"total": 80},
    "public": True,
    "description": "The biggest classic rock hits.",
}

PLAYBACK = {
    "item": TRACK,
    "device": {"name": "MacBook Pro"},
    "progress_ms": 120000,
    "is_playing": True,
}


class TestFormatTrack:
    def test_basic_fields(self):
        result = format_track(TRACK)
        assert result["name"] == "Bohemian Rhapsody"
        assert result["id"] == "4u7EnebtmKWzUH433cf5Qv"
        assert result["uri"] == "spotify:track:4u7EnebtmKWzUH433cf5Qv"
        assert result["artists"] == "Queen"
        assert result["duration_ms"] == 354947

    def test_excludes_album_by_default(self):
        result = format_track(TRACK)
        assert "album" not in result

    def test_includes_album_when_requested(self):
        result = format_track(TRACK, include_album=True)
        assert result["album"] == "A Night at the Opera"

    def test_multiple_artists(self):
        track = {**TRACK, "artists": [{"name": "Queen"}, {"name": "David Bowie"}]}
        result = format_track(track)
        assert result["artists"] == "Queen, David Bowie"

    def test_missing_album(self):
        track = {k: v for k, v in TRACK.items() if k != "album"}
        result = format_track(track, include_album=True)
        assert "album" not in result


class TestFormatTrackList:
    def test_formats_multiple(self):
        result = format_track_list([TRACK, TRACK])
        assert len(result) == 2

    def test_filters_none(self):
        result = format_track_list([TRACK, None, {}, TRACK])  # type: ignore[list-item]
        assert len(result) == 2

    def test_empty(self):
        assert format_track_list([]) == []


class TestFormatArtist:
    def test_basic_fields(self):
        result = format_artist(ARTIST)
        assert result["name"] == "Queen"
        assert result["id"] == "1dfeR4HaWDbWqFHLkxsg1d"
        assert result["genres"] == ["classic rock", "glam rock", "rock"]

    def test_missing_genres(self):
        artist = {k: v for k, v in ARTIST.items() if k != "genres"}
        result = format_artist(artist)
        assert result["genres"] == []


class TestFormatArtistList:
    def test_filters_none(self):
        result = format_artist_list([ARTIST, None, ARTIST])  # type: ignore[list-item]
        assert len(result) == 2


class TestFormatAlbum:
    def test_basic_fields(self):
        result = format_album(ALBUM)
        assert result["name"] == "A Night at the Opera"
        assert result["id"] == "1GbtB4zTqAsyfZEsm1RZfx"
        assert result["artists"] == "Queen"
        assert result["release_date"] == "1975-11-21"
        assert result["total_tracks"] == 12

    def test_multiple_artists(self):
        album = {**ALBUM, "artists": [{"name": "Queen"}, {"name": "David Bowie"}]}
        result = format_album(album)
        assert result["artists"] == "Queen, David Bowie"


class TestFormatAlbumList:
    def test_filters_none(self):
        result = format_album_list([ALBUM, None, ALBUM])  # type: ignore[list-item]
        assert len(result) == 2


class TestFormatPlaylist:
    def test_basic_fields(self):
        result = format_playlist(PLAYLIST)
        assert result["name"] == "Classic Rock"
        assert result["owner"] == "Spotify"
        assert result["total_tracks"] == 80
        assert result["public"] is True
        assert result["description"] == "The biggest classic rock hits."

    def test_tracks_total_from_items_key(self):
        playlist = {**PLAYLIST, "items": {"total": 42}}
        del playlist["tracks"]
        result = format_playlist(playlist)
        assert result["total_tracks"] == 42

    def test_no_total(self):
        playlist = {k: v for k, v in PLAYLIST.items() if k != "tracks"}
        result = format_playlist(playlist)
        assert result["total_tracks"] == 0

    def test_no_description(self):
        playlist = {k: v for k, v in PLAYLIST.items() if k != "description"}
        result = format_playlist(playlist)
        assert "description" not in result

    def test_missing_owner(self):
        playlist = {k: v for k, v in PLAYLIST.items() if k != "owner"}
        result = format_playlist(playlist)
        assert result["owner"] == "unknown"


class TestFormatNowPlaying:
    def test_basic_fields(self):
        result = format_now_playing(PLAYBACK)
        assert result["track"] == "Bohemian Rhapsody"
        assert result["artists"] == "Queen"
        assert result["album"] == "A Night at the Opera"
        assert result["progress_ms"] == 120000
        assert result["duration_ms"] == 354947
        assert result["is_playing"] is True
        assert result["device"] == "MacBook Pro"

    def test_empty_playback(self):
        result = format_now_playing({})
        assert result["track"] is None
        assert result["is_playing"] is False
        assert result["device"] is None
