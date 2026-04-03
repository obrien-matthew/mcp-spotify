# Apply for Spotify Extended Quota Access

Development Mode apps are restricted from several API endpoints that this MCP server uses for music discovery. Without extended quota, the following tools return 403 Forbidden:

- `get_artist_top_tracks`
- `get_related_artists`

These are the primary discovery tools for building playlists (finding new music based on artists you like). Without them, playlist building is limited to `search_tracks` and your personal top tracks/artists.

## Steps

1. **Go to the Spotify Developer Dashboard**
   - Visit https://developer.spotify.com/dashboard
   - Select your app

2. **Request Extended Quota**
   - Look for a **Request Extension** or **Extended Quota Mode** option in your app settings
   - Spotify's process has changed over time -- if you don't see it directly, check under **Settings** or **App Status**

3. **Fill Out the Application**
   - **App description**: Describe the MCP server -- e.g., "A Model Context Protocol server that enables AI assistants to build and manage Spotify playlists through natural language conversation."
   - **Which endpoints do you need?**: At minimum:
     - `Get Artist's Top Tracks` (`/v1/artists/{id}/top-tracks`)
     - `Get Artist's Related Artists` (`/v1/artists/{id}/related-artists`)
   - **Use case**: Personal tool for AI-assisted playlist curation
   - **Expected user count**: 1 (personal use)

4. **Wait for Approval**
   - Spotify reviews applications manually
   - Approval can take days to weeks depending on the queue
   - You'll get an email when approved

5. **After Approval**
   - Delete the cached token: `rm ~/.spotify_mcp_cache`
   - Reconnect the MCP server -- the new token will have access to the extended endpoints

## Workaround While Waiting

Without these endpoints, you can still build playlists using:
- `search_tracks` with Spotify's query syntax (`genre:rock`, `year:2020-2024`, `artist:radiohead`)
- `get_my_top_tracks` and `get_my_top_artists` as starting points
- Iterative search -- ask Claude to search for tracks by artists similar to ones you like

## Notes

- As of late 2024, Spotify tightened API access significantly. Extended quota is now required for many endpoints that were previously open.
- The deprecated `recommendations` endpoint is not available even with extended quota (unless your app had access before November 2024).
