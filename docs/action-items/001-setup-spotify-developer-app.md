# Set Up Spotify Developer App

Before using this MCP server, you need to register a Spotify Developer application to get API credentials.

## Steps

1. **Go to the Spotify Developer Dashboard**
   - Visit https://developer.spotify.com/dashboard
   - Log in with your Spotify account (create one first if needed)

2. **Create an App**
   - Click **Create App**
   - Fill in:
     - **App name**: anything (e.g., "Spotify MCP")
     - **App description**: anything
     - **Redirect URI**: `http://127.0.0.1:8888/callback` (this must match exactly)
   - Check the Terms of Service box
   - Click **Save**

3. **Get Your Credentials**
   - On the app's dashboard page, you'll see the **Client ID** displayed
   - Click **Show Client Secret** to reveal the secret
   - Save both values -- you'll need them as environment variables

4. **Configure the MCP Server**
   - Set the environment variables in your shell or Claude Desktop config:
     ```bash
     export SPOTIFY_CLIENT_ID="your_client_id_here"
     export SPOTIFY_CLIENT_SECRET="your_client_secret_here"
     export SPOTIFY_REDIRECT_URI="http://127.0.0.1:8888/callback"
     ```

5. **First-Time Authorization**
   - Run `uv run spotify-mcp` from the project directory
   - A browser window will open asking you to authorize the app
   - Click **Agree** to grant the requested permissions
   - The token is cached at `~/.spotify_mcp_cache` -- you won't need to do this again unless the token expires and can't be refreshed

## Notes

- The redirect URI **must** use `127.0.0.1`, not `localhost` -- Spotify requires this
- Free Spotify accounts work, but playback control tools (`play_track`, `pause_playback`) require Spotify Premium
- The app starts in "Development Mode" which allows up to 25 users -- this is fine for personal use
