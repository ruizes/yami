"""Mini Desktop Lyrics Window"""

import tkinter as tk
import customtkinter as ctk
import logging
from typing import Optional
from enum import Enum
from PIL import Image, ImageDraw

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
        "opacity": 1.0,
        "border_radius": 0,
        "font_family": "Microsoft YaHei",
        "show_controls": False,
        "show_background": False,
        "show_minimal_controls": True,
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
        
        close_size = (20, 20)
        close_icon = Image.new("RGBA", close_size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(close_icon)
        draw.line([(5, 5), (15, 15)], fill="#ffffff", width=2)
        draw.line([(15, 5), (5, 15)], fill="#ffffff", width=2)
        self.close_icon = ctk.CTkImage(close_icon, size=close_size)

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
        width = min(800, int(screen_width * 0.6))
        
        current_geo = self.geometry()
        if '+' in current_geo:
            _, x, y = current_geo.split('+')
            self.geometry(f"{width}x{total_height}+{x}+{y}")
        else:
            self.geometry(f"{width}x{total_height}")

    def _setup_context_menu(self):
        self._context_menu = tk.Menu(self, tearoff=0, bg="#333333", fg="white", 
                                      activebackground="#555555", activeforeground="white")
        
        self._context_menu.add_command(label="播放/暂停", command=self.play_pause)
        self._context_menu.add_command(label="上一首", command=self.play_previous)
        self._context_menu.add_command(label="下一首", command=self.play_next)
        self._context_menu.add_separator()
        self._context_menu.add_command(label="收藏/取消收藏", command=self.toggle_favorite)
        self._context_menu.add_separator()
        self._context_menu.add_command(label="样式: 现代", command=lambda: self._set_style_from_menu("现代"))
        self._context_menu.add_command(label="样式: 经典", command=lambda: self._set_style_from_menu("经典"))
        self._context_menu.add_command(label="样式: 极简", command=lambda: self._set_style_from_menu("极简"))
        self._context_menu.add_command(label="样式: 玻璃", command=lambda: self._set_style_from_menu("玻璃"))
        self._context_menu.add_separator()
        self._context_menu.add_command(label="锁定窗口" if not self.is_locked else "解锁窗口", 
                                        command=self.toggle_lock)
        self._context_menu.add_separator()
        self._context_menu.add_command(label="隐藏歌词", command=self.hide_window)
        self._context_menu.add_command(label="关闭歌词窗口", command=self.destroy_lyrics_window)
        
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

    def _set_style_from_menu(self, style_name):
        self.on_style_change(style_name)

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
        
        self.header_frame.grid_columnconfigure(6, weight=1)
        
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
        
        self.minimal_controls_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        
        self.minimal_style_menu = ctk.CTkOptionMenu(
            self.minimal_controls_frame,
            values=["现代", "经典", "极简", "玻璃"],
            command=self.on_style_change,
            width=70,
            height=26,
            font=("Microsoft YaHei", 10),
            fg_color="#222222",
            button_color="#333333",
            button_hover_color="#444444",
            dropdown_fg_color="#222222"
        )
        self.minimal_style_menu.pack(side="left", padx=3)
        
        self.minimal_font_menu = ctk.CTkOptionMenu(
            self.minimal_controls_frame,
            values=["16", "20", "24", "28", "32", "36", "40", "48"],
            command=self._on_minimal_font_change,
            width=50,
            height=26,
            font=("Microsoft YaHei", 10),
            fg_color="#222222",
            button_color="#333333",
            button_hover_color="#444444",
            dropdown_fg_color="#222222"
        )
        self.minimal_font_menu.pack(side="left", padx=3)
        
        self.minimal_lock_btn = ctk.CTkButton(
            self.minimal_controls_frame,
            text="🔒",
            command=self.toggle_lock,
            width=40,
            height=26,
            font=("Microsoft YaHei", 10),
            fg_color="#222222",
            hover_color="#333333",
            text_color="#ffffff"
        )
        self.minimal_lock_btn.pack(side="left", padx=3)
        
        self.minimal_play_btn = ctk.CTkButton(
            self.minimal_controls_frame,
            text="▶",
            command=self.play_pause,
            width=40,
            height=26,
            font=("Microsoft YaHei", 12),
            fg_color="#222222",
            hover_color="#333333",
            text_color="#ffffff"
        )
        self.minimal_play_btn.pack(side="left", padx=3)
        
        self.minimal_close_btn2 = ctk.CTkButton(
            self.minimal_controls_frame,
            text="✕",
            command=self.destroy_lyrics_window,
            width=40,
            height=26,
            font=("Microsoft YaHei", 12),
            fg_color="#222222",
            hover_color="#442222",
            text_color="#ff6666"
        )
        self.minimal_close_btn2.pack(side="left", padx=3)
        
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
            self.minimal_controls_frame.pack_forget()
        else:
            self.header_frame.pack_forget()
            self.controls_frame.pack_forget()
            self.minimal_close_btn.pack_forget()
            
            if config.get("show_minimal_controls", False):
                self.minimal_controls_frame.pack(side="top", anchor="ne", padx=10, pady=5)
        
        self._update_window_size()

    def on_style_change(self, choice):
        style_map = {
            "现代": LyricsStyle.MODERN,
            "经典": LyricsStyle.CLASSIC,
            "极简": LyricsStyle.MINIMAL,
            "玻璃": LyricsStyle.GLASS
        }
        self.current_style = style_map.get(choice, LyricsStyle.MODERN)
        self.style_menu.set(choice)
        self.apply_style()

    def on_size_change(self, value):
        self.font_size = int(value)
        self.size_value.configure(text=str(self.font_size))
        if hasattr(self, 'minimal_font_menu'):
            self.minimal_font_menu.set(str(self.font_size))
        self.apply_style()

    def _on_minimal_font_change(self, choice):
        self.font_size = int(choice)
        if hasattr(self, 'size_slider'):
            self.size_slider.set(self.font_size)
            self.size_value.configure(text=str(self.font_size))
        self.apply_style()

    def toggle_lock(self):
        self.is_locked = not self.is_locked
        if self.is_locked:
            self.lock_btn.configure(text="🔓 解锁")
            if hasattr(self, 'minimal_lock_btn'):
                self.minimal_lock_btn.configure(text="🔓")
            self.attributes("-topmost", True)
        else:
            self.lock_btn.configure(text="🔒 锁定")
            if hasattr(self, 'minimal_lock_btn'):
                self.minimal_lock_btn.configure(text="🔒")
        
        if self._context_menu:
            self._context_menu.entryconfigure(
                self._context_menu.index("锁定窗口" if not self.is_locked else "解锁窗口"),
                label="锁定窗口" if not self.is_locked else "解锁窗口"
            )

    def hide_window(self):
        self.withdraw()
        self.is_visible = False

    def show_window(self):
        self.deiconify()
        self.is_visible = True
        self.attributes("-topmost", True)

    def destroy_lyrics_window(self):
        self.destroy()
        self.is_visible = False
        if hasattr(self.music_player, 'lyrics_window'):
            self.music_player.lyrics_window = None

    def start_drag(self, event):
        if self.is_locked:
            return
        
        widget = event.widget
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
        if hasattr(self.music_player, 'play_previous'):
            self.music_player.play_previous()

    def play_next(self):
        if hasattr(self.music_player, 'play_next_song'):
            self.music_player.play_next_song()

    def play_pause(self):
        if hasattr(self.music_player, 'control_bar'):
            if hasattr(self.music_player.control_bar, 'play_pause'):
                self.music_player.control_bar.play_pause()
        self.update_play_button()

    def update_play_button(self):
        try:
            is_playing = False
            try:
                import vlc
                if hasattr(self.music_player, 'music_list_player'):
                    state = self.music_player.music_list_player.get_state()
                    is_playing = (state == vlc.State.Playing)
            except Exception:
                pass
            
            if hasattr(self.music_player, '_is_playing'):
                is_playing = self.music_player._is_playing
            
            if is_playing:
                self.play_pause_btn.configure(image=self.pause_icon)
                if hasattr(self, 'minimal_play_btn'):
                    self.minimal_play_btn.configure(text="⏸")
            else:
                self.play_pause_btn.configure(image=self.play_icon)
                if hasattr(self, 'minimal_play_btn'):
                    self.minimal_play_btn.configure(text="▶")
        except Exception:
            pass

    def toggle_favorite(self):
        try:
            song_title = ""
            if hasattr(self.music_player, 'get_song_title'):
                song_title = self.music_player.get_song_title()
            
            if not song_title:
                song_title = "当前歌曲"
            
            is_fav = self.lyrics_manager.toggle_favorite(song_title)
            self.update_favorite_button(is_fav)
            
            logging.info(f"歌曲 '{song_title}' 已{'收藏' if is_fav else '取消收藏'}")
        except Exception as e:
            logging.exception(e)

    def update_favorite_button(self, is_favorite):
        if is_favorite:
            self.favorite_btn.configure(image=self.heart_filled_icon)
        else:
            self.favorite_btn.configure(image=self.heart_empty_icon)

    def load_lyrics_for_current_song(self):
        try:
            if hasattr(self.music_player, 'music_list_player'):
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
                        
                        song_title = ""
                        if hasattr(self.music_player, 'get_song_title'):
                            song_title = self.music_player.get_song_title()
                        if song_title:
                            is_fav = self.lyrics_manager.is_favorite(song_title)
                            self.update_favorite_button(is_fav)
                        
                        artist = ""
                        if hasattr(self.music_player, 'get_song_artist'):
                            artist = self.music_player.get_song_artist()
                        self.song_info_label.configure(text=f"{song_title} - {artist}")
        except Exception as e:
            logging.exception(e)
            self.current_lyric_label.configure(text="暂无歌词")

    def update_lyrics(self):
        try:
            should_update = False
            import vlc
            if hasattr(self.music_player, 'music_list_player'):
                if self.music_player.music_list_player.get_state() == vlc.State.Playing:
                    should_update = True
                    
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
        except Exception:
            pass
        
        try:
            self.after(100, self.update_lyrics)
        except Exception:
            pass
