"""Lyric Editor - Immersive Time Axis Mode"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import time
import re
import json
from pathlib import Path

class LyricEditor(ttk.Frame):
    """Immersive lyric time axis editor with dual panel layout"""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.current_line_index = 0
        self.lyric_lines = []
        self.timestamps = []
        
        # Configure grid layout
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        # Left panel - Text input
        self.left_panel = ttk.Frame(self, padding=10)
        self.left_panel.grid(row=0, column=0, sticky="nsew")
        self.left_panel.grid_rowconfigure(0, weight=1)
        self.left_panel.grid_columnconfigure(0, weight=1)
        
        ttk.Label(self.left_panel, text="歌词文本输入", font=("roboto", 16)).pack(pady=(0, 10))
        
        self.text_input = scrolledtext.ScrolledText(self.left_panel, wrap=tk.WORD, font=("微软雅黑", 12))
        self.text_input.pack(fill=tk.BOTH, expand=True)
        self.text_input.bind('<KeyRelease>', self._on_text_change)
        
        # Right panel - Preview
        self.right_panel = ttk.Frame(self, padding=10)
        self.right_panel.grid(row=0, column=1, sticky="nsew")
        self.right_panel.grid_rowconfigure(0, weight=1)
        self.right_panel.grid_columnconfigure(0, weight=1)
        
        preview_frame = ttk.Frame(self.right_panel)
        preview_frame.pack(fill=tk.X, pady=(0, 10))
        ttk.Label(preview_frame, text="打轴预览", font=("roboto", 16)).pack(side=tk.LEFT)
        
        self.current_line_label = ttk.Label(preview_frame, text="当前行: 0/0", font=("roboto", 10))
        self.current_line_label.pack(side=tk.RIGHT)
        
        self.preview_listbox = tk.Listbox(self.right_panel, font=("微软雅黑", 12), selectmode=tk.SINGLE)
        self.preview_listbox.pack(fill=tk.BOTH, expand=True)
        self.preview_listbox.bind('<ButtonRelease-1>', self._on_preview_click)
        
        # Control frame
        self.control_frame = ttk.Frame(self, padding=10)
        self.control_frame.grid(row=1, column=0, columnspan=2, sticky="ew")
        
        self.status_label = ttk.Label(self.control_frame, text="按 Down 键标记当前播放时间到歌词行")
        self.status_label.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(self.control_frame, text="保存歌词", command=self._save_lyrics).pack(side=tk.RIGHT, padx=5)
        ttk.Button(self.control_frame, text="退出编辑", command=self._exit_editor).pack(side=tk.RIGHT, padx=5)
        ttk.Button(self.control_frame, text="重置时间轴", command=self._reset_timestamps).pack(side=tk.RIGHT, padx=5)
        
        # Bind keyboard events
        self.bind_all('<Down>', self._on_down_key)
        self.bind_all('<KP_Down>', self._on_down_key)
        
        # Load example lyrics
        self._load_example_lyrics()
        
    def _load_example_lyrics(self):
        """Load example lyrics into editor"""
        example_lyrics = """[00:00.00]
请输入或粘贴歌词到左侧面板
每行歌词单独一行

