"""
Overlay window for displaying lyrics on screen.
Now:
- Transparent tinted background (alpha).
- Resizable and movable with standard window chrome.
- Highlights current line for synced lyrics.
- Smooth auto-scroll for unsynced lyrics.
"""
import tkinter as tk
import time

class LyricsOverlay:
    def __init__(self, parent=None):
        self.root = tk.Toplevel(parent) if parent else tk.Tk()
        self.root.title("Lyrics Overlay")
        self.root.attributes('-topmost', True)

        self.tint_color = '#000000'
        self.root.configure(bg=self.tint_color)
        self.root.resizable(True, True)

        self.update_position()

        self.lyrics_text = tk.Text(
            self.root,
            bg=self.tint_color,
            fg='#FFFFFF',
            font=('Arial', 22, 'bold'),
            wrap=tk.WORD,
            relief=tk.FLAT,
            borderwidth=0,
            padx=30,
            pady=20,
            insertbackground='white',
            selectbackground='gray',
            state=tk.DISABLED,
            height=7
        )
        self.lyrics_text.pack(fill=tk.BOTH, expand=True, anchor='center')
        self.lyrics_text.tag_configure('center', justify='center')
        self.lyrics_text.tag_configure('current_line', foreground='yellow', font=('Arial', 24, 'bold'))
        self.lyrics_text.tag_configure('other_line', foreground='white', font=('Arial', 22, 'bold'))

        self.current_line_index = -1
        self.synced_lyrics = []
        self.is_synced = False
        self.start_time = None
        self.track_duration = 0
        self.user_speed_multiplier = 1.0
        self.user_offset_seconds = 0.0
        self.unsynced_scroll_delay = 5.0

        self.scroll_job = None
        self.user_scrolling = False
        self.manual_override = False

        self.root.bind('<Up>', lambda e: self.adjust_speed(0.1))
        self.root.bind('<Down>', lambda e: self.adjust_speed(-0.1))
        self.root.bind('<Right>', lambda e: self.adjust_offset(1))
        self.root.bind('<Left>', lambda e: self.adjust_offset(-1))
        self.lyrics_text.bind('<MouseWheel>', self.on_user_scroll)
        self.lyrics_text.bind('<Button-4>', self.on_user_scroll)
        self.lyrics_text.bind('<Button-5>', self.on_user_scroll)

    def update_position(self):
        self.root.update_idletasks()
        width = 900
        height = 280
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width - width) // 2
        y = screen_height - height - 50
        self.root.geometry(f'{width}x{height}+{x}+{y}')

    def set_lyrics(self, lyrics_data, track_duration=0, progress_ms=0):
        # Aggressive state reset
        if self.scroll_job:
            self.root.after_cancel(self.scroll_job)
            self.scroll_job = None
        
        self.current_line_index = -1
        self.synced_lyrics = []
        self.start_time = None

        # Set new state
        self.manual_override = False
        self.track_duration = track_duration
        self.is_synced = lyrics_data.get('type') == 'synced'

        if self.is_synced:
            self.set_synced_lyrics(lyrics_data['lyrics'], progress_ms)
        else:
            self.set_unsynced_lyrics(lyrics_data.get('lyrics', ''), progress_ms)

    def set_synced_lyrics(self, lyrics, progress_ms):
        self.synced_lyrics = lyrics
        self.lyrics_text.config(state=tk.NORMAL)
        self.lyrics_text.delete(1.0, tk.END)
        for i, l in enumerate(self.synced_lyrics):
            self.lyrics_text.insert(tk.END, l['line'] + '\n', ('other_line', 'center'))
        self.lyrics_text.config(state=tk.DISABLED)
        
        self.start_time = time.time() - (progress_ms / 1000.0)
        self.update_synced_lyrics()

    def set_unsynced_lyrics(self, lyrics, progress_ms):
        self.unsynced_scroll_delay = 5.0
        self.synced_lyrics = []
        lines = [l.strip() for l in lyrics.split('\n') if l.strip()]
        self.total_seconds = (self.track_duration / 1000.0) if self.track_duration else max(len(lines), 1)

        self.lyrics_text.config(state=tk.NORMAL)
        self.lyrics_text.delete(1.0, tk.END)
        self.lyrics_text.insert(1.0, '\n'.join(lines), 'center')
        self.lyrics_text.config(state=tk.DISABLED)

        self.start_time = time.time() - (progress_ms / 1000.0)
        self.start_smooth_scroll()

    def update_progress(self, progress_ms):
        if self.manual_override:
            return
        
        # Re-sync start_time for both synced and unsynced to prevent clock drift
        self.start_time = time.time() - (progress_ms / 1000.0)
        
        if not self.is_synced:
            if self.total_seconds > 0:
                progress_seconds = progress_ms / 1000.0
                scroll_delay_seconds = self.unsynced_scroll_delay

                if progress_seconds < scroll_delay_seconds:
                    fraction = 0.0
                else:
                    effective_progress = progress_seconds - scroll_delay_seconds
                    effective_duration = self.total_seconds - scroll_delay_seconds
                    if effective_duration > 0:
                        fraction = max(0.0, min(1.0, effective_progress / effective_duration))
                    else:
                        fraction = 1.0
                
                self.lyrics_text.yview_moveto(fraction)

    def update_synced_lyrics(self):
        try:
            # Always reschedule the next call to ensure the loop continues
            if self.scroll_job:
                self.root.after_cancel(self.scroll_job)
            self.scroll_job = self.root.after(50, self.update_synced_lyrics)

            if not self.start_time or not self.synced_lyrics:
                return

            elapsed_ms = (time.time() - self.start_time) * 1000
            
            new_line_index = -1
            for i, l in enumerate(self.synced_lyrics):
                if elapsed_ms >= l['time']:
                    new_line_index = i
                else:
                    break
            
            if new_line_index != self.current_line_index:
                self.lyrics_text.config(state=tk.NORMAL)

                # Remove all 'current_line' tags first to prevent double highlighting
                self.lyrics_text.tag_remove('current_line', '1.0', 'end')
                
                if self.current_line_index != -1:
                    # Make the old line a normal 'other_line'
                    self.lyrics_text.tag_add('other_line', f"{self.current_line_index + 1}.0", f"{self.current_line_index + 1}.end")

                if new_line_index != -1:
                    # Highlight the new line
                    self.lyrics_text.tag_add('current_line', f"{new_line_index + 1}.0", f"{new_line_index + 1}.end")
                    self.lyrics_text.tag_remove('other_line', f"{new_line_index + 1}.0", f"{new_line_index + 1}.end")
                    
                    # Scroll to center the new line
                    line_count = len(self.synced_lyrics)
                    if line_count > 0:
                        self.lyrics_text.update_idletasks()

                        total_display_lines = self.lyrics_text.count("1.0", "end", "displaylines")
                        if isinstance(total_display_lines, tuple):
                            total_display_lines = total_display_lines[0]
                        
                        if total_display_lines is None:
                            return

                        if total_display_lines > 0:
                            start_display_line = self.lyrics_text.count("1.0", f"{new_line_index + 1}.0", "displaylines")
                            if isinstance(start_display_line, tuple):
                                start_display_line = start_display_line[0]

                            next_line_index_str = f"{new_line_index + 2}.0"
                            end_display_line = self.lyrics_text.count("1.0", next_line_index_str, "displaylines")
                            if isinstance(end_display_line, tuple):
                                end_display_line = end_display_line[0]

                            if start_display_line is None or end_display_line is None:
                                return

                            num_display_lines = end_display_line - start_display_line
                            if num_display_lines == 0: num_display_lines = 1

                            center_display_line = start_display_line + (num_display_lines / 2.0)
                            target_center_frac = center_display_line / total_display_lines

                            top_frac, bottom_frac = self.lyrics_text.yview()
                            view_height_frac = bottom_frac - top_frac

                            new_top_frac = target_center_frac - (view_height_frac / 2)

                            if view_height_frac < 1.0:
                                new_top_frac = max(0.0, min(new_top_frac, 1.0 - view_height_frac))
                            else:
                                new_top_frac = 0.0
                            
                            self.lyrics_text.yview_moveto(new_top_frac)

                self.lyrics_text.config(state=tk.DISABLED)
                self.current_line_index = new_line_index

        except Exception as e:
            import traceback
            error_str = traceback.format_exc()
            print(f"Error in update_synced_lyrics: {error_str}")
            self.display_error(error_str)

    def start_smooth_scroll(self):
        if self.scroll_job:
            self.root.after_cancel(self.scroll_job)

        def step():
            if not self.start_time:
                return

            elapsed = (time.time() - self.start_time) * self.user_speed_multiplier + self.user_offset_seconds
            scroll_delay_seconds = self.unsynced_scroll_delay

            if elapsed < scroll_delay_seconds:
                fraction = 0.0
            else:
                effective_progress = elapsed - scroll_delay_seconds
                effective_duration = self.total_seconds - scroll_delay_seconds
                if effective_duration > 0:
                    fraction = max(0.0, min(1.0, effective_progress / effective_duration))
                else:
                    fraction = 1.0

            if not self.user_scrolling:
                self.lyrics_text.yview_moveto(fraction)
            
            self.scroll_job = self.root.after(50, step)

        step()

    def close(self):
        if self.scroll_job:
            self.root.after_cancel(self.scroll_job)
        self.root.destroy()

    def display_error(self, error_message):
        """Displays an error message in the overlay."""
        try:
            self.lyrics_text.config(state=tk.NORMAL)
            self.lyrics_text.delete(1.0, tk.END)
            
            if 'error' not in self.lyrics_text.tag_names():
                self.lyrics_text.tag_configure('error', foreground='red', font=('Arial', 14, 'bold'))

            self.lyrics_text.insert(1.0, f"An error occurred:\n\n{error_message}", ('center', 'error'))
            self.lyrics_text.config(state=tk.DISABLED)
        except Exception as e:
            print(f"--- FALLBACK: FAILED TO DISPLAY ERROR IN OVERLAY ---")
            print(f"Original Error: {error_message}")
            print(f"Error during display: {e}")

    def adjust_speed(self, delta):
        self.user_speed_multiplier = max(0.1, self.user_speed_multiplier + delta)
        print(f"Scroll speed multiplier: {self.user_speed_multiplier:.2f}")

    def adjust_offset(self, delta_seconds):
        self.user_offset_seconds += delta_seconds
        print(f"Scroll offset seconds: {self.user_offset_seconds:+.1f}")

    def on_user_scroll(self, event):
        self.user_scrolling = True
        self.manual_override = True
        if not self.is_synced:
            self.unsynced_scroll_delay = 0.0
        if hasattr(self, '_scroll_resume_job'):
            self.root.after_cancel(self._scroll_resume_job)

        def resume():
            if not self.is_synced:
                top_fraction, _ = self.lyrics_text.yview()
                if self.user_speed_multiplier > 0:
                    elapsed_time_equivalent = (top_fraction * self.total_seconds - self.user_offset_seconds) / self.user_speed_multiplier
                    self.start_time = time.time() - elapsed_time_equivalent
            self.user_scrolling = False

        self._scroll_resume_job = self.root.after(500, resume)