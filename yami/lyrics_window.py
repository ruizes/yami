"""Mini Desktop Lyrics Window"""

import tkinter as tk
import customtkinter as ctk
import logging
from typing import Optional, Callable
from enum import Enum
from PIL import Image, ImageTk

from .lyrics import LyricsManager


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
        
        self.update_lyrics()

    def _create_heart_icons(self):
        heart_size = (20, 20)
        
        heart_empty = Image.new("RGBA", heart_size, (0, 0, 0, 0))
        from PIL import ImageDraw
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
        self.music_player.play_previous()

    def play_next(self):
        self.music_player.play_next_song()

    def play_pause(self):
        self.music_player.control_bar.play_pause()
        self.update_play_button()

    def update_play_button(self):
        import vlc
        if self.music_player.music_list_player.get_state() == vlc.State.Playing:
            self.play_pause_btn.configure(image=self.pause_icon)
        else:
            self.play_pause_btn.configure(image=self.play_icon)

    def toggle_favorite(self):
        song_title = self.music_player.get_song_title()
        if song_title:
            is_fav = self.lyrics_manager.toggle_favorite(song_title)
            self.update_favorite_button(is_fav)

    def update_favorite_button(self, is_favorite):
        if is_favorite:
            self.favorite_btn.configure(image=self.heart_filled_icon)
        else:
            self.favorite_btn.configure(image=self.heart_empty_icon)

    def load_lyrics_for_current_song(self):
        try:
            media = self.music_player.music_list_player.get_media_player().get_media()
            if media:
                media.parse()
                song_path = media.get_meta(15)
                if song_path:
                    from pathlib import Path
                    if song_path.startswith("file://"):
                        song_path = song_path[7:]
                    success = self.lyrics_manager.load_lyrics_for_song(song_path)
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
        except Exception as e:
            logging.exception(e)
            self.current_lyric_label.configure(text="暂无歌词")

    def update_lyrics(self):
        import vlc
        try:
            if self.music_player.music_list_player.get_state() == vlc.State.Playing:
                current_time = self.music_player.music.get_time() / 1000
                
                if self.lyrics_manager.has_lyrics():
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
                
        except Exception as e:
            logging.exception(e)
        
        self.after(100, self.update_lyrics)
