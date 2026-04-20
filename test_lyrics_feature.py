"""测试迷你桌面歌词功能"""

import tkinter as tk
import customtkinter as ctk
from PIL import Image, ImageDraw
import logging

logging.basicConfig(level=logging.DEBUG)

from yami.lyrics_window import LyricsWindow, LyricsStyle, STYLE_CONFIGS
from yami.lyrics import LyricsManager, LyricsParser


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
        
    class MockControlBar:
        def play_pause(self, event=None):
            print("播放/暂停")
            
    control_bar = MockControlBar()
    
    class MockMusicListPlayer:
        def get_state(self):
            return 3
            
    music_list_player = MockMusicListPlayer()


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
    print("=" * 50)
    print("测试歌词解析器")
    print("=" * 50)
    
    lrc_path = create_test_lrc()
    parser = LyricsParser()
    
    if parser.parse_lrc_file(lrc_path):
        print(f"歌曲标题: {parser.title}")
        print(f"歌手: {parser.artist}")
        print(f"专辑: {parser.album}")
        print(f"歌词行数: {len(parser.lyrics)}")
        
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
    print("=" * 50)
    print("测试歌词窗口")
    print("=" * 50)
    
    ctk.set_appearance_mode("dark")
    
    root = ctk.CTk()
    root.title("音乐播放器测试")
    root.geometry("400x200")
    
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
        font=("Microsoft YaHei", 14),
        height=50
    )
    btn.pack(expand=True, padx=20, pady=20)
    
    info_label = ctk.CTkLabel(
        root,
        text="测试功能:\n• 4种样式切换\n• 字体大小调整\n• 锁定/解锁\n• 播放控制按钮\n• 收藏功能",
        font=("Microsoft YaHei", 12),
        justify="left"
    )
    info_label.pack(pady=10)
    
    print("\n歌词窗口已准备就绪！")
    print("点击按钮可以打开迷你歌词窗口")
    print()
    print("功能说明:")
    print("1. 样式下拉菜单: 现代/经典/极简/玻璃")
    print("2. 字体滑块: 16-48 像素可调")
    print("3. 锁定按钮: 防止误触，锁定后无法拖动")
    print("4. 隐藏按钮: 隐藏歌词窗口")
    print("5. 底部控制: 收藏、上一首、播放/暂停、下一首")
    
    root.mainloop()


if __name__ == "__main__":
    test_lyrics_parser()
    test_lyrics_window()
