"""Tests for Spotify ID/URI validation and pagination helpers."""

import pytest

from spotify_mcp.validation import (
    extract_id,
    validate_limit,
    validate_offset,
    validate_spotify_id,
)


class TestValidateSpotifyId:
    def test_valid_id(self):
        assert validate_spotify_id("6rqhFgbbKwnb9MLmUQDhG6") == "6rqhFgbbKwnb9MLmUQDhG6"

    def test_strips_whitespace(self):
        assert (
            validate_spotify_id("  6rqhFgbbKwnb9MLmUQDhG6  ")
            == "6rqhFgbbKwnb9MLmUQDhG6"
        )

    def test_too_short(self):
        with pytest.raises(ValueError, match="Invalid Spotify"):
            validate_spotify_id("abc123")

    def test_too_long(self):
        with pytest.raises(ValueError, match="Invalid Spotify"):
            validate_spotify_id("6rqhFgbbKwnb9MLmUQDhG6X")

    def test_invalid_characters(self):
        with pytest.raises(ValueError, match="Invalid Spotify"):
            validate_spotify_id("6rqhFgbbKwnb9MLmUQDh!!")

    def test_empty_string(self):
        with pytest.raises(ValueError, match="Invalid Spotify"):
            validate_spotify_id("")

    def test_custom_label(self):
        with pytest.raises(ValueError, match="Invalid Spotify artist"):
            validate_spotify_id("bad", label="artist")


class TestExtractId:
    def test_bare_id(self):
        assert extract_id("6rqhFgbbKwnb9MLmUQDhG6") == "6rqhFgbbKwnb9MLmUQDhG6"

    def test_track_uri(self):
        assert (
            extract_id("spotify:track:6rqhFgbbKwnb9MLmUQDhG6")
            == "6rqhFgbbKwnb9MLmUQDhG6"
        )

    def test_artist_uri(self):
        assert (
            extract_id("spotify:artist:0TnOYISbd1XYRBk9myaseg")
            == "0TnOYISbd1XYRBk9myaseg"
        )

    def test_album_uri(self):
        assert (
            extract_id("spotify:album:0TnOYISbd1XYRBk9myaseg")
            == "0TnOYISbd1XYRBk9myaseg"
        )

    def test_playlist_uri(self):
        assert (
            extract_id("spotify:playlist:37i9dQZF1DXcBWIGoYBM5M")
            == "37i9dQZF1DXcBWIGoYBM5M"
        )

    def test_strips_whitespace_from_uri(self):
        assert (
            extract_id("  spotify:track:6rqhFgbbKwnb9MLmUQDhG6  ")
            == "6rqhFgbbKwnb9MLmUQDhG6"
        )

    def test_invalid_uri_type(self):
        with pytest.raises(ValueError, match="Invalid Spotify"):
            extract_id("spotify:show:6rqhFgbbKwnb9MLmUQDhG6")

    def test_invalid_value(self):
        with pytest.raises(ValueError, match="Invalid Spotify"):
            extract_id("not-a-valid-id")


class TestValidateLimit:
    def test_normal_value(self):
        assert validate_limit(20) == 20

    def test_clamps_to_max(self):
        assert validate_limit(100) == 50

    def test_clamps_to_max_custom(self):
        assert validate_limit(200, max_val=100) == 100

    def test_clamps_to_min(self):
        assert validate_limit(0) == 1

    def test_negative(self):
        assert validate_limit(-5) == 1

    def test_exact_max(self):
        assert validate_limit(50) == 50

    def test_exact_min(self):
        assert validate_limit(1) == 1


class TestValidateOffset:
    def test_zero(self):
        assert validate_offset(0) == 0

    def test_positive(self):
        assert validate_offset(50) == 50

    def test_negative(self):
        with pytest.raises(ValueError, match="non-negative"):
            validate_offset(-1)
