"""
Main application entry point for Lyrics Overlay.
"""
import sys
import time
import threading
from spotify_client import SpotifyClient
from lyrics_fetcher import LyricsFetcher
from overlay import LyricsOverlay
import tkinter as tk
from tkinter import ttk, scrolledtext

class LyricsOverlayApp:
    def __init__(self):
        self.spotify_client = None
        self.lyrics_fetcher = LyricsFetcher()
        self.overlay = None
        self.monitoring = False
        self.monitor_thread = None
        self.current_track_id = None
        
        # Initialize Spotify client
        try:
            self.spotify_client = SpotifyClient()
            print("✓ Spotify client initialized")
        except Exception as e:
            print(f"⚠ Warning: Could not initialize Spotify client: {e}")
            print("  You can still use testing mode.")
        
        # Create control window (hidden) to host Tk mainloop
        self.create_control_window()
        self.control_window.withdraw()
    
    def create_control_window(self):
        """Create the control window for settings and testing."""
        self.control_window = tk.Tk()
        self.control_window.title("Lyrics Overlay Control")
        self.control_window.geometry("600x700")
        
        # Title
        title_label = tk.Label(
            self.control_window,
            text="Lyrics Overlay",
            font=('Arial', 20, 'bold')
        )
        title_label.pack(pady=10)
        
        # Status
        self.status_label = tk.Label(
            self.control_window,
            text="Status: Ready",
            font=('Arial', 12)
        )
        self.status_label.pack(pady=5)
        
        # Minimal labels for status (window hidden by default)
        status_frame = ttk.Frame(self.control_window, padding=10)
        status_frame.pack(fill=tk.BOTH, expand=True)

        self.status_label = tk.Label(
            status_frame,
            text="Status: Ready",
            font=('Arial', 12)
        )
        self.status_label.pack(pady=5)

        self.current_track_label = tk.Label(
            status_frame,
            text="No track playing",
            font=('Arial', 10),
            wraplength=550
        )
        self.current_track_label.pack(pady=5)

        # Close handler
        self.control_window.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def start_monitoring(self):
        """Start monitoring Spotify for currently playing track."""
        if not self.spotify_client:
            self.update_status("Error: Spotify client not initialized")
            return
        
        self.monitoring = True
        self.update_status("Monitoring Spotify...")
        
        def monitor():
            while self.monitoring:
                try:
                    track = self.spotify_client.get_current_track()
                    if track:
                        track_id = f"{track['name']} - {track['artist']}"
                        
                        if track_id != self.current_track_id:
                            self.current_track_id = track_id
                            self.update_track_display(track)
                            self.fetch_and_display_lyrics(track)
                        
                        # Update scroll with Spotify's progress
                        if self.overlay and track.get('progress_ms'):
                            self.overlay.update_progress(track['progress_ms'])
                    else:
                        if self.current_track_id:
                            self.current_track_id = None
                            self.update_track_display(None)
                            self.close_overlay()
                    
                    time.sleep(1)  # Check every second for better sync
                except Exception as e:
                    import traceback
                    error_str = traceback.format_exc()
                    print(f"Error in monitoring: {error_str}")
                    if self.overlay:
                        # Use after() to ensure GUI update is thread-safe
                        self.control_window.after(0, self.overlay.display_error, error_str)
                    time.sleep(5)
        
        self.monitor_thread = threading.Thread(target=monitor, daemon=True)
        self.monitor_thread.start()
    
    def stop_monitoring(self):
        """Stop monitoring Spotify."""
        self.monitoring = False
        self.update_status("Monitoring stopped")
    
    def update_status(self, status):
        """Update status label."""
        self.status_label.config(text=f"Status: {status}")
    
    def update_track_display(self, track):
        """Update current track display."""
        if track:
            text = f"Now playing: {track['name']} by {track['artist']}"
        else:
            text = "No track playing"
        self.current_track_label.config(text=text)
    
    def fetch_and_display_lyrics(self, track):
        """Fetch and display lyrics for the current track."""
        self.update_status(f"Fetching lyrics for {track['name']}...")
        
        # Fetch lyrics
        lyrics_data = self.lyrics_fetcher.fetch_lyrics(
            track['name'],
            track['artist'],
            track['album'],
            track['duration_ms'] / 1000
        )
        
        if not lyrics_data:
            self.update_status(f"No lyrics found for {track['name']}")
            return
        
        # Create or update overlay
        if not self.overlay:
            # Create overlay attached to control window (same main thread)
            self.overlay = LyricsOverlay(parent=self.control_window)
        
        # Set lyrics with current progress
        progress_ms = track.get('progress_ms', 0)
        self.overlay.set_lyrics(lyrics_data, track.get('duration_ms', 0), progress_ms)
        
        lyrics_type = "synced" if lyrics_data['type'] == 'synced' else "unsynced"
        self.update_status(f"Displaying {lyrics_type} lyrics")
    
    def test_lyrics(self):
        """Test with custom lyrics."""
        lyrics = self.test_lyrics_text.get(1.0, tk.END).strip()
        sync_times_str = self.sync_times_entry.get().strip()
        
        if not lyrics:
            self.update_status("Please enter lyrics")
            return
        
        sync_times = None
        if sync_times_str:
            try:
                sync_times = [float(t.strip()) for t in sync_times_str.split(',')]
            except ValueError:
                self.update_status("Invalid sync times format")
                return
        
        # Create or update overlay
        if not self.overlay:
            self.overlay = LyricsOverlay(parent=self.control_window)
            self.overlay.start_update_loop()
            self.control_window.after(100, lambda: None)
        
        # Set test lyrics
        self.overlay.set_test_lyrics(lyrics, sync_times)
        
        lyrics_type = "synced" if sync_times else "unsynced"
        self.update_status(f"Testing with {lyrics_type} lyrics")
    
    def close_overlay(self):
        """Close the overlay window."""
        if self.overlay:
            self.overlay.close()
            self.overlay = None
            self.update_status("Overlay closed")
    
    def on_closing(self):
        """Handle window closing."""
        self.stop_monitoring()
        self.close_overlay()
        self.control_window.destroy()
        sys.exit(0)
    
    def run(self):
        """Run the application."""
        # Auto-start monitoring
        self.start_monitoring()
        # Main Tk loop (window hidden)
        self.control_window.mainloop()

if __name__ == "__main__":
    app = LyricsOverlayApp()
    app.run()