"""Audio Player using pygame.mixer as an alternative to VLC"""

import os
import logging
import threading
from pathlib import Path
from typing import Callable, Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum

import pygame
from mutagen import File as MutagenFile


class PlayerState(Enum):
    PLAYING = 1
    PAUSED = 2
    STOPPED = 3


@dataclass
class MediaInfo:
    file_path: str
    title: str = ""
    artist: str = ""
    album: str = ""
    duration: float = 0.0
    cover_path: Optional[str] = None


class AudioPlayer:
    """Audio player using pygame.mixer"""

    def __init__(self):
        pygame.mixer.init()
        self._playlist: List[str] = []
        self._current_index: int = 0
        self._state: PlayerState = PlayerState.STOPPED
        self._media_info_cache: Dict[str, MediaInfo] = {}
        self._end_callback: Optional[Callable] = None
        self._progress_thread: Optional[threading.Thread] = None
        self._running: bool = False
        self._start_position: float = 0.0
        self._start_time: float = 0.0
        
        self._volume: float = 1.0
        self._media: Optional[pygame.mixer.Sound] = None
        self._channel: Optional[pygame.mixer.Channel] = None
        
        logging.debug("Pygame audio player initialized")

    def set_playlist(self, playlist: List[str]):
        """Set the playlist"""
        self._playlist = playlist.copy()
        logging.debug("Playlist set with %d songs", len(playlist))

    def get_playlist(self) -> List[str]:
        """Get the playlist"""
        return self._playlist.copy()

    def play(self, index: int = 0):
        """Play song at given index"""
        if not self._playlist or index < 0 or index >= len(self._playlist):
            logging.warning("Invalid index or empty playlist")
            return

        self._current_index = index
        file_path = self._playlist[index]
        
        try:
            # Stop any current playback
            self.stop()
            
            # Load and play
            pygame.mixer.music.load(file_path)
            pygame.mixer.music.set_volume(self._volume)
            pygame.mixer.music.play()
            
            self._state = PlayerState.PLAYING
            self._start_position = 0.0
            self._start_time = pygame.time.get_ticks() / 1000.0
            
            # Set up end of track callback
            self._setup_end_callback()
            
            logging.debug("Playing: %s", file_path)
        except Exception as e:
            logging.error("Failed to play %s: %s", file_path, e)
            self._state = PlayerState.STOPPED

    def play_item_at_index(self, index: int):
        """Alias for play() to match VLC API"""
        self.play(index)

    def pause(self):
        """Pause playback"""
        if self._state == PlayerState.PLAYING:
            pygame.mixer.music.pause()
            self._state = PlayerState.PAUSED
            logging.debug("Paused")

    def resume(self):
        """Resume playback"""
        if self._state == PlayerState.PAUSED:
            pygame.mixer.music.unpause()
            self._state = PlayerState.PLAYING
            logging.debug("Resumed")

    def stop(self):
        """Stop playback"""
        pygame.mixer.music.stop()
        self._state = PlayerState.STOPPED
        self._running = False
        logging.debug("Stopped")

    def play_next(self):
        """Play next song in playlist"""
        if not self._playlist:
            return
        
        next_index = (self._current_index + 1) % len(self._playlist)
        self.play(next_index)
        
        # Call callback if set
        if self._end_callback:
            try:
                self._end_callback(None)
            except Exception as e:
                logging.error("End callback error: %s", e)

    def play_previous(self):
        """Play previous song in playlist"""
        if not self._playlist:
            return
        
        prev_index = (self._current_index - 1) % len(self._playlist)
        self.play(prev_index)

    def get_state(self) -> PlayerState:
        """Get current player state"""
        return self._state

    def get_current_index(self) -> int:
        """Get current song index"""
        return self._current_index

    def get_position(self) -> float:
        """Get current position in seconds (0.0 to 1.0)"""
        if not pygame.mixer.music.get_busy():
            return 0.0
        
        # Get current position in milliseconds
        try:
            current_ms = pygame.mixer.music.get_pos()
            if current_ms < 0:
                return 0.0
            
            duration = self.get_length()
            if duration > 0:
                return current_ms / (duration * 1000)
        except Exception as e:
            logging.error("Error getting position: %s", e)
        
        return 0.0

    def get_length(self) -> float:
        """Get current song length in seconds"""
        if not self._playlist or self._current_index < 0 or self._current_index >= len(self._playlist):
            return 0.0
        
        file_path = self._playlist[self._current_index]
        try:
            if file_path not in self._media_info_cache:
                self._extract_media_info(file_path)
            
            return self._media_info_cache[file_path].duration
        except Exception as e:
            logging.error("Error getting length: %s", e)
            return 0.0

    def set_volume(self, volume: float):
        """Set volume (0.0 to 1.0)"""
        self._volume = max(0.0, min(1.0, volume))
        pygame.mixer.music.set_volume(self._volume)

    def get_volume(self) -> float:
        """Get current volume"""
        return self._volume

    def set_end_callback(self, callback: Callable):
        """Set callback for when song ends"""
        self._end_callback = callback

    def _setup_end_callback(self):
        """Set up end of track detection"""
        def check_end():
            while self._state == PlayerState.PLAYING:
                # Check if music is still playing
                if not pygame.mixer.music.get_busy():
                    # Wait a bit to make sure it's really the end
                    import time
                    time.sleep(0.1)
                    if not pygame.mixer.music.get_busy() and self._state == PlayerState.PLAYING:
                        self.play_next()
                        break
                import time
                time.sleep(0.1)
        
        thread = threading.Thread(target=check_end, daemon=True)
        thread.start()

    def _extract_media_info(self, file_path: str) -> MediaInfo:
        """Extract media info using mutagen"""
        if file_path in self._media_info_cache:
            return self._media_info_cache[file_path]
        
        try:
            audio = MutagenFile(file_path)
            if audio is None:
                info = MediaInfo(file_path=file_path, filename=os.path.basename(file_path))
                self._media_info_cache[file_path] = info
                return info
            
            # Get title
            title = ""
            if hasattr(audio, 'tags') and audio.tags:
                if 'TIT2' in audio.tags:
                    title = str(audio.tags['TIT2'])
                elif 'title' in audio.tags:
                    title = str(audio.tags['title'][0])
            
            # Get artist
            artist = ""
            if hasattr(audio, 'tags') and audio.tags:
                if 'TPE1' in audio.tags:
                    artist = str(audio.tags['TPE1'])
                elif 'artist' in audio.tags:
                    artist = str(audio.tags['artist'][0])
            
            # Get album
            album = ""
            if hasattr(audio, 'tags') and audio.tags:
                if 'TALB' in audio.tags:
                    album = str(audio.tags['TALB'])
                elif 'album' in audio.tags:
                    album = str(audio.tags['album'][0])
            
            # Get duration
            duration = 0.0
            if hasattr(audio, 'info') and audio.info:
                if hasattr(audio.info, 'length'):
                    duration = audio.info.length
            
            # Use filename if no title
            if not title:
                title = os.path.splitext(os.path.basename(file_path))[0]
            
            info = MediaInfo(
                file_path=file_path,
                title=title,
                artist=artist,
                album=album,
                duration=duration
            )
            self._media_info_cache[file_path] = info
            return info
            
        except Exception as e:
            logging.error("Error extracting media info: %s", e)
            info = MediaInfo(
                file_path=file_path,
                title=os.path.splitext(os.path.basename(file_path))[0]
            )
            self._media_info_cache[file_path] = info
            return info

    def get_meta(self, meta_type: int = 0) -> str:
        """Get metadata (simulates VLC's get_meta)
        0 = Title, 1 = Artist, 4 = Album, 15 = Cover (not supported)
        """
        if not self._playlist or self._current_index < 0 or self._current_index >= len(self._playlist):
            return ""
        
        file_path = self._playlist[self._current_index]
        info = self._extract_media_info(file_path)
        
        if meta_type == 0:  # Title
            return info.title
        elif meta_type == 1:  # Artist
            return info.artist
        elif meta_type == 4:  # Album
            return info.album
        elif meta_type == 15:  # Cover
            return ""
        
        return ""

    def is_playing(self) -> bool:
        """Check if currently playing"""
        return self._state == PlayerState.PLAYING

    def is_paused(self) -> bool:
        """Check if currently paused"""
        return self._state == PlayerState.PAUSED

    def quit(self):
        """Clean up"""
        self._running = False
        pygame.mixer.music.stop()
        pygame.mixer.quit()
        logging.debug("Audio player quit")


