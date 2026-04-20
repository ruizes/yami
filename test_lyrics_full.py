"""迷你桌面歌词功能测试 - 完整独立版本"""

import tkinter as tk
import customtkinter as ctk
from PIL import Image, ImageDraw
import logging
import re
import os
from pathlib import Path
from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple
from enum import Enum
import threading
import time

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


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

    def get_surrounding_lyrics(self, current_time: float, count: int = 2) -> Dict:
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

    def get_surrounding_lyrics(self, current_time: float, count: int = 2) -> Dict:
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


class LyricsStyle(Enum):
    MODERN = "modern"
    CLASSIC = "classic"
    MINIMAL = "minimal"
    GLASS = "glass"


STYLE_CONFIGS = {
    LyricsStyle.MODERN: {
        "bg_color": "#1a1a2e",
        "current_text_color": "#00d4ff",
        "other_text_color": "#6b7280",
        "highlight_color": "#00d4ff",
        "opacity": 0.9,
        "border_radius": 20,
        "font_family": "Microsoft YaHei",
        "show_controls": True,
        "show_background": True,
        "name": "现代"
    },
    LyricsStyle.CLASSIC: {
        "bg_color": "#000000",
        "current_text_color": "#ffcc00",
        "other_text_color": "#888888",
        "highlight_color": "#ffcc00",
        "opacity": 0.85,
        "border_radius": 0,
        "font_family": "SimHei",
        "show_controls": True,
        "show_background": True,
        "name": "经典"
    },
    LyricsStyle.MINIMAL: {
        "bg_color": "transparent",
        "current_text_color": "#ffffff",
        "other_text_color": "#aaaaaa",
        "highlight_color": "#3aafa9",
        "opacity": 1.0,
        "border_radius": 0,
        "font_family": "Microsoft YaHei",
        "show_controls": False,
        "show_background": False,
        "name": "极简"
    },
    LyricsStyle.GLASS: {
        "bg_color": "#2c2c2c",
        "current_text_color": "#e0e0e0",
        "other_text_color": "#666666",
        "highlight_color": "#3aafa9",
        "opacity": 0.7,
        "border_radius": 15,
        "font_family": "Microsoft YaHei",
        "show_controls": True,
        "show_background": True,
        "name": "玻璃"
    }
}


