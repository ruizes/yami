"""Lyrics Parser and Manager"""

import re
import os
import logging
from pathlib import Path
from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple


@dataclass
class LyricLine:
    time: float
    text: str


class LyricsParser:
    def __init__(self):
        self.lyrics: List[LyricLine] = []
        self.title: str = ""
        self.artist: str = ""
        self.album: str = ""

    def parse_lrc_file(self, lrc_path: str) -> bool:
        try:
            if not os.path.exists(lrc_path):
                return False
            
            with open(lrc_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            return self.parse_lrc_content(content)
        except Exception as e:
            logging.exception(e)
            return False

    def parse_lrc_content(self, content: str) -> bool:
        self.lyrics = []
        lines = content.strip().split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            if line.startswith('[ti:'):
                self.title = self._extract_tag(line, 'ti')
            elif line.startswith('[ar:'):
                self.artist = self._extract_tag(line, 'ar')
            elif line.startswith('[al:'):
                self.album = self._extract_tag(line, 'al')
            else:
                lyric_lines = self._parse_lyric_line(line)
                self.lyrics.extend(lyric_lines)
        
        self.lyrics.sort(key=lambda x: x.time)
        return len(self.lyrics) > 0

    def _extract_tag(self, line: str, tag: str) -> str:
        match = re.match(r'\[' + tag + r':(.*)\]', line)
        if match:
            return match.group(1).strip()
        return ""

    def _parse_lyric_line(self, line: str) -> List[LyricLine]:
        results = []
        pattern = r'\[(\d+):(\d+)\.(\d+)\](.*)'
        matches = re.findall(pattern, line)
        
        for match in matches:
            minutes = int(match[0])
            seconds = int(match[1])
            milliseconds = int(match[2])
            text = match[3].strip()
            
            total_seconds = minutes * 60 + seconds + milliseconds / 1000
            if text:
                results.append(LyricLine(time=total_seconds, text=text))
        
        return results

    def get_lyric_at_time(self, current_time: float) -> Tuple[Optional[str], int]:
        if not self.lyrics:
            return None, -1
        
        for i, lyric in enumerate(self.lyrics):
            if lyric.time > current_time:
                if i > 0:
                    return self.lyrics[i-1].text, i-1
                return self.lyrics[0].text, 0
        
        if self.lyrics:
            return self.lyrics[-1].text, len(self.lyrics) - 1
        
        return None, -1

    def get_surrounding_lyrics(self, current_time: float, count: int = 2) -> Dict[str, str]:
        result = {
            'previous': [],
            'current': '',
            'next': []
        }
        
        current_text, current_idx = self.get_lyric_at_time(current_time)
        
        if current_idx >= 0:
            result['current'] = current_text
            
            for i in range(max(0, current_idx - count), current_idx):
                result['previous'].append(self.lyrics[i].text)
            
            for i in range(current_idx + 1, min(len(self.lyrics), current_idx + count + 1)):
                result['next'].append(self.lyrics[i].text)
        
        return result

    def is_empty(self) -> bool:
        return len(self.lyrics) == 0


class LyricsManager:
    def __init__(self):
        self.parser = LyricsParser()
        self.favorites: set = set()
        self._load_favorites()

    def load_lyrics_for_song(self, song_path: str) -> bool:
        song_path = Path(song_path)
        lrc_path = song_path.with_suffix('.lrc')
        
        if lrc_path.exists():
            return self.parser.parse_lrc_file(str(lrc_path))
        
        lrc_path2 = song_path.parent / (song_path.stem + '.lrc')
        if lrc_path2.exists():
            return self.parser.parse_lrc_file(str(lrc_path2))
        
        return False

    def get_current_lyric(self, current_time: float) -> Tuple[Optional[str], int]:
        return self.parser.get_lyric_at_time(current_time)

    def get_surrounding_lyrics(self, current_time: float, count: int = 2) -> Dict[str, str]:
        return self.parser.get_surrounding_lyrics(current_time, count)

    def has_lyrics(self) -> bool:
        return not self.parser.is_empty()

    def toggle_favorite(self, song_title: str) -> bool:
        if song_title in self.favorites:
            self.favorites.remove(song_title)
            self._save_favorites()
            return False
        else:
            self.favorites.add(song_title)
            self._save_favorites()
            return True

    def is_favorite(self, song_title: str) -> bool:
        return song_title in self.favorites

    def _load_favorites(self):
        try:
            favorites_path = Path.home() / '.yami_favorites.txt'
            if favorites_path.exists():
                with open(favorites_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        self.favorites.add(line.strip())
        except Exception as e:
            logging.exception(e)

    def _save_favorites(self):
        try:
            favorites_path = Path.home() / '.yami_favorites.txt'
            with open(favorites_path, 'w', encoding='utf-8') as f:
                for title in self.favorites:
                    f.write(title + '\n')
        except Exception as e:
            logging.exception(e)
