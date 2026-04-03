"""Response formatters that produce clean, LLM-friendly dicts.

Only includes fields useful for an LLM -- no images, external URLs, or hrefs.
"""


def format_track(track: dict, include_album: bool = False) -> dict:
    artists = ", ".join(a["name"] for a in track.get("artists", []))
    result: dict = {
        "name": track["name"],
        "id": track["id"],
        "uri": track["uri"],
        "artists": artists,
        "duration_ms": track.get("duration_ms"),
    }
    if include_album and track.get("album"):
        result["album"] = track["album"]["name"]
    return result


def format_track_list(tracks: list[dict], include_album: bool = False) -> list[dict]:
    return [format_track(t, include_album) for t in tracks if t]


def format_artist(artist: dict) -> dict:
    return {
        "name": artist["name"],
        "id": artist["id"],
        "uri": artist["uri"],
        "genres": artist.get("genres", []),
    }


def format_artist_list(artists: list[dict]) -> list[dict]:
    return [format_artist(a) for a in artists if a]


def _get_playlist_total(playlist: dict) -> int:
    """Extract track count from either 'tracks' or 'items' key."""
    for key in ("tracks", "items"):
        val = playlist.get(key)
        if isinstance(val, dict) and "total" in val:
            return val["total"]
    return 0


def format_playlist(playlist: dict) -> dict:
    result: dict = {
        "name": playlist["name"],
        "id": playlist["id"],
        "uri": playlist["uri"],
        "owner": playlist.get("owner", {}).get("display_name", "unknown"),
        "total_tracks": _get_playlist_total(playlist),
        "public": playlist.get("public"),
    }
    if playlist.get("description"):
        result["description"] = playlist["description"]
    return result


def format_playlist_list(playlists: list[dict]) -> list[dict]:
    return [format_playlist(p) for p in playlists if p]


def format_now_playing(playback: dict) -> dict:
    track = playback.get("item", {})
    device = playback.get("device", {})
    return {
        "track": track.get("name"),
        "artists": ", ".join(a["name"] for a in track.get("artists", [])),
        "album": track.get("album", {}).get("name"),
        "progress_ms": playback.get("progress_ms"),
        "duration_ms": track.get("duration_ms"),
        "is_playing": playback.get("is_playing", False),
        "device": device.get("name"),
    }
