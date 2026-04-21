"""Test script to verify all modules can be imported"""

import sys
import os

# Add the project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("Testing imports...")

# Test pygame first
print("1. Testing pygame...")
import pygame
print(f"   Pygame version: {pygame.version.ver}")

# Test customtkinter
print("2. Testing customtkinter...")
import customtkinter as ctk
print(f"   CustomTkinter loaded")

# Test mutagen
print("3. Testing mutagen...")
from mutagen import File
print(f"   Mutagen loaded")

# Test our modules
print("4. Testing yami.util...")
from yami.util import GEOMETRY, TITLE, SUPPORTED_FORMATS
print(f"   Geometry: {GEOMETRY}, Title: {TITLE}")

print("5. Testing yami.classification...")
from yami.classification import ClassificationManager, Genre, ListeningMode, SongInfo
print(f"   Genres: {[g.value for g in Genre]}")
print(f"   Modes: {[m.value for m in ListeningMode]}")

print("6. Testing yami.audio_player...")
from yami.audio_player import AudioPlayer, State, VLCCompatPlayer
print(f"   AudioPlayer loaded, State: {State}")

print("7. Testing yami.sidebar...")
from yami.sidebar import SidebarFrame
print(f"   SidebarFrame loaded")

print("8. Testing yami.playlist...")
from yami.playlist import PlaylistFrame
print(f"   PlaylistFrame loaded")

print("9. Testing yami.control...")
from yami.control import ControlBar
print(f"   ControlBar loaded")

print("10. Testing yami.topbar...")
from yami.topbar import TopBar
print(f"   TopBar loaded")

print("11. Testing yami.cover_art...")
from yami.cover_art import CoverArtFrame
print(f"   CoverArtFrame loaded")

print("12. Testing yami.progress...")
from yami.progress import BottomFrame
print(f"   BottomFrame loaded")

print("\n✅ All imports successful!")

# Quick test of classification
print("\nTesting classification functionality...")
cm = ClassificationManager()

# Test songs with different keywords
test_songs = [
    ("artist1 - 摇滚歌曲.mp3", "摇滚歌曲", "Artist1"),
    ("artist2 - 助眠音乐.mp3", "助眠音乐", "Artist2"),
    ("artist1 - DJ 混音.mp3", "DJ 混音", "Artist1"),
    ("artist3 - 抖音热歌.mp3", "抖音热歌", "Artist3"),
    ("artist4 - Lo-Fi 放松.mp3", "Lo-Fi 放松", "Artist4"),
    ("artist5 - Classical Symphony.mp3", "Classical Symphony", "Artist5"),
]

for filename, title, artist in test_songs:
    song = SongInfo(file_path=f"/test/{filename}", title=title, artist=artist, filename=filename)
    song.genre = cm.classify_song_by_content(song)
    cm.add_song(song)
    print(f"   {filename} -> Genre: {song.genre.value}")

print(f"\n   Total songs: {len(cm.all_songs)}")
print(f"   Artists: {cm.get_all_artists()}")
print(f"   Songs for DJ mode: {len(cm.get_songs_for_mode(ListeningMode.DJ))}")
print(f"   Songs for Sleep mode: {len(cm.get_songs_for_mode(ListeningMode.SLEEP))}")

print("\n✅ All tests passed!")