# VLC compatibility classes and constants
class State:
    """Simulate VLC State enum"""
    Playing = PlayerState.PLAYING
    Paused = PlayerState.PAUSED
    Stopped = PlayerState.STOPPED


class EventType:
    """Simulate VLC EventType enum"""
    MediaListPlayerNextItemSet = "MediaListPlayerNextItemSet"


# Compatibility wrapper for easy migration
class VLCCompatPlayer:
    """VLC-compatible interface using pygame"""

    def __init__(self):
        self.player = AudioPlayer()
        self._event_manager = _EventManager(self)

    @property
    def vlc_instance(self):
        return self

    @property
    def music(self):
        return self.player

    @property
    def music_list_player(self):
        return self

    def event_manager(self):
        return self._event_manager

    def set_media_list(self, media_list):
        """Set media list (list of file paths)"""
        self.player.set_playlist(media_list)

    def media_list_new(self):
        """Create new media list"""
        return []

    def media_new(self, file_path: str):
        """Create media (just return the path)"""
        return file_path

    def play_item_at_index(self, index: int):
        self.player.play(index)

    def play(self):
        if self.player.is_paused():
            self.player.resume()
        else:
            self.player.play(self.player.get_current_index())

    def pause(self):
        self.player.pause()

    def next(self):
        self.player.play_next()

    def previous(self):
        self.player.play_previous()

    def stop(self):
        self.player.stop()

    def get_state(self):
        state = self.player.get_state()
        if state == PlayerState.PLAYING:
            return State.Playing
        elif state == PlayerState.PAUSED:
            return State.Paused
        return State.Stopped

    def get_media_player(self):
        return self.player

    def get_media(self):
        if not self.player._playlist:
            return None
        idx = self.player.get_current_index()
        if idx < 0 or idx >= len(self.player._playlist):
            return None
        return _MediaCompat(self.player._playlist[idx], self.player)


class _MediaCompat:
    """Compatibility wrapper for media"""

    def __init__(self, file_path: str, player: AudioPlayer):
        self.file_path = file_path
        self.player = player

    def is_parsed(self):
        return True

    def parse(self):
        pass

    def get_meta(self, meta_type: int):
        # Extract info from file
        try:
            if self.file_path in self.player._media_info_cache:
                info = self.player._media_info_cache[self.file_path]
            else:
                info = self.player._extract_media_info(self.file_path)
            
            if meta_type == 0:  # Title
                return info.title
            elif meta_type == 1:  # Artist
                return info.artist
            elif meta_type == 4:  # Album
                return info.album
            elif meta_type == 15:  # Cover
                return ""
        except Exception:
            pass
        return ""


class _EventManager:
    """Simulate VLC event manager"""

    def __init__(self, player: VLCCompatPlayer):
        self.player = player
        self._callbacks: Dict[str, List[Callable]] = {}

    def event_attach(self, event_type: str, callback: Callable):
        if event_type not in self._callbacks:
            self._callbacks[event_type] = []
        self._callbacks[event_type].append(callback)
