import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import re
from typing import Dict, List, Tuple

class LyricEditor(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.current_line = 0
        self.lyric_timestamps: Dict[int, float] = {}
        self.lyric_lines: List[str] = []
        
        # Configure grid layout
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        # Left panel - Text input
        self.left_panel = ttk.Frame(self)
        self.left_panel.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        self.left_panel.grid_columnconfigure(0, weight=1)
        self.left_panel.grid_rowconfigure(0, weight=1)
        
        self.text_input_label = ttk.Label(self.left_panel, text="歌词文本输入（每行一句歌词）")
        self.text_input_label.grid(row=0, column=0, sticky="w", pady=5)
        
        self.text_input = scrolledtext.ScrolledText(self.left_panel, wrap=tk.WORD, font=("微软雅黑", 12))
        self.text_input.grid(row=1, column=0, sticky="nsew", pady=5)
        self.text_input.bind("<<Modified>>", self._on_text_change)
        
        # Right panel - Preview
        self.right_panel = ttk.Frame(self)
        self.right_panel.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)
        self.right_panel.grid_columnconfigure(0, weight=1)
        self.right_panel.grid_rowconfigure(1, weight=1)
        
        self.preview_label = ttk.Label(self.right_panel, text="打轴预览（按Down键标记时间）")
        self.preview_label.grid(row=0, column=0, sticky="w", pady=5)
        
        # Current playback time display
        self.current_time_display = ttk.Label(
            self.right_panel, 
            text="当前时间: 00:00.000", 
            font=("微软雅黑", 14, "bold")
        )
        self.current_time_display.grid(row=1, column=0, sticky="n", pady=5)
        
        self.preview_frame = ttk.Frame(self.right_panel)
        self.preview_frame.grid(row=2, column=0, sticky="nsew", pady=5)
        self.preview_frame.grid_columnconfigure(0, weight=1)
        self.preview_frame.grid_rowconfigure(0, weight=1)
        
        self.preview_list = tk.Listbox(self.preview_frame, font=("微软雅黑", 12), activestyle="none")
        self.preview_list.grid(row=0, column=0, sticky="nsew")
        self.preview_list.bind("<<ListboxSelect>>", self._on_preview_click)
        
        self.preview_scrollbar = ttk.Scrollbar(self.preview_frame, orient="vertical", command=self.preview_list.yview)
        self.preview_scrollbar.grid(row=0, column=1, sticky="ns")
        self.preview_list.configure(yscrollcommand=self.preview_scrollbar.set)
        
        # Control buttons
        self.button_frame = ttk.Frame(self)
        self.button_frame.grid(row=1, column=0, columnspan=2, pady=10)
        
        self.save_button = ttk.Button(self.button_frame, text="保存歌词", command=self._save_lyrics)
        self.save_button.pack(side=tk.LEFT, padx=5)
        
        self.reset_button = ttk.Button(self.button_frame, text="重置时间轴", command=self._reset_timestamps)
        self.reset_button.pack(side=tk.LEFT, padx=5)
        
        self.exit_button = ttk.Button(self.button_frame, text="退出编辑", command=self._exit_editor)
        self.exit_button.pack(side=tk.RIGHT, padx=5)
        
        # Bind keyboard events
        self.bind_all("<Down>", self._on_down_key)
        
        # Start time update loop
        self._update_time_display()
        
    def _on_text_change(self, event=None):
        if self.text_input.edit_modified():
            content = self.text_input.get(1.0, tk.END)
            self.lyric_lines = [line.strip() for line in content.split('\n') if line.strip()]
            self._update_preview()
            self.text_input.edit_modified(False)
    
    def _update_preview(self):
        self.preview_list.delete(0, tk.END)
        for idx, line in enumerate(self.lyric_lines):
            if idx in self.lyric_timestamps:
                time_str = f"[{self._format_time(self.lyric_timestamps[idx])}] {line}"
            else:
                time_str = f"[未标记] {line}"
            self.preview_list.insert(tk.END, time_str)
        
        # Highlight current line
        if 0 <= self.current_line < len(self.lyric_lines):
            self.preview_list.selection_clear(0, tk.END)
            self.preview_list.selection_set(self.current_line)
            self._scroll_to_current_line()
    
    def _format_time(self, time_ms: float) -> str:
        total_seconds = time_ms / 1000
        minutes = int(total_seconds // 60)
        seconds = total_seconds % 60
        return f"{minutes:02d}:{seconds:06.3f}"
    
    def _update_time_display(self):
        try:
            current_time = self.parent.get_current_time_ms()
            time_str = self._format_time(current_time)
            self.current_time_display.configure(text=f"当前时间: {time_str}")
        except:
            pass
        self.after(100, self._update_time_display)
    
    def _parse_time(self, time_str: str) -> float:
        try:
            minutes, seconds = time_str.split(':')
            total_seconds = int(minutes) * 60 + float(seconds)
            return total_seconds * 1000
        except:
            return 0
    
    def _on_down_key(self, event=None):
        if self.current_line >= len(self.lyric_lines):
            messagebox.showinfo("完成", "所有歌词行都已标记！")
            return
        
        # Get current playback time
        current_time = self.parent.get_current_time_ms()
        self.lyric_timestamps[self.current_line] = current_time
        
        # Move to next line
        self.current_line += 1
        self._update_preview()
    
    def _on_preview_click(self, event=None):
        selected_indices = self.preview_list.curselection()
        if selected_indices:
            idx = selected_indices[0]
            if idx in self.lyric_timestamps:
                self.parent.seek_to_time(int(self.lyric_timestamps[idx]))
                self.current_line = idx
                self._update_preview()
    
    def _scroll_to_current_line(self):
        if 0 <= self.current_line < self.preview_list.size():
            # Calculate center position
            line_count = self.preview_list.size()
            half_viewport = self.preview_list.winfo_height() // (2 * self.preview_list.winfo_font().metrics('linespace'))
            scroll_to = max(0, min(self.current_line - half_viewport, line_count - half_viewport * 2))
            self.preview_list.see(scroll_to)
    
    def _save_lyrics(self):
        if not self.lyric_timestamps:
            messagebox.showwarning("警告", "还没有标记任何歌词时间！")
            return
            
        # Sort timestamps by index
        sorted_timestamps = sorted(self.lyric_timestamps.items())
        
        # Generate LRC content
        lrc_content = "[ti:Unknown]\n[ar:Unknown]\n[al:Unknown]\n\n"
        for idx, time_ms in sorted_timestamps:
            if idx < len(self.lyric_lines):
                time_str = self._format_time(time_ms)
                lrc_content += f"[{time_str}] {self.lyric_lines[idx]}\n"
        
        # Save to file
        try:
            from tkinter import filedialog
            file_path = filedialog.asksaveasfilename(
                defaultextension=".lrc",
                filetypes=[("LRC歌词文件", "*.lrc"), ("所有文件", "*.*")]
            )
            if file_path:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(lrc_content)
                messagebox.showinfo("成功", "歌词文件已保存！")
        except Exception as e:
            messagebox.showerror("错误", f"保存失败: {str(e)}")
    
    def _reset_timestamps(self):
        self.lyric_timestamps.clear()
        self.current_line = 0
        self._update_preview()
    
    def _exit_editor(self):
        # Cleanup keyboard bindings
        self.cleanup()
        # Switch back to normal mode
        self.parent.toggle_lyric_editor_mode()
    
    def cleanup(self):
        try:
            self.unbind_all("<Down>")
        except:
            pass