按下 Down 键标记当前播放时间到对应歌词行
点击预览区歌词可以跳转到对应时间点
"""
        self.text_input.insert(tk.END, example_lyrics)
        self._on_text_change()
        
    def _on_text_change(self, event=None):
        """Update preview when text changes"""
        content = self.text_input.get(1.0, tk.END)
        lines = [line.strip() for line in content.split('\n') if line.strip()]
        
        # Parse existing timestamps
        new_lyric_lines = []
        new_timestamps = []
        
        for line in lines:
            timestamp_match = re.match(r'^\[(\d{2}):(\d{2})\.(\d{2,3})\]\s*(.*)', line)
            if timestamp_match:
                mins, secs, millis, lyric = timestamp_match.groups()
                total_sec = float(mins) * 60 + float(secs) + float(millis) / 100
                new_timestamps.append(total_sec)
                new_lyric_lines.append(lyric)
            else:
                new_lyric_lines.append(line)
                new_timestamps.append(None)
        
        self.lyric_lines = new_lyric_lines
        self.timestamps = new_timestamps
        
        # Reset current line if it's beyond the new length
        if self.current_line_index >= len(self.lyric_lines):
            self.current_line_index = 0
        
        self._update_preview()
        
    def _update_preview(self):
        """Update preview listbox"""
        self.preview_listbox.delete(0, tk.END)
        
        for i, (lyric, timestamp) in enumerate(zip(self.lyric_lines, self.timestamps)):
            if timestamp is not None:
                mins = int(timestamp // 60)
                secs = int(timestamp % 60)
                millis = int((timestamp - int(timestamp)) * 100)
                display_text = f"[{mins:02d}:{secs:02d}.{millis:02d}] {lyric}"
            else:
                display_text = f"[未标记] {lyric}"
            
            self.preview_listbox.insert(tk.END, display_text)
            
            # Highlight current line
            if i == self.current_line_index:
                self.preview_listbox.itemconfig(i, {'bg': '#4a6fa5', 'fg': 'white'})
            else:
                self.preview_listbox.itemconfig(i, {'bg': '', 'fg': ''})
        
        # Update current line label
        self.current_line_label.config(text=f"当前行: {self.current_line_index + 1}/{len(self.lyric_lines)}")
        
        # Auto scroll to current line
        self._auto_scroll_to_current()
        
    def _auto_scroll_to_current(self):
        """Auto scroll to keep current line centered"""
        if not self.lyric_lines:
            return
            
        listbox_height = self.preview_listbox.winfo_height()
        line_height = self.preview_listbox.winfo_reqheight() // max(1, self.preview_listbox.size())
        visible_lines = listbox_height // line_height
        
        # Calculate scroll position to center current line
        scroll_to = max(0, self.current_line_index - visible_lines // 2)
        self.preview_listbox.yview_moveto(scroll_to / len(self.lyric_lines))
        
    def _on_down_key(self, event=None):
        """Handle Down key press to capture current time"""
        if self.current_line_index >= len(self.lyric_lines):
            return
            
        try:
            # Get current playback time
            current_time = self.parent.music.get_time() / 1000.0
            self.timestamps[self.current_line_index] = current_time
            
            # Move to next line
            self.current_line_index = min(self.current_line_index + 1, len(self.lyric_lines) - 1)
            
            # Update UI
            self._update_preview()
            self._update_text_input()
            
            self.status_label.config(text=f"已标记时间: {current_time:.2f}s")
            
        except Exception as e:
            self.status_label.config(text=f"错误: 无法获取播放时间")
            
    def _update_text_input(self):
        """Update text input with timestamps"""
        content = []
        for lyric, timestamp in zip(self.lyric_lines, self.timestamps):
            if timestamp is not None:
                mins = int(timestamp // 60)
                secs = int(timestamp % 60)
                millis = int((timestamp - int(timestamp)) * 100)
                content.append(f"[{mins:02d}:{secs:02d}.{millis:02d}] {lyric}")
            else:
                content.append(lyric)
        
        # Preserve cursor position
        cursor_pos = self.text_input.index(tk.INSERT)
        
        self.text_input.delete(1.0, tk.END)
        self.text_input.insert(tk.END, '\n'.join(content))
        
        # Restore cursor position
        try:
            self.text_input.mark_set(tk.INSERT, cursor_pos)
        except:
            pass
            
    def _on_preview_click(self, event):
        """Handle click on preview list to seek to timestamp"""
        selected_index = self.preview_listbox.curselection()
        if not selected_index:
            return
            
        index = selected_index[0]
        if index < len(self.timestamps) and self.timestamps[index] is not None:
            try:
                self.parent.seek_to_time(int(self.timestamps[index] * 1000))
                self.current_line_index = index
                self._update_preview()
                self.status_label.config(text=f"跳转到: {self.timestamps[index]:.2f}s")
            except Exception as e:
                self.status_label.config(text=f"错误: 无法跳转播放位置")
                
    def _save_lyrics(self):
        """Save lyrics to file"""
        if not self.lyric_lines:
            messagebox.showwarning("警告", "没有歌词可以保存")
            return
            
        try:
            # Get current media info
            media = self.parent.music.get_media()
            title = media.get_meta(0) or "未知歌曲"
            artist = media.get_meta(1) or "未知艺术家"
            
            # Create filename
            filename = f"{title} - {artist}.lrc"
            filename = filename.replace('/', '_').replace('\\', '_').replace(':', '-')
            
            # Format lyrics
            lyrics_content = []
            for lyric, timestamp in zip(self.lyric_lines, self.timestamps):
                if timestamp is not None:
                    mins = int(timestamp // 60)
                    secs = int(timestamp % 60)
                    millis = int((timestamp - int(timestamp)) * 100)
                    lyrics_content.append(f"[{mins:02d}:{secs:02d}.{millis:02d}] {lyric}")
                else:
                    lyrics_content.append(lyric)
            
            # Save file
            with open(filename, 'w', encoding='utf-8') as f:
                f.write('\n'.join(lyrics_content))
                
            messagebox.showinfo("成功", f"歌词已保存到:\n{filename}")
            self.status_label.config(text=f"歌词已保存: {filename}")
            
        except Exception as e:
            messagebox.showerror("错误", f"保存失败: {str(e)}")
            
    def _reset_timestamps(self):
        """Reset all timestamps"""
        self.timestamps = [None] * len(self.lyric_lines)
        self.current_line_index = 0
        self._update_preview()
        self._update_text_input()
        self.status_label.config(text="时间轴已重置")
        
    def _exit_editor(self):
        """Exit editor mode and cleanup"""
        self.cleanup()
        self.parent.toggle_lyric_editor_mode()
    
    def cleanup(self):
        """Cleanup when exiting editor"""
        try:
            self.unbind_all('<Down>')
            self.unbind_all('<KP_Down>')
        except:
            pass