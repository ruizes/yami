"""Top Bar"""

import asyncio
import logging
import tkinter as tk
from tkinter import filedialog, simpledialog
import os
from pathlib import Path

import customtkinter as ctk
import spotdl.utils
import spotdl.utils.formatter
import spotdl.utils.search
import spotdl
from mutagen import File as MutagenFile

from .util import SUPPORTED_FORMATS
from .classification import SongInfo, Genre


class TopBar(ctk.CTkFrame):
    """Holds Download And Open Buttons"""

    def __init__(self, parent):
        super().__init__(parent, fg_color="#121212")
        self.parent = parent

        # WIDGETS
        self.open_folder = ctk.CTkButton(
            self,
            command=self.choose_folder,
            text="Open",
            font=("roboto", 15),
            width=70,
            image=parent.folder_icon,
        )
        
        # Download button - only enabled if downloader is available
        if hasattr(parent, 'downloader') and parent.downloader is not None:
            self.music_downloader = ctk.CTkButton(
                self,
                text="Download",
                font=("roboto", 15),
                width=70,
                image=parent.music_icon,
                command=self.prompt_download,
            )
        else:
            self.music_downloader = ctk.CTkButton(
                self,
                text="Download",
                font=("roboto", 15),
                width=70,
                image=parent.music_icon,
                state="disabled",
                fg_color="#555555",
                hover_color="#555555",
            )

        self.yami = ctk.CTkButton(
            self,
            text="About",
            font=("roboto", 15),
            width=70,
            image=parent.music_icon,
        )

        # WIDGET PLACEMENT
        self.open_folder.grid(row=0, column=1, sticky="w", pady=5, padx=10)
        self.music_downloader.grid(row=0, column=2, sticky="w", pady=5, padx=10)
        self.yami.grid(row=0, column=3, sticky="w", pady=5, padx=10)
        logging.debug("initialized topbar")

    def choose_folder(self, _event=None):

        self.parent.current_folder = filedialog.askdirectory(
            title="Select Music Folder"
        )
        if not self.parent.current_folder:
            return

        # CLEAR PLAYLIST, LISTBOX AND CLASSIFICATION DATA
        self.parent.playlist_frame.song_list.delete(0, tk.END)
        self.parent.classification_manager.clear()
        
        # Create a simple list to hold file paths
        self.parent.media_list = []

        # FILTER MUSIC FILES
        for root, _, files in os.walk(self.parent.current_folder):
            music_files = [file for file in files if file.endswith(SUPPORTED_FORMATS)]

            for file in music_files:
                file_path = os.path.join(root, file)
                
                # Get artist and title from metadata
                artistname, title = self.get_name_and_title_from_file(file_path)
                
                # Create SongInfo and classify
                song_info = SongInfo(
                    file_path=file_path,
                    title=title or "",
                    artist=artistname or "",
                    filename=file
                )
                # Auto-classify based on filename and metadata
                song_info.genre = self.parent.classification_manager.classify_song_by_content(song_info)
                self.parent.classification_manager.add_song(song_info)
                
                # Add to media list for playback
                self.parent.media_list.append(file_path)
                
                # Add to UI
                display_title = title if title else os.path.splitext(file)[0]
                display_artist = artistname if artistname else "Unknown Artist"
                self.parent.playlist_frame.song_list.insert(
                    "end", f"• {display_title} - {display_artist}"
                )
        
        # Set the playlist in the audio player
        self.parent.music_list_player.set_media_list(self.parent.media_list)
        
        # Update filtered playlist
        self.parent.filtered_playlist = self.parent.classification_manager.all_songs.copy()
        
        # Update sidebar if it exists
        if hasattr(self.parent, 'sidebar_frame'):
            self.parent.sidebar_frame.refresh_artist_list()
            self.parent.sidebar_frame.refresh_genre_list()
        
        os.chdir(self.parent.current_folder)
        logging.info("Loaded %d songs, grouped into %d artists and %d genres", 
                     len(self.parent.classification_manager.all_songs),
                     len(self.parent.classification_manager.songs_by_artist),
                     len(self.parent.classification_manager.songs_by_genre))

    def prompt_download(self):
        if self.parent.downloader is None:
            logging.warning("Downloader not available (ffmpeg may be missing)")
            return
            
        if not self.parent.current_folder:
            self.choose_folder()
        song_url = simpledialog.askstring(
            "Download Music", "Enter the name of the song:"
        )
        if song_url:
            self.parent.loop.create_task(self.download_song(song_url))

    def get_name_and_title_from_file(self, file_path: str):
        """Get song artist name and title from file metadata using mutagen"""

        logging.debug("getting song artist name + title from file: %s", file_path)
        try:
            audio = MutagenFile(file_path)
            if audio is None:
                # If no metadata, use filename
                filename = os.path.splitext(os.path.basename(file_path))[0]
                # Try to parse filename like "Artist - Title"
                if " - " in filename:
                    parts = filename.split(" - ", 1)
                    return parts[0].strip(), parts[1].strip()
                return "", filename
            
            title = ""
            artist = ""
            
            # Try different tag formats
            if hasattr(audio, 'tags') and audio.tags:
                # ID3 tags (mp3)
                if 'TIT2' in audio.tags:
                    title = str(audio.tags['TIT2'])
                elif 'title' in audio.tags:
                    title = str(audio.tags['title'][0])
                
                if 'TPE1' in audio.tags:
                    artist = str(audio.tags['TPE1'])
                elif 'artist' in audio.tags:
                    artist = str(audio.tags['artist'][0])
            
            # If no metadata, use filename
            if not title:
                filename = os.path.splitext(os.path.basename(file_path))[0]
                if " - " in filename:
                    parts = filename.split(" - ", 1)
                    artist = artist or parts[0].strip()
                    title = parts[1].strip()
                else:
                    title = filename
            
            return artist, title
            
        except Exception as e:
            logging.exception(e)
            # Fallback to filename
            filename = os.path.splitext(os.path.basename(file_path))[0]
            if " - " in filename:
                parts = filename.split(" - ", 1)
                return parts[0].strip(), parts[1].strip()
            return "", filename

    async def download_song(self, song_url):
        try:
            logging.info("searching %s", song_url)

            # ASYNC UNTIL DOWNLOAD GETS OVER
            song, path = await asyncio.ensure_future(
                asyncio.to_thread(
                    self.parent.downloader.search_and_download,
                    spotdl.utils.search.get_simple_songs([song_url])[0],
                )
            )
            await asyncio.sleep(0)  # STOP FROM FREEZING
            logging.info("saving file")
            self.downloaded_song_path = os.path.join(
                self.parent.current_folder,
                spotdl.utils.formatter.create_file_name(
                    song=song,
                    template=self.parent.downloader.settings["output"],
                    file_extension=self.parent.downloader.settings["format"],
                    restrict=self.parent.downloader.settings["restrict"],
                    file_name_length=self.parent.downloader.settings[
                        "max_filename_length"
                    ],
                ),
            )
            logging.info("saved at %s", self.downloaded_song_path)
        except Exception as e:
            logging.error(e)
            return

        # Add the new song to the classification and playlist
        if os.path.exists(self.downloaded_song_path):
            artistname, title = self.get_name_and_title_from_file(self.downloaded_song_path)
            
            # Create SongInfo and classify
            song_info = SongInfo(
                file_path=self.downloaded_song_path,
                title=title or "",
                artist=artistname or "",
                filename=os.path.basename(self.downloaded_song_path)
            )
            song_info.genre = self.parent.classification_manager.classify_song_by_content(song_info)
            self.parent.classification_manager.add_song(song_info)
            
            # Add to media list
            if hasattr(self.parent, 'media_list'):
                self.parent.media_list.append(self.downloaded_song_path)
            
            # Update filtered playlist
            self.parent.filtered_playlist = self.parent.classification_manager.all_songs.copy()
            
            # Update UI
            display_title = title if title else os.path.splitext(os.path.basename(self.downloaded_song_path))[0]
            display_artist = artistname if artistname else "Unknown Artist"
            self.parent.playlist_frame.song_list.insert(
                "end", f"• {display_title} - {display_artist}"
            )
            
            # Update sidebar
            if hasattr(self.parent, 'sidebar_frame'):
                self.parent.sidebar_frame.refresh_artist_list()
                self.parent.sidebar_frame.refresh_genre_list()
