# Extended Quota Access (Spotify Web API)

## Status: Effectively Inaccessible for Personal Projects

As of May 2025, Spotify's Extended Quota Mode requires:

- A **legally registered business entity** (not individuals)
- **250,000+ monthly active users**
- An active, launched service in key Spotify markets
- Review process takes up to 6 weeks

This makes Extended Quota inaccessible for personal projects, hobby apps, and small tools.

## What's Gated

These tools in this MCP server require Extended Quota and return **403 Forbidden** in Development Mode:

- `get_artist_top_tracks` -- `GET /artists/{id}/top-tracks`
- `get_related_artists` -- `GET /artists/{id}/related-artists`

The tools remain in the codebase in case Spotify loosens restrictions, but they are non-functional for Development Mode apps.

## Workarounds

Without these endpoints, playlist building relies on:

- `search_tracks` with Spotify's query syntax (`genre:rock`, `year:2020-2024`, `artist:radiohead`)
- `get_my_top_tracks` and `get_my_top_artists` as starting points
- The LLM's own music knowledge to suggest artists and tracks by name

## Timeline

- **November 2024**: Spotify restricted many endpoints to Extended Quota only
- **May 2025**: Extended Quota criteria raised to 250k MAU + registered business
- **February 2026**: Further Development Mode restrictions (Premium required, search cap reduced)

See the [Spotify Web API Restrictions](../../README.md#spotify-web-api-restrictions) section in the README for full details.