class MockMusicPlayer:
    def __init__(self):
        self._is_playing = False
        self._current_time = 0.0
        self._song_duration = 60.0
        self._playlist = [
            {"title": "夜曲", "artist": "周杰伦", "duration": 240},
            {"title": "稻香", "artist": "周杰伦", "duration": 223},
            {"title": "青花瓷", "artist": "周杰伦", "duration": 239},
        ]
        self._current_song_index = 0
        
        self._create_icons()
        
        self.control_bar = type('ControlBar', (), {
            'play_pause': self.play_pause
        })()
        
        self.lyrics_window = None
        self.lyrics_manager = LyricsManager()
        
        self._play_thread = None
        self._stop_flag = False

    def _create_icons(self):
        size = (30, 30)
        
        play_icon = Image.new("RGBA", size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(play_icon)
        draw.polygon([(8, 5), (8, 25), (25, 15)], fill="#ffffff")
        self.play_icon = ctk.CTkImage(play_icon, size=size)
        
        pause_icon = Image.new("RGBA", size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(pause_icon)
        draw.rectangle([(8, 5), (13, 25)], fill="#ffffff")
        draw.rectangle([(17, 5), (22, 25)], fill="#ffffff")
        self.pause_icon = ctk.CTkImage(pause_icon, size=size)
        
        prev_icon = Image.new("RGBA", size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(prev_icon)
        draw.polygon([(22, 5), (22, 25), (10, 15)], fill="#ffffff")
        draw.rectangle([(5, 5), (8, 25)], fill="#ffffff")
        self.prev_icon = ctk.CTkImage(prev_icon, size=size)
        
        next_icon = Image.new("RGBA", size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(next_icon)
        draw.polygon([(8, 5), (8, 25), (20, 15)], fill="#ffffff")
        draw.rectangle([(22, 5), (25, 25)], fill="#ffffff")
        self.next_icon = ctk.CTkImage(next_icon, size=size)

    class MockState:
        Playing = 1
        Paused = 2
        
    class MockMusicListPlayer:
        def __init__(self, outer):
            self.outer = outer
            
        def get_state(self):
            if self.outer._is_playing:
                return 1
            return 2
    
    class MockMusic:
        def __init__(self, outer):
            self.outer = outer
            
        def get_time(self):
            return int(self.outer._current_time * 1000)

    @property
    def music_list_player(self):
        return self.MockMusicListPlayer(self)
    
    @property
    def music(self):
        return self.MockMusic(self)

    def get_song_title(self):
        if 0 <= self._current_song_index < len(self._playlist):
            return self._playlist[self._current_song_index]["title"]
        return "未知歌曲"

    def get_song_artist(self):
        if 0 <= self._current_song_index < len(self._playlist):
            return self._playlist[self._current_song_index]["artist"]
        return "未知歌手"

    def play_pause(self, event=None):
        self._is_playing = not self._is_playing
        if self._is_playing:
            self._stop_flag = False
            self._play_thread = threading.Thread(target=self._simulate_playback, daemon=True)
            self._play_thread.start()
            logging.info(f"播放: {self.get_song_title()}")
        else:
            self._stop_flag = True
            logging.info(f"暂停: {self.get_song_title()}")

    def _simulate_playback(self):
        while self._is_playing and not self._stop_flag:
            time.sleep(0.1)
            self._current_time += 0.1
            if self._current_time >= self._song_duration:
                self._current_time = 0.0
                self.play_next_song()

    def play_next_song(self):
        self._current_song_index = (self._current_song_index + 1) % len(self._playlist)
        self._current_time = 0.0
        logging.info(f"切换到下一首: {self.get_song_title()}")
        
        if self.lyrics_window and self.lyrics_window.winfo_exists():
            self.lyrics_window.load_lyrics_for_current_song()

    def play_previous(self, event=None):
        self._current_song_index = (self._current_song_index - 1) % len(self._playlist)
        self._current_time = 0.0
        logging.info(f"切换到上一首: {self.get_song_title()}")
        
        if self.lyrics_window and self.lyrics_window.winfo_exists():
            self.lyrics_window.load_lyrics_for_current_song()


class LyricsWindow(ctk.CTkToplevel):
    def __init__(self, parent, music_player):
        super().__init__(parent)
        
        self.parent = parent
        self.music_player = music_player
        self.lyrics_manager = LyricsManager()
        
        self.is_locked = False
        self.current_style = LyricsStyle.MODERN
        self.font_size = 24
        self.is_visible = True
        self.current_lyric_index = -1
        self._drag_start_x = 0
        self._drag_start_y = 0
        self._window_start_x = 0
        self._window_start_y = 0
        self._is_dragging = False
        self._context_menu = None
        
        self.play_icon = music_player.play_icon
        self.pause_icon = music_player.pause_icon
        self.prev_icon = music_player.prev_icon
        self.next_icon = music_player.next_icon
        
        self._create_icons()
        self.setup_window()
        self.create_widgets()
        self.apply_style()
        self._setup_context_menu()
        self._update_window_size()
        
        self.load_lyrics_for_current_song()
        self.update_lyrics()

    def _create_icons(self):
        heart_size = (24, 24)
        
        heart_empty = Image.new("RGBA", heart_size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(heart_empty)
        
        heart_xy = [
            (12, 4), (16, 6), (18, 9), (19, 12),
            (18, 15), (16, 17), (12, 19), (8, 17),
            (6, 15), (5, 12), (6, 9), (8, 6)
        ]
        draw.polygon(heart_xy, outline="#888888", fill=None, width=2)
        self.heart_empty_icon = ctk.CTkImage(heart_empty, size=heart_size)
        
        heart_filled = Image.new("RGBA", heart_size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(heart_filled)
        draw.polygon(heart_xy, outline="#ff4d4d", fill="#ff4d4d")
        self.heart_filled_icon = ctk.CTkImage(heart_filled, size=heart_size)

    def setup_window(self):
        self.title("迷你歌词")
        self.overrideredirect(True)
        self.attributes("-topmost", True)
        self.attributes("-transparentcolor", "#010101")
        self.configure(fg_color="#010101")
        
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width - 700) // 2
        y = screen_height - 250
        self.geometry(f"700x200+{x}+{y}")
        
        self.bind("<Map>", lambda e: self.attributes("-topmost", True))

    def _update_window_size(self):
        config = STYLE_CONFIGS[self.current_style]
        if config["show_controls"]:
            header_height = 50
            controls_height = 50
        else:
            header_height = 0
            controls_height = 10
        
        lyrics_height = self.font_size * 3 + 40
        total_height = header_height + lyrics_height + controls_height + 20
        
        screen_width = self.winfo_screenwidth()
        width = min(900, int(screen_width * 0.7))
        
        current_geo = self.geometry()
        if '+' in current_geo:
            _, x, y = current_geo.split('+')
            self.geometry(f"{width}x{total_height}+{x}+{y}")
        else:
            self.geometry(f"{width}x{total_height}")

    def _setup_context_menu(self):
        self._context_menu = tk.Menu(self, tearoff=0, bg="#333333", fg="white", 
                                      activebackground="#555555", activeforeground="white",
                                      font=("Microsoft YaHei", 10))
        
        self._context_menu.add_command(label="▶ 播放/暂停", command=self.play_pause)
        self._context_menu.add_command(label="⏮ 上一首", command=self.play_previous)
        self._context_menu.add_command(label="⏭ 下一首", command=self.play_next)
        self._context_menu.add_separator()
        self._context_menu.add_command(label="♡ 收藏/取消收藏", command=self.toggle_favorite)
        self._context_menu.add_separator()
        
        style_menu = tk.Menu(self._context_menu, tearoff=0, bg="#333333", fg="white",
                             activebackground="#555555", activeforeground="white",
                             font=("Microsoft YaHei", 10))
        
        for style in LyricsStyle:
            config = STYLE_CONFIGS[style]
            style_menu.add_command(label=config["name"], 
                                   command=lambda s=style: self._set_style(s))
        
        self._context_menu.add_cascade(label="🎨 切换样式", menu=style_menu)
        self._context_menu.add_separator()
        
        self._context_menu.add_command(label="🔒 锁定窗口" if not self.is_locked else "🔓 解锁窗口", 
                                        command=self.toggle_lock)
        self._context_menu.add_separator()
        
        font_menu = tk.Menu(self._context_menu, tearoff=0, bg="#333333", fg="white",
                           activebackground="#555555", activeforeground="white",
                           font=("Microsoft YaHei", 10))
        
        for size in [16, 20, 24, 28, 32, 36, 40, 48]:
            font_menu.add_command(label=f"{size} 像素", 
                                  command=lambda s=size: self._set_font_size(s))
        
        self._context_menu.add_cascade(label="📏 字体大小", menu=font_menu)
        self._context_menu.add_separator()
        
        self._context_menu.add_command(label="👁 隐藏歌词", command=self.hide_window)
        self._context_menu.add_command(label="✕ 关闭窗口", command=self.destroy_lyrics_window)
        
        self.bind("<Button-3>", self._show_context_menu)
        self.main_frame.bind("<Button-3>", self._show_context_menu)
        self.lyrics_frame.bind("<Button-3>", self._show_context_menu)
        self.current_lyric_label.bind("<Button-3>", self._show_context_menu)
        self.prev_lyric_label.bind("<Button-3>", self._show_context_menu)
        self.next_lyric_label.bind("<Button-3>", self._show_context_menu)

    def _show_context_menu(self, event):
        try:
            self._context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self._context_menu.grab_release()

    def _set_style(self, style):
        self.current_style = style
        self.style_menu.set(STYLE_CONFIGS[style]["name"])
        self.apply_style()

    def _set_font_size(self, size):
        self.font_size = size
        self.size_slider.set(size)
        self.size_value.configure(text=str(size))
        self.apply_style()

    def create_widgets(self):
        self.main_frame = ctk.CTkFrame(self, corner_radius=20, fg_color="#1a1a2e")
        self.main_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        self.main_frame.bind("<Button-1>", self.start_drag)
        self.main_frame.bind("<B1-Motion>", self.do_drag)
        self.main_frame.bind("<ButtonRelease-1>", self.stop_drag)
        
        self.header_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.header_frame.pack(fill="x", padx=15, pady=(10, 0))
        
        self.style_label = ctk.CTkLabel(
            self.header_frame,
            text="样式:",
            font=("Microsoft YaHei", 11),
            text_color="#888888"
        )
        self.style_label.pack(side="left", padx=(0, 5))
        
        self.style_menu = ctk.CTkOptionMenu(
            self.header_frame,
            values=["现代", "经典", "极简", "玻璃"],
            command=self.on_style_change,
            width=90,
            height=28,
            font=("Microsoft YaHei", 11)
        )
        self.style_menu.pack(side="left", padx=5)
        
        self.size_label = ctk.CTkLabel(
            self.header_frame,
            text="字体:",
            font=("Microsoft YaHei", 11),
            text_color="#888888"
        )
        self.size_label.pack(side="left", padx=(15, 5))
        
        self.size_slider = ctk.CTkSlider(
            self.header_frame,
            from_=16,
            to=56,
            command=self.on_size_change,
            width=120,
            height=16
        )
        self.size_slider.set(self.font_size)
        self.size_slider.pack(side="left", padx=5)
        
        self.size_value = ctk.CTkLabel(
            self.header_frame,
            text=f"{self.font_size}",
            font=("Microsoft YaHei", 11),
            text_color="#888888",
            width=35
        )
        self.size_value.pack(side="left", padx=2)
        
        self.lock_btn = ctk.CTkButton(
            self.header_frame,
            text="🔒 锁定",
            command=self.toggle_lock,
            width=70,
            height=28,
            font=("Microsoft YaHei", 11)
        )
        self.lock_btn.pack(side="left", padx=15)
        
        self.close_btn = ctk.CTkButton(
            self.header_frame,
            text="✕ 关闭",
            command=self.destroy_lyrics_window,
            width=60,
            height=28,
            font=("Microsoft YaHei", 11),
            fg_color="#553333",
            hover_color="#774444"
        )
        self.close_btn.pack(side="left", padx=5)
        
        self.minimal_close_btn = ctk.CTkButton(
            self.main_frame,
            text="✕",
            command=self.destroy_lyrics_window,
            width=30,
            height=30,
            font=("Microsoft YaHei", 14),
            fg_color="transparent",
            hover_color="#333333",
            text_color="#ff6666",
            corner_radius=15
        )
        
        self.lyrics_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.lyrics_frame.pack(fill="both", expand=True, padx=30, pady=10)
        
        self.prev_lyric_label = ctk.CTkLabel(
            self.lyrics_frame,
            text="",
            font=("Microsoft YaHei", max(14, self.font_size - 10)),
            text_color="#6b7280",
            anchor="center"
        )
        self.prev_lyric_label.pack(fill="x", pady=3)
        
        self.current_lyric_label = ctk.CTkLabel(
            self.lyrics_frame,
            text="暂无歌词",
            font=("Microsoft YaHei", self.font_size, "bold"),
            text_color="#00d4ff",
            anchor="center"
        )
        self.current_lyric_label.pack(fill="x", pady=5)
        
        self.next_lyric_label = ctk.CTkLabel(
            self.lyrics_frame,
            text="",
            font=("Microsoft YaHei", max(14, self.font_size - 10)),
            text_color="#6b7280",
            anchor="center"
        )
        self.next_lyric_label.pack(fill="x", pady=3)
        
        self.controls_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.controls_frame.pack(fill="x", padx=20, pady=(0, 10))
        
        self.favorite_btn = ctk.CTkButton(
            self.controls_frame,
            text="",
            image=self.heart_empty_icon,
            command=self.toggle_favorite,
            width=45,
            height=35,
            fg_color="transparent",
            hover_color="#333333"
        )
        self.favorite_btn.pack(side="left", padx=8)
        
        self.prev_btn = ctk.CTkButton(
            self.controls_frame,
            text="",
            image=self.prev_icon,
            command=self.play_previous,
            width=45,
            height=35,
            fg_color="transparent",
            hover_color="#333333"
        )
        self.prev_btn.pack(side="left", padx=8)
        
        self.play_pause_btn = ctk.CTkButton(
            self.controls_frame,
            text="",
            image=self.play_icon,
            command=self.play_pause,
            width=55,
            height=35,
            fg_color="transparent",
            hover_color="#333333"
        )
        self.play_pause_btn.pack(side="left", padx=8)
        
        self.next_btn = ctk.CTkButton(
            self.controls_frame,
            text="",
            image=self.next_icon,
            command=self.play_next,
            width=45,
            height=35,
            fg_color="transparent",
            hover_color="#333333"
        )
        self.next_btn.pack(side="left", padx=8)
        
        self.song_info_label = ctk.CTkLabel(
            self.controls_frame,
            text="",
            font=("Microsoft YaHei", 11),
            text_color="#888888",
            anchor="e"
        )
        self.song_info_label.pack(side="right", padx=10, expand=True)
        
        for widget in [self.main_frame, self.prev_lyric_label, self.current_lyric_label, 
                       self.next_lyric_label, self.lyrics_frame, self.song_info_label]:
            widget.bind("<Button-1>", self.start_drag)
            widget.bind("<B1-Motion>", self.do_drag)
            widget.bind("<ButtonRelease-1>", self.stop_drag)

    def apply_style(self):
        config = STYLE_CONFIGS[self.current_style]
        
        if config["show_background"]:
            self.main_frame.configure(fg_color=config["bg_color"])
            self.attributes("-alpha", config["opacity"])
        else:
            self.main_frame.configure(fg_color="#010101")
            self.attributes("-alpha", 1.0)
        
        self.main_frame.configure(corner_radius=config["border_radius"])
        
        current_font_size = self.font_size
        other_font_size = max(14, current_font_size - 10)
        
        self.current_lyric_label.configure(
            text_color=config["current_text_color"],
            font=(config["font_family"], current_font_size, "bold")
        )
        self.prev_lyric_label.configure(
            text_color=config["other_text_color"],
            font=(config["font_family"], other_font_size)
        )
        self.next_lyric_label.configure(
            text_color=config["other_text_color"],
            font=(config["font_family"], other_font_size)
        )
        
        if config["show_controls"]:
            self.header_frame.pack(fill="x", padx=15, pady=(10, 0), before=self.lyrics_frame)
            self.controls_frame.pack(fill="x", padx=20, pady=(0, 10), after=self.lyrics_frame)
            self.minimal_close_btn.pack_forget()
        else:
            self.header_frame.pack_forget()
            self.controls_frame.pack_forget()
            self.minimal_close_btn.pack(side="top", anchor="ne", padx=10, pady=5)
        
        self._update_window_size()

    def on_style_change(self, choice):
        style_map = {
            "现代": LyricsStyle.MODERN,
            "经典": LyricsStyle.CLASSIC,
            "极简": LyricsStyle.MINIMAL,
            "玻璃": LyricsStyle.GLASS
        }
        self.current_style = style_map.get(choice, LyricsStyle.MODERN)
        self.apply_style()

    def on_size_change(self, value):
        self.font_size = int(value)
        self.size_value.configure(text=str(self.font_size))
        self.apply_style()

    def toggle_lock(self):
        self.is_locked = not self.is_locked
        if self.is_locked:
            self.lock_btn.configure(text="🔓 解锁")
            self.attributes("-topmost", True)
            logging.info("窗口已锁定")
        else:
            self.lock_btn.configure(text="🔒 锁定")
            logging.info("窗口已解锁")

    def hide_window(self):
        self.withdraw()
        self.is_visible = False
        logging.info("歌词窗口已隐藏")

    def show_window(self):
        self.deiconify()
        self.is_visible = True
        self.attributes("-topmost", True)
        logging.info("歌词窗口已显示")

    def destroy_lyrics_window(self):
        self.destroy()
        self.is_visible = False
        if hasattr(self.music_player, 'lyrics_window'):
            self.music_player.lyrics_window = None
        logging.info("歌词窗口已关闭")

    def start_drag(self, event):
        if self.is_locked:
            return
        
        self._drag_start_x = event.x_root
        self._drag_start_y = event.y_root
        
        self._window_start_x = self.winfo_x()
        self._window_start_y = self.winfo_y()
        
        self._is_dragging = True

    def do_drag(self, event):
        if self.is_locked or not self._is_dragging:
            return
        
        delta_x = event.x_root - self._drag_start_x
        delta_y = event.y_root - self._drag_start_y
        
        new_x = self._window_start_x + delta_x
        new_y = self._window_start_y + delta_y
        
        self.geometry(f"+{new_x}+{new_y}")

    def stop_drag(self, event):
        self._is_dragging = False

    def play_previous(self):
        self.music_player.play_previous()
        self.update_play_button()

    def play_next(self):
        self.music_player.play_next_song()
        self.update_play_button()

    def play_pause(self):
        self.music_player.control_bar.play_pause()
        self.update_play_button()

    def update_play_button(self):
        try:
            if self.music_player._is_playing:
                self.play_pause_btn.configure(image=self.pause_icon)
            else:
                self.play_pause_btn.configure(image=self.play_icon)
        except Exception:
            pass

    def toggle_favorite(self):
        try:
            song_title = self.music_player.get_song_title()
            
            if not song_title:
                song_title = "当前歌曲"
            
            is_fav = self.lyrics_manager.toggle_favorite(song_title)
            self.update_favorite_button(is_fav)
            
            status = "已收藏" if is_fav else "已取消收藏"
            logging.info(f"歌曲 '{song_title}' {status}")
        except Exception as e:
            logging.exception(e)

    def update_favorite_button(self, is_favorite):
        if is_favorite:
            self.favorite_btn.configure(image=self.heart_filled_icon)
        else:
            self.favorite_btn.configure(image=self.heart_empty_icon)

    def load_lyrics_for_current_song(self):
        try:
            test_lrc = """[ti:测试歌曲]
[ar:测试歌手]
[al:测试专辑]

[00:00.00]欢迎使用迷你桌面歌词
[00:03.50]这是一个功能丰富的歌词显示
[00:07.00]支持四种样式选择
[00:10.50]现代、经典、极简、玻璃
[00:14.00]可以调整字体大小
[00:17.50]可以锁定窗口防误触
[00:21.00]包含播放控制按钮
[00:24.50]以及收藏功能
[00:28.00]拖动窗口可以移动位置
[00:31.50]点击锁定按钮防止误操作
[00:35.00]右键菜单有更多功能
[00:38.50]祝您使用愉快
[00:42.00]感谢使用迷你桌面歌词
"""
            
            success = self.lyrics_manager.parser.parse_lrc_content(test_lrc)
            
            if not success:
                self.current_lyric_label.configure(text="暂无歌词")
                self.prev_lyric_label.configure(text="")
                self.next_lyric_label.configure(text="")
            
            song_title = self.music_player.get_song_title()
            if song_title:
                is_fav = self.lyrics_manager.is_favorite(song_title)
                self.update_favorite_button(is_fav)
            
            artist = self.music_player.get_song_artist()
            self.song_info_label.configure(text=f"{song_title} - {artist}")
            
            logging.info(f"已加载歌词: {song_title}")
        except Exception as e:
            logging.exception(e)
            self.current_lyric_label.configure(text="暂无歌词")

    def update_lyrics(self):
        try:
            if self.lyrics_manager.has_lyrics():
                current_time = self.music_player._current_time
                
                surrounding = self.lyrics_manager.get_surrounding_lyrics(current_time, count=1)
                
                current_text = surrounding.get('current', '')
                prev_texts = surrounding.get('previous', [])
                next_texts = surrounding.get('next', [])
                
                if current_text:
                    self.current_lyric_label.configure(text=current_text)
                
                if prev_texts:
                    self.prev_lyric_label.configure(text=prev_texts[-1])
                else:
                    self.prev_lyric_label.configure(text="")
                
                if next_texts:
                    self.next_lyric_label.configure(text=next_texts[0])
                else:
                    self.next_lyric_label.configure(text="")
            
            self.update_play_button()
        except Exception:
            pass
        
        try:
            self.after(100, self.update_lyrics)
        except Exception:
            pass


class LyricsTestApp:
    def __init__(self):
        ctk.set_appearance_mode("dark")
        
        self.root = ctk.CTk()
        self.root.title("音乐播放器 - 歌词测试")
        self.root.geometry("600x400")
        
        self.music_player = MockMusicPlayer()
        self.lyrics_window = None
        
        self.create_widgets()
        
        logging.info("歌词测试应用已启动")

    def create_widgets(self):
        title_label = ctk.CTkLabel(
            self.root,
            text="🎵 迷你桌面歌词测试",
            font=("Microsoft YaHei", 24, "bold")
        )
        title_label.pack(pady=20)
        
        info_frame = ctk.CTkFrame(self.root, fg_color="#2a2a2a")
        info_frame.pack(fill="x", padx=30, pady=10)
        
        self.song_title_label = ctk.CTkLabel(
            info_frame,
            text=f"当前歌曲: {self.music_player.get_song_title()}",
            font=("Microsoft YaHei", 14),
            text_color="#00d4ff"
        )
        self.song_title_label.pack(pady=10)
        
        self.artist_label = ctk.CTkLabel(
            info_frame,
            text=f"歌手: {self.music_player.get_song_artist()}",
            font=("Microsoft YaHei", 12),
            text_color="#888888"
        )
        self.artist_label.pack(pady=(0, 10))
        
        control_frame = ctk.CTkFrame(self.root, fg_color="transparent")
        control_frame.pack(pady=20)
        
        self.lyrics_btn = ctk.CTkButton(
            control_frame,
            text="📝 打开歌词窗口",
            command=self.toggle_lyrics,
            width=200,
            height=50,
            font=("Microsoft YaHei", 16)
        )
        self.lyrics_btn.pack(side="left", padx=10)
        
        self.play_btn = ctk.CTkButton(
            control_frame,
            text="▶ 播放/暂停",
            command=self.play_pause,
            width=120,
            height=50,
            font=("Microsoft YaHei", 14)
        )
        self.play_btn.pack(side="left", padx=10)
        
        nav_frame = ctk.CTkFrame(self.root, fg_color="transparent")
        nav_frame.pack(pady=10)
        
        prev_btn = ctk.CTkButton(
            nav_frame,
            text="⏮ 上一首",
            command=self.prev_song,
            width=100,
            height=40,
            font=("Microsoft YaHei", 12)
        )
        prev_btn.pack(side="left", padx=10)
        
        next_btn = ctk.CTkButton(
            nav_frame,
            text="⏭ 下一首",
            command=self.next_song,
            width=100,
            height=40,
            font=("Microsoft YaHei", 12)
        )
        next_btn.pack(side="left", padx=10)
        
        fav_btn = ctk.CTkButton(
            nav_frame,
            text="♡ 收藏",
            command=self.toggle_favorite,
            width=100,
            height=40,
            font=("Microsoft YaHei", 12)
        )
        fav_btn.pack(side="left", padx=10)
        
        features_text = """功能说明:

1. 📝 点击"打开歌词窗口"显示迷你歌词
2. ▶ 播放后歌词会自动同步滚动
3. 🎨 支持4种样式: 现代/经典/极简/玻璃
4. 📏 可调节字体大小 (16-56像素)
5. 🔒 锁定窗口防止误触
6. ♡ 心形按钮收藏歌曲
7. 🖱 右键菜单更多功能

注意: 极简模式下可通过右键菜单或右上角按钮关闭
"""
        features_label = ctk.CTkLabel(
            self.root,
            text=features_text,
            font=("Microsoft YaHei", 11),
            text_color="#888888",
            justify="left"
        )
        features_label.pack(pady=20, padx=30, anchor="w")

    def toggle_lyrics(self):
        if self.lyrics_window and self.lyrics_window.winfo_exists():
            if self.lyrics_window.is_visible:
                self.lyrics_window.hide_window()
                self.lyrics_btn.configure(text="📝 打开歌词窗口")
            else:
                self.lyrics_window.show_window()
                self.lyrics_btn.configure(text="📝 关闭歌词窗口")
        else:
            self.lyrics_window = LyricsWindow(self.root, self.music_player)
            self.music_player.lyrics_window = self.lyrics_window
            self.lyrics_btn.configure(text="📝 关闭歌词窗口")

    def play_pause(self):
        self.music_player.play_pause()
        if self.music_player._is_playing:
            self.play_btn.configure(text="⏸ 暂停")
        else:
            self.play_btn.configure(text="▶ 播放")

    def prev_song(self):
        self.music_player.play_previous()
        self._update_song_info()

    def next_song(self):
        self.music_player.play_next_song()
        self._update_song_info()

    def toggle_favorite(self):
        song_title = self.music_player.get_song_title()
        is_fav = self.music_player.lyrics_manager.toggle_favorite(song_title)
        status = "已收藏" if is_fav else "已取消收藏"
        logging.info(f"歌曲 '{song_title}' {status}")

    def _update_song_info(self):
        self.song_title_label.configure(
            text=f"当前歌曲: {self.music_player.get_song_title()}"
        )
        self.artist_label.configure(
            text=f"歌手: {self.music_player.get_song_artist()}"
        )

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    app = LyricsTestApp()
    app.run()
