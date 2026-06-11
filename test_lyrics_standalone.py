"""测试迷你桌面歌词功能 - 独立版本"""

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

logging.basicConfig(level=logging.DEBUG)


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
        "shadow_color": "#000000",
        "opacity": 0.9,
        "border_radius": 20,
        "font_family": "Microsoft YaHei",
        "show_controls": True,
        "show_background": True,
    },
    LyricsStyle.CLASSIC: {
        "bg_color": "#000000",
        "current_text_color": "#ffcc00",
        "other_text_color": "#888888",
        "highlight_color": "#ffcc00",
        "shadow_color": "#000000",
        "opacity": 0.85,
        "border_radius": 0,
        "font_family": "SimHei",
        "show_controls": True,
        "show_background": True,
    },
    LyricsStyle.MINIMAL: {
        "bg_color": "transparent",
        "current_text_color": "#ffffff",
        "other_text_color": "#aaaaaa",
        "highlight_color": "#3aafa9",
        "shadow_color": "#000000",
        "opacity": 1.0,
        "border_radius": 0,
        "font_family": "Microsoft YaHei",
        "show_controls": False,
        "show_background": False,
    },
    LyricsStyle.GLASS: {
        "bg_color": "#2c2c2c",
        "current_text_color": "#e0e0e0",
        "other_text_color": "#666666",
        "highlight_color": "#3aafa9",
        "shadow_color": "#000000",
        "opacity": 0.7,
        "border_radius": 15,
        "font_family": "Microsoft YaHei",
        "show_controls": True,
        "show_background": True,
    }
}


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
        self._offset_x = 0
        self._offset_y = 0
        self._is_dragging = False
        
        self.play_icon = music_player.play_icon
        self.pause_icon = music_player.pause_icon
        self.prev_icon = music_player.prev_icon
        self.next_icon = music_player.next_icon
        
        self._create_heart_icons()
        self.setup_window()
        self.create_widgets()
        self.apply_style()

    def _create_heart_icons(self):
        heart_size = (20, 20)
        
        heart_empty = Image.new("RGBA", heart_size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(heart_empty)
        
        heart_xy = [
            (10, 3), (14, 5), (16, 8), (17, 11),
            (16, 14), (14, 16), (10, 18), (6, 16),
            (4, 14), (3, 11), (4, 8), (6, 5)
        ]
        draw.polygon(heart_xy, outline="#888888", fill=None, width=2)
        self.heart_empty_icon = ctk.CTkImage(heart_empty, size=heart_size)
        
        heart_filled = Image.new("RGBA", heart_size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(heart_filled)
        draw.polygon(heart_xy, outline="#ff4d4d", fill="#ff4d4d")
        self.heart_filled_icon = ctk.CTkImage(heart_filled, size=heart_size)

    def setup_window(self):
        self.title("迷你歌词")
        self.geometry("600x150")
        self.overrideredirect(True)
        self.attributes("-topmost", True)
        self.attributes("-transparentcolor", "#010101")
        self.configure(fg_color="#010101")
        
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width - 600) // 2
        y = screen_height - 200
        self.geometry(f"+{x}+{y}")

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
            font=("Microsoft YaHei", 10),
            text_color="#888888"
        )
        self.style_label.pack(side="left", padx=(0, 5))
        
        self.style_menu = ctk.CTkOptionMenu(
            self.header_frame,
            values=["现代", "经典", "极简", "玻璃"],
            command=self.on_style_change,
            width=80,
            height=25,
            font=("Microsoft YaHei", 10)
        )
        self.style_menu.pack(side="left", padx=5)
        
        self.size_label = ctk.CTkLabel(
            self.header_frame,
            text="字体:",
            font=("Microsoft YaHei", 10),
            text_color="#888888"
        )
        self.size_label.pack(side="left", padx=(10, 5))
        
        self.size_slider = ctk.CTkSlider(
            self.header_frame,
            from_=16,
            to=48,
            command=self.on_size_change,
            width=100,
            height=15
        )
        self.size_slider.set(self.font_size)
        self.size_slider.pack(side="left", padx=5)
        
        self.size_value = ctk.CTkLabel(
            self.header_frame,
            text=f"{self.font_size}",
            font=("Microsoft YaHei", 10),
            text_color="#888888",
            width=30
        )
        self.size_value.pack(side="left", padx=2)
        
        self.lock_btn = ctk.CTkButton(
            self.header_frame,
            text="锁定",
            command=self.toggle_lock,
            width=50,
            height=25,
            font=("Microsoft YaHei", 10)
        )
        self.lock_btn.pack(side="left", padx=10)
        
        self.hide_btn = ctk.CTkButton(
            self.header_frame,
            text="隐藏",
            command=self.hide_window,
            width=50,
            height=25,
            font=("Microsoft YaHei", 10)
        )
        self.hide_btn.pack(side="left", padx=5)
        
        self.lyrics_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.lyrics_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        self.prev_lyric_label = ctk.CTkLabel(
            self.lyrics_frame,
            text="",
            font=("Microsoft YaHei", 16),
            text_color="#6b7280",
            anchor="center"
        )
        self.prev_lyric_label.pack(fill="x", pady=2)
        
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
            font=("Microsoft YaHei", 16),
            text_color="#6b7280",
            anchor="center"
        )
        self.next_lyric_label.pack(fill="x", pady=2)
        
        self.controls_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.controls_frame.pack(fill="x", padx=20, pady=(0, 10))
        
        self.favorite_btn = ctk.CTkButton(
            self.controls_frame,
            text="",
            image=self.heart_empty_icon,
            command=self.toggle_favorite,
            width=40,
            height=30,
            fg_color="transparent",
            hover_color="#333333"
        )
        self.favorite_btn.pack(side="left", padx=5)
        
        self.prev_btn = ctk.CTkButton(
            self.controls_frame,
            text="",
            image=self.prev_icon,
            command=self.play_previous,
            width=40,
            height=30,
            fg_color="transparent",
            hover_color="#333333"
        )
        self.prev_btn.pack(side="left", padx=5)
        
        self.play_pause_btn = ctk.CTkButton(
            self.controls_frame,
            text="",
            image=self.play_icon,
            command=self.play_pause,
            width=50,
            height=30,
            fg_color="transparent",
            hover_color="#333333"
        )
        self.play_pause_btn.pack(side="left", padx=5)
        
        self.next_btn = ctk.CTkButton(
            self.controls_frame,
            text="",
            image=self.next_icon,
            command=self.play_next,
            width=40,
            height=30,
            fg_color="transparent",
            hover_color="#333333"
        )
        self.next_btn.pack(side="left", padx=5)
        
        self.song_info_label = ctk.CTkLabel(
            self.controls_frame,
            text="",
            font=("Microsoft YaHei", 10),
            text_color="#888888",
            anchor="e"
        )
        self.song_info_label.pack(side="right", padx=5)
        
        for widget in [self.main_frame, self.prev_lyric_label, self.current_lyric_label, 
                       self.next_lyric_label, self.lyrics_frame]:
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
        
        self.current_lyric_label.configure(
            text_color=config["current_text_color"],
            font=(config["font_family"], self.font_size, "bold")
        )
        self.prev_lyric_label.configure(
            text_color=config["other_text_color"],
            font=(config["font_family"], max(12, self.font_size - 8))
        )
        self.next_lyric_label.configure(
            text_color=config["other_text_color"],
            font=(config["font_family"], max(12, self.font_size - 8))
        )
        
        if config["show_controls"]:
            self.header_frame.pack(fill="x", padx=15, pady=(10, 0))
            self.controls_frame.pack(fill="x", padx=20, pady=(0, 10))
        else:
            self.header_frame.pack_forget()
            self.controls_frame.pack_forget()

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
            self.lock_btn.configure(text="解锁")
            self.attributes("-topmost", True)
        else:
            self.lock_btn.configure(text="锁定")

    def hide_window(self):
        self.withdraw()
        self.is_visible = False

    def show_window(self):
        self.deiconify()
        self.is_visible = True

    def start_drag(self, event):
        if self.is_locked:
            return
        self._is_dragging = True
        self._offset_x = event.x
        self._offset_y = event.y

    def do_drag(self, event):
        if self.is_locked or not self._is_dragging:
            return
        x = self.winfo_pointerx() - self._offset_x
        y = self.winfo_pointery() - self._offset_y
        self.geometry(f"+{x}+{y}")

    def stop_drag(self, event):
        self._is_dragging = False

    def play_previous(self):
        print("播放上一首")
        self.music_player.play_previous()

    def play_next(self):
        print("播放下一首")
        self.music_player.play_next_song()

    def play_pause(self):
        print("播放/暂停")
        self.update_play_button()

    def update_play_button(self):
        if self.play_pause_btn.cget("image") == str(self.play_icon):
            self.play_pause_btn.configure(image=self.pause_icon)
        else:
            self.play_pause_btn.configure(image=self.play_icon)

    def toggle_favorite(self):
        song_title = self.music_player.get_song_title()
        if song_title:
            is_fav = self.lyrics_manager.toggle_favorite(song_title)
            self.update_favorite_button(is_fav)
            print(f"收藏状态: {'已收藏' if is_fav else '已取消收藏'}")

    def update_favorite_button(self, is_favorite):
        if is_favorite:
            self.favorite_btn.configure(image=self.heart_filled_icon)
        else:
            self.favorite_btn.configure(image=self.heart_empty_icon)


