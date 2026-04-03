"""Input validation helpers for Spotify IDs, URIs, and pagination parameters."""

import re

SPOTIFY_ID_RE = re.compile(r"^[a-zA-Z0-9]{22}$")
SPOTIFY_URI_RE = re.compile(
    r"^spotify:(track|artist|album|playlist):([a-zA-Z0-9]{22})$"
)


def validate_spotify_id(value: str, label: str = "ID") -> str:
    """Validate a 22-character base62 Spotify ID."""
    value = value.strip()
    if not SPOTIFY_ID_RE.match(value):
        raise ValueError(
            f"Invalid Spotify {label}: '{value}'. "
            f"Expected a 22-character alphanumeric string."
        )
    return value


def extract_id(value: str) -> str:
    """Accept either a bare Spotify ID or a full URI (spotify:type:id).

    Returns just the 22-char ID portion.
    """
    value = value.strip()
    match = SPOTIFY_URI_RE.match(value)
    if match:
        return match.group(2)
    return validate_spotify_id(value)


def validate_limit(value: int, max_val: int = 50) -> int:
    """Clamp a limit parameter to the range [1, max_val]."""
    return max(1, min(value, max_val))


def validate_offset(value: int) -> int:
    """Ensure offset is non-negative."""
    if value < 0:
        raise ValueError(f"Offset must be non-negative, got {value}.")
    return value
