# Lyrics Overlay

A desktop application that overlays synced or unsynced lyrics on your screen based on the song you're currently listening to on Spotify.

## Features

- 🎵 Automatically detects currently playing track on Spotify
- 🎤 Displays synced lyrics from Musixmatch or Spotify
- 📝 Falls back to Genius for unsynced lyrics if synced lyrics aren't available
- 🧪 Testing mode with manual lyrics and sync times
- 🎨 Customizable overlay position and styling

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up Spotify API credentials:
   - Go to https://developer.spotify.com/dashboard
   - Create a new app
   - Copy your Client ID and Client Secret
   - Add redirect URI: `http://127.0.0.1:8888/callback` (Note: Use `127.0.0.1` instead of `localhost` for security compliance)

3. Set up Genius API (optional, for fallback lyrics):
   - Go to https://genius.com/api-clients
   - Create an app and get your access token

4. Create a `.env` file in the project root:
```
SPOTIFY_CLIENT_ID=
SPOTIFY_CLIENT_SECRET=
GENIUS_ACCESS_TOKEN=
```

**Note**: Musixmatch synced lyrics are fetched via web scraping, so no API key is needed!

## Usage

Run the application:
```bash
python main.py
```

The overlay will automatically detect your currently playing Spotify track and display lyrics.

### Testing Mode

Use the testing mode to test with custom lyrics and sync times without needing Spotify.

## API Keys

- **Spotify**: Required for detecting currently playing track
- **Musixmatch**: No API key needed! Uses web scraping to fetch synced lyrics
- **Genius**: Optional, provides fallback unsynced lyrics

