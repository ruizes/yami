"""Sidebar for music classification and listening modes"""

import tkinter as tk
import customtkinter as ctk
import logging
from typing import Optional

from .classification import Genre, ListeningMode


class SidebarFrame(ctk.CTkFrame):
    """Sidebar for artist, genre, and mode selection"""

    def __init__(self, parent):
        super().__init__(parent, corner_radius=10, fg_color="#1a1a1a", width=200)
        self.parent = parent

        # Don't let frame shrink
        self.pack_propagate(False)

        # Current selections
        self.current_mode: Optional[ListeningMode] = None
        self.current_artist: Optional[str] = None
        self.current_genre: Optional[Genre] = None

        # Setup UI
        self.setup_ui()
        logging.debug("Initialized sidebar frame")

    def setup_ui(self):
        # Title
        title_label = ctk.CTkLabel(
            self,
            text="音乐分类",
            font=("roboto", 14, "bold"),
            text_color="#e0e0e0"
        )
        title_label.pack(pady=(10, 5), padx=10, anchor="w")

        # Separator
        separator = ctk.CTkFrame(self, height=2, fg_color="#333333")
        separator.pack(fill="x", padx=10, pady=5)

        # Listening Mode section
        mode_label = ctk.CTkLabel(
            self,
            text="听歌模式",
            font=("roboto", 12, "bold"),
            text_color="#b0b0b0"
        )
        mode_label.pack(pady=(10, 5), padx=10, anchor="w")

        # Mode buttons frame
        self.mode_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.mode_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        # Genre section
        genre_label = ctk.CTkLabel(
            self,
            text="音乐类型",
            font=("roboto", 12, "bold"),
            text_color="#b0b0b0"
        )
        genre_label.pack(pady=(5, 5), padx=10, anchor="w")

        # Genre buttons frame
        self.genre_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.genre_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        # Artist section
        artist_label = ctk.CTkLabel(
            self,
            text="歌手",
            font=("roboto", 12, "bold"),
            text_color="#b0b0b0"
        )
        artist_label.pack(pady=(5, 5), padx=10, anchor="w")

        # Artist buttons frame
        self.artist_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.artist_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        # Reset button
        reset_button = ctk.CTkButton(
            self,
            text="显示全部",
            command=self.reset_filters,
            fg_color="#3aafa9",
            hover_color="#2d9389",
            font=("roboto", 11)
        )
        reset_button.pack(pady=(5, 15), padx=10, fill="x")

        # Create mode buttons
        self.create_mode_buttons()

    def create_mode_buttons(self):
        # Clear existing buttons
        for widget in self.mode_frame.winfo_children():
            widget.destroy()

        # Create buttons for each listening mode
        for mode in ListeningMode:
            btn = ctk.CTkButton(
                self.mode_frame,
                text=mode.value,
                command=lambda m=mode: self.select_mode(m),
                fg_color="#2a2a2a",
                hover_color="#3a3a3a",
                anchor="w",
                font=("roboto", 11)
            )
            btn.pack(fill="x", pady=2)

    def refresh_genre_list(self):
        # Clear existing buttons
        for widget in self.genre_frame.winfo_children():
            widget.destroy()

        # Get available genres from classification manager
        genres = self.parent.classification_manager.get_all_genres()

        # Create buttons for each genre
        for genre in genres:
            count = len(self.parent.classification_manager.get_songs_by_genre(genre))
            btn_text = f"{genre.value} ({count})"
            btn = ctk.CTkButton(
                self.genre_frame,
                text=btn_text,
                command=lambda g=genre: self.select_genre(g),
                fg_color="#2a2a2a",
                hover_color="#3a3a3a",
                anchor="w",
                font=("roboto", 10)
            )
            btn.pack(fill="x", pady=1)

    def refresh_artist_list(self):
        # Clear existing buttons
        for widget in self.artist_frame.winfo_children():
            widget.destroy()

        # Get available artists from classification manager
        artists = self.parent.classification_manager.get_all_artists()

        # Create buttons for each artist
        for artist in artists:
            count = len(self.parent.classification_manager.get_songs_by_artist(artist))
            btn_text = f"{artist} ({count})"
            btn = ctk.CTkButton(
                self.artist_frame,
                text=btn_text,
                command=lambda a=artist: self.select_artist(a),
                fg_color="#2a2a2a",
                hover_color="#3a3a3a",
                anchor="w",
                font=("roboto", 10)
            )
            btn.pack(fill="x", pady=1)

    def select_mode(self, mode: ListeningMode):
        logging.debug("Selected mode: %s", mode.value)
        self.current_mode = mode
        self.current_artist = None
        self.current_genre = None

        # Update button styles
        self._update_mode_button_styles()

        # Filter playlist
        songs = self.parent.classification_manager.get_songs_for_mode(mode)
        self._filter_playlist_by_songs(songs)

    def select_genre(self, genre: Genre):
        logging.debug("Selected genre: %s", genre.value)
        self.current_genre = genre
        self.current_artist = None
        self.current_mode = None

        # Update button styles
        self._update_genre_button_styles()

        # Filter playlist
        songs = self.parent.classification_manager.get_songs_by_genre(genre)
        self._filter_playlist_by_songs(songs)

    def select_artist(self, artist: str):
        logging.debug("Selected artist: %s", artist)
        self.current_artist = artist
        self.current_genre = None
        self.current_mode = None

        # Update button styles
        self._update_artist_button_styles()

        # Filter playlist
        songs = self.parent.classification_manager.get_songs_by_artist(artist)
        self._filter_playlist_by_songs(songs)

    def reset_filters(self):
        logging.debug("Resetting all filters")
        self.current_artist = None
        self.current_genre = None
        self.current_mode = None

        # Reset button styles
        self._update_mode_button_styles()
        self._update_genre_button_styles()
        self._update_artist_button_styles()

        # Show all songs
        all_songs = self.parent.classification_manager.all_songs
        self._filter_playlist_by_songs(all_songs)

    def _update_mode_button_styles(self):
        for widget in self.mode_frame.winfo_children():
            if isinstance(widget, ctk.CTkButton):
                text = widget.cget("text")
                if self.current_mode and text == self.current_mode.value:
                    widget.configure(fg_color="#3aafa9")
                else:
                    widget.configure(fg_color="#2a2a2a")

    def _update_genre_button_styles(self):
        for widget in self.genre_frame.winfo_children():
            if isinstance(widget, ctk.CTkButton):
                text = widget.cget("text")
                if self.current_genre and text.startswith(self.current_genre.value):
                    widget.configure(fg_color="#3aafa9")
                else:
                    widget.configure(fg_color="#2a2a2a")

    def _update_artist_button_styles(self):
        for widget in self.artist_frame.winfo_children():
            if isinstance(widget, ctk.CTkButton):
                text = widget.cget("text")
                if self.current_artist and text.startswith(self.current_artist):
                    widget.configure(fg_color="#3aafa9")
                else:
                    widget.configure(fg_color="#2a2a2a")

    def _filter_playlist_by_songs(self, songs):
        # Update filtered playlist
        self.parent.filtered_playlist = songs

        # Clear playlist UI
        self.parent.playlist_frame.song_list.delete(0, tk.END)

        # Create new media list
        self.parent.media_list = self.parent.vlc_instance.media_list_new()
        self.parent.music_list_player.set_media_list(self.parent.media_list)

        # Add filtered songs to playlist
        for song in songs:
            media = self.parent.vlc_instance.media_new(song.file_path)
            self.parent.media_list.add_media(media)

            # Use actual metadata
            artist = song.artist or "Unknown Artist"
            title = song.title or song.filename
            self.parent.playlist_frame.song_list.insert(
                "end", f"• {title} - {artist}"
            )

        logging.info("Filtered playlist to %d songs", len(songs))
