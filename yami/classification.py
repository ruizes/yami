"""Music Classification Module"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Set
import logging
import os


class Genre(Enum):
    ROCK = "摇滚"
    POP = "流行"
    HIPHOP = "嘻哈"
    ELECTRONIC = "电子"
    JAZZ = "爵士"
    CLASSICAL = "古典"
    COUNTRY = "乡村"
    RNB = "R&B"
    TIKTOK_HOT = "抖音热歌"
    SLEEP = "助眠"
    DJ = "DJ"
    LOFI = "Lo-Fi"
    INSTRUMENTAL = "纯音乐"
    CHINESE = "华语"
    ENGLISH = "欧美"
    JAPANESE = "日语"
    KOREAN = "韩语"
    OTHER = "其他"


class ListeningMode(Enum):
    RANDOM = "随机模式"
    ROCK = "摇滚模式"
    TIKTOK = "抖音模式"
    SLEEP = "睡眠模式"
    DJ = "DJ模式"
    LOFI = "Lo-Fi模式"
    JAZZ = "爵士模式"
    CLASSICAL = "古典模式"
    POP = "流行模式"
    WORK = "工作模式"
    EXERCISE = "运动模式"
    RELAX = "放松模式"


GENRE_KEYWORDS = {
    Genre.ROCK: ["rock", "摇滚", "punk", "金属", "metal", "alternative"],
    Genre.POP: ["pop", "流行", "流行乐"],
    Genre.HIPHOP: ["hiphop", "hip hop", "rap", "嘻哈", "说唱"],
    Genre.ELECTRONIC: ["electronic", "电子", "edm", "dance"],
    Genre.JAZZ: ["jazz", "爵士"],
    Genre.CLASSICAL: ["classical", "古典", "orchestra", "交响乐"],
    Genre.COUNTRY: ["country", "乡村"],
    Genre.RNB: ["r&b", "rnb", "节奏布鲁斯"],
    Genre.TIKTOK_HOT: ["tiktok", "抖音", "热歌", "热门", "trending", "流行歌曲"],
    Genre.SLEEP: ["sleep", "助眠", "催眠", "放松", "relax", "peaceful", "meditation"],
    Genre.DJ: ["dj", "电音", "混音", "mix", "remix", "club", "舞曲"],
    Genre.LOFI: ["lofi", "lo-fi", "chill", "慢摇"],
    Genre.INSTRUMENTAL: ["instrumental", "纯音乐", "轻音乐"],
    Genre.CHINESE: ["华语", "中文", "chinese", "国语"],
    Genre.ENGLISH: ["english", "欧美", "英文", "english"],
    Genre.JAPANESE: ["japanese", "日语", "日本", "jpop"],
    Genre.KOREAN: ["korean", "韩语", "韩国", "kpop"],
}

MODE_TO_GENRES = {
    ListeningMode.RANDOM: [],
    ListeningMode.ROCK: [Genre.ROCK, Genre.DJ],
    ListeningMode.TIKTOK: [Genre.TIKTOK_HOT, Genre.POP],
    ListeningMode.SLEEP: [Genre.SLEEP, Genre.CLASSICAL, Genre.LOFI, Genre.INSTRUMENTAL],
    ListeningMode.DJ: [Genre.DJ, Genre.ELECTRONIC, Genre.ROCK],
    ListeningMode.LOFI: [Genre.LOFI, Genre.JAZZ],
    ListeningMode.JAZZ: [Genre.JAZZ],
    ListeningMode.CLASSICAL: [Genre.CLASSICAL],
    ListeningMode.POP: [Genre.POP, Genre.TIKTOK_HOT],
    ListeningMode.WORK: [Genre.LOFI, Genre.INSTRUMENTAL, Genre.CLASSICAL],
    ListeningMode.EXERCISE: [Genre.ROCK, Genre.DJ, Genre.HIPHOP, Genre.ELECTRONIC],
    ListeningMode.RELAX: [Genre.SLEEP, Genre.LOFI, Genre.JAZZ, Genre.INSTRUMENTAL],
}


@dataclass
class SongInfo:
    file_path: str
    title: str = ""
    artist: str = ""
    album: str = ""
    genre: Genre = Genre.OTHER
    filename: str = ""
    
    def __post_init__(self):
        if not self.filename:
            self.filename = os.path.basename(self.file_path)


@dataclass
class ClassificationManager:
    songs_by_artist: Dict[str, List[SongInfo]] = field(default_factory=dict)
    songs_by_genre: Dict[Genre, List[SongInfo]] = field(default_factory=dict)
    all_songs: List[SongInfo] = field(default_factory=list)
    current_mode: ListeningMode = ListeningMode.RANDOM
    current_artist: Optional[str] = None
    current_genre: Optional[Genre] = None
    
    def add_song(self, song: SongInfo):
        self.all_songs.append(song)
        
        if song.artist:
            if song.artist not in self.songs_by_artist:
                self.songs_by_artist[song.artist] = []
            self.songs_by_artist[song.artist].append(song)
        
        if song.genre not in self.songs_by_genre:
            self.songs_by_genre[song.genre] = []
        self.songs_by_genre[song.genre].append(song)
        
        logging.debug("Added song: %s - %s (genre: %s)", song.artist, song.title, song.genre)
    
    def classify_song_by_content(self, song: SongInfo) -> Genre:
        combined_text = f"{song.title} {song.artist} {song.album} {song.filename}".lower()
        
        for genre, keywords in GENRE_KEYWORDS.items():
            for keyword in keywords:
                if keyword.lower() in combined_text:
                    return genre
        
        return Genre.OTHER
    
    def get_songs_by_artist(self, artist: str) -> List[SongInfo]:
        return self.songs_by_artist.get(artist, [])
    
    def get_songs_by_genre(self, genre: Genre) -> List[SongInfo]:
        return self.songs_by_genre.get(genre, [])
    
    def get_songs_for_mode(self, mode: ListeningMode) -> List[SongInfo]:
        self.current_mode = mode
        
        if mode == ListeningMode.RANDOM:
            return self.all_songs
        
        genres = MODE_TO_GENRES.get(mode, [])
        songs = []
        for genre in genres:
            songs.extend(self.songs_by_genre.get(genre, []))
        
        return songs
    
    def get_all_artists(self) -> List[str]:
        return sorted(list(self.songs_by_artist.keys()))
    
    def get_all_genres(self) -> List[Genre]:
        return sorted(list(self.songs_by_genre.keys()), key=lambda g: g.value)
    
    def clear(self):
        self.songs_by_artist.clear()
        self.songs_by_genre.clear()
        self.all_songs.clear()
        self.current_artist = None
        self.current_genre = None
        logging.debug("Cleared classification data")
