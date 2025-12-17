"""
Spotify client for detecting currently playing track.
"""
import os
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv

load_dotenv()

class SpotifyClient:
    def __init__(self):
        self.client_id = os.getenv('SPOTIFY_CLIENT_ID')
        self.client_secret = os.getenv('SPOTIFY_CLIENT_SECRET')
        
        if not self.client_id or not self.client_secret:
            raise ValueError("Spotify credentials not found in .env file")
        
        scope = "user-read-currently-playing user-read-playback-state"
        cache_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.spotify_cache')
        self.sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
            client_id=self.client_id,
            client_secret=self.client_secret,
            redirect_uri="http://127.0.0.1:8888/callback",
            scope=scope,
            cache_path=cache_path
        ))
    
    def get_current_track(self):
        """Get currently playing track information."""
        try:
            current = self.sp.current_user_playing_track()
            if current and current['is_playing']:
                track = current['item']
                if track:
                    return {
                        'name': track['name'],
                        'artist': ', '.join([artist['name'] for artist in track['artists']]),
                        'album': track['album']['name'],
                        'duration_ms': track['duration_ms'],
                        'progress_ms': current['progress_ms'],
                        'is_playing': current['is_playing']
                    }
            return None
        except Exception as e:
            print(f"Error getting current track: {e}")
            return None
    
    def get_track_lyrics_from_spotify(self, track_id):
        """Get synced lyrics from Spotify (if available)."""
        try:
            # Note: Spotify's lyrics API is not publicly available yet
            # This is a placeholder for when it becomes available
            # For now, we'll use Musixmatch
            return None
        except Exception as e:
            print(f"Error getting Spotify lyrics: {e}")
            return None