class MockMusicPlayer:
    def __init__(self):
        self.lyrics_manager = LyricsManager()
        self.current_time = 0
        
        self._create_icons()
        
    def _create_icons(self):
        size = (30, 30)
        
        play_icon = Image.new("RGBA", size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(play_icon)
        draw.polygon([(5, 5), (5, 25), (25, 15)], fill="#ffffff")
        self.play_icon = ctk.CTkImage(play_icon, size=size)
        
        pause_icon = Image.new("RGBA", size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(pause_icon)
        draw.rectangle([(5, 5), (12, 25)], fill="#ffffff")
        draw.rectangle([(18, 5), (25, 25)], fill="#ffffff")
        self.pause_icon = ctk.CTkImage(pause_icon, size=size)
        
        prev_icon = Image.new("RGBA", size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(prev_icon)
        draw.polygon([(25, 5), (25, 25), (10, 15)], fill="#ffffff")
        draw.rectangle([(3, 5), (8, 25)], fill="#ffffff")
        self.prev_icon = ctk.CTkImage(prev_icon, size=size)
        
        next_icon = Image.new("RGBA", size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(next_icon)
        draw.polygon([(5, 5), (5, 25), (20, 15)], fill="#ffffff")
        draw.rectangle([(22, 5), (27, 25)], fill="#ffffff")
        self.next_icon = ctk.CTkImage(next_icon, size=size)
        
    def get_song_title(self):
        return "测试歌曲"
    
    def get_song_artist(self):
        return "测试歌手"
    
    def play_previous(self):
        print("播放上一首")
        
    def play_next_song(self):
        print("播放下一首")


def create_test_lrc():
    test_lrc = """[ti:测试歌曲]
[ar:测试歌手]
[al:测试专辑]

[00:00.00]第一句歌词
[00:03.00]第二句歌词
[00:06.00]第三句歌词
[00:09.00]第四句歌词
[00:12.00]第五句歌词
[00:15.00]第六句歌词
[00:18.00]第七句歌词
[00:21.00]第八句歌词
"""
    with open("test_song.lrc", "w", encoding="utf-8") as f:
        f.write(test_lrc)
    return "test_song.lrc"


def test_lyrics_parser():
    print("=" * 60)
    print("测试歌词解析器")
    print("=" * 60)
    
    lrc_path = create_test_lrc()
    parser = LyricsParser()
    
    if parser.parse_lrc_file(lrc_path):
        print(f"歌曲标题: {parser.title}")
        print(f"歌手: {parser.artist}")
        print(f"专辑: {parser.album}")
        print(f"歌词行数: {len(parser.lyrics)}")
        print()
        
        for lyric in parser.lyrics:
            print(f"[{lyric.time:.2f}s] {lyric.text}")
            
        print("\n测试时间查找:")
        test_times = [0, 2, 5, 8, 15, 25]
        for t in test_times:
            text, idx = parser.get_lyric_at_time(t)
            print(f"  时间 {t}s -> 索引 {idx}: {text}")
    else:
        print("解析失败")
        
    print()


def test_lyrics_window():
    print("=" * 60)
    print("测试歌词窗口")
    print("=" * 60)
    
    ctk.set_appearance_mode("dark")
    
    root = ctk.CTk()
    root.title("音乐播放器测试")
    root.geometry("500x300")
    
    mock_player = MockMusicPlayer()
    
    lyrics_window = None
    
    def toggle_lyrics():
        nonlocal lyrics_window
        if lyrics_window and lyrics_window.winfo_exists():
            if lyrics_window.is_visible:
                lyrics_window.hide_window()
            else:
                lyrics_window.show_window()
        else:
            lyrics_window = LyricsWindow(root, mock_player)
            
            lrc_path = create_test_lrc()
            lyrics_window.lyrics_manager.parser.parse_lrc_file(lrc_path)
            
            lyrics_window.current_lyric_label.configure(text="第一句歌词")
            lyrics_window.prev_lyric_label.configure(text="")
            lyrics_window.next_lyric_label.configure(text="第二句歌词")
            lyrics_window.song_info_label.configure(text="测试歌曲 - 测试歌手")
    
    btn = ctk.CTkButton(
        root,
        text="打开迷你歌词窗口",
        command=toggle_lyrics,
        font=("Microsoft YaHei", 16),
        height=60
    )
    btn.pack(expand=True, padx=30, pady=20)
    
    info_text = """功能说明:

1. 样式切换: 4种样式可选
   - 现代: 深色背景,高亮文字
   - 经典: 黑色背景,黄色文字
   - 极简: 透明背景,仅显示歌词
   - 玻璃: 半透明背景,简洁风格

2. 字体调整: 滑块调节 16-48 像素

3. 锁定功能: 防止误触,锁定后无法拖动

4. 控制按钮:
   - 收藏: 心形按钮
   - 上一首/下一首
   - 播放/暂停"""
    
    info_label = ctk.CTkLabel(
        root,
        text=info_text,
        font=("Microsoft YaHei", 11),
        justify="left"
    )
    info_label.pack(pady=10, padx=20)
    
    print("\n歌词窗口已准备就绪！")
    print("点击按钮可以打开迷你歌词窗口")
    print()
    print("功能说明:")
    print("1. 样式下拉菜单: 现代/经典/极简/玻璃")
    print("2. 字体滑块: 16-48 像素可调")
    print("3. 锁定按钮: 防止误触，锁定后无法拖动")
    print("4. 隐藏按钮: 隐藏歌词窗口")
    print("5. 底部控制: 收藏、上一首、播放/暂停、下一首")
    print("=" * 60)
    
    root.mainloop()


if __name__ == "__main__":
    test_lyrics_parser()
    test_lyrics_window()
