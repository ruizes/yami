import tkinter as tk
import math
from threading import Timer

class Sound3DFrame(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.canvas_width = 600
        self.canvas_height = 600
        self.room_radius = 250
        self.listener_radius = 10
        self.source_radius = 8
        
        # 声源初始位置在中心
        self.source_x = self.canvas_width // 2
        self.source_y = self.canvas_height // 2
        self.is_dragging = False
        
        # 混响波纹效果
        self.ripples = []
        
        # 创建Canvas
        self.canvas = tk.Canvas(self, width=self.canvas_width, height=self.canvas_height, bg="#2b2b2b", highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        # 绑定事件
        self.canvas.bind("<ButtonPress-1>", self.on_source_click)
        self.canvas.bind("<B1-Motion>", self.on_source_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_source_release)
        
        # 初始化绘制
        self.draw_scene()
        
        # 启动动画循环
        self.animate()
        
        # 初始音频参数设置
        self.update_audio_params()
    
    def draw_scene(self):
        """绘制整个场景"""
        self.canvas.delete("all")
        
        # 绘制房间（大圆）
        center_x = self.canvas_width // 2
        center_y = self.canvas_height // 2
        
        self.canvas.create_oval(
            center_x - self.room_radius,
            center_y - self.room_radius,
            center_x + self.room_radius,
            center_y + self.room_radius,
            outline="#4a90e2",
            width=3
        )
        
        # 绘制网格线
        self.draw_grid(center_x, center_y)
        
        # 绘制波纹效果
        self.draw_ripples()
        
        # 绘制听众（中心小圆）
        self.canvas.create_oval(
            center_x - self.listener_radius,
            center_y - self.listener_radius,
            center_x + self.listener_radius,
            center_y + self.listener_radius,
            fill="#ffffff",
            outline="#cccccc"
        )
        
        # 绘制声源点
        self.canvas.create_oval(
            self.source_x - self.source_radius,
            self.source_y - self.source_radius,
            self.source_x + self.source_radius,
            self.source_y + self.source_radius,
            fill="#e74c3c",
            outline="#c0392b",
            width=2
        )
        
        # 绘制连接线
        self.canvas.create_line(
            center_x, center_y,
            self.source_x, self.source_y,
            fill="#95a5a6",
            dash=(4, 2)
        )
        
        # 显示参数信息
        distance = self.get_distance_from_center()
        pan = self.calculate_pan()
        volume = self.calculate_volume()
        reverb = self.calculate_reverb()
        
        info_text = f"距离: {int(distance)} | 声像: {pan:+.2f} | 音量: {int(volume)}% | 混响: {int(reverb*100)}%"
        self.canvas.create_text(
            self.canvas_width // 2,
            self.canvas_height - 20,
            text=info_text,
            fill="#ecf0f1",
            font=("Arial", 10)
        )
    
    def draw_grid(self, center_x, center_y):
        """绘制辅助网格"""
        # 十字线
        self.canvas.create_line(center_x, 0, center_x, self.canvas_height, fill="#34495e", dash=(2, 2))
        self.canvas.create_line(0, center_y, self.canvas_width, center_y, fill="#34495e", dash=(2, 2))
        
        # 同心圆网格
        for r in range(50, self.room_radius, 50):
            self.canvas.create_oval(
                center_x - r, center_y - r,
                center_x + r, center_y + r,
                outline="#34495e",
                dash=(1, 2)
            )
    
    def draw_ripples(self):
        """绘制混响波纹效果"""
        current_time = self.canvas.winfo_toplevel().winfo_id() % 1000 / 1000
        
        # 更新波纹
        new_ripples = []
        for ripple in self.ripples:
            ripple["radius"] += ripple["speed"]
            ripple["alpha"] -= 0.02
            if ripple["alpha"] > 0:
                new_ripples.append(ripple)
        
        self.ripples = new_ripples
        
        # 绘制波纹
        for ripple in self.ripples:
            alpha = int(ripple["alpha"] * 255)
            color = f"#{int(0x4a90e2 * alpha / 255):06x}"
            self.canvas.create_oval(
                self.source_x - ripple["radius"],
                self.source_y - ripple["radius"],
                self.source_x + ripple["radius"],
                self.source_y + ripple["radius"],
                outline=color,
                width=1
            )
    
    def on_source_click(self, event):
        """点击声源点开始拖拽"""
        distance = math.hypot(event.x - self.source_x, event.y - self.source_y)
        if distance <= self.source_radius * 2:
            self.is_dragging = True
    
    def on_source_drag(self, event):
        """拖拽声源点"""
        if self.is_dragging:
            center_x = self.canvas_width // 2
            center_y = self.canvas_height // 2
            
            # 计算到中心的距离，限制在房间内
            distance = math.hypot(event.x - center_x, event.y - center_y)
            if distance <= self.room_radius - self.source_radius:
                self.source_x = event.x
                self.source_y = event.y
            else:
                # 在房间边缘放置声源
                angle = math.atan2(event.y - center_y, event.x - center_x)
                self.source_x = center_x + (self.room_radius - self.source_radius) * math.cos(angle)
                self.source_y = center_y + (self.room_radius - self.source_radius) * math.sin(angle)
            
            # 更新音频参数
            self.update_audio_params()
            
            # 添加波纹效果
            self.add_ripple()
    
    def on_source_release(self, event):
        """释放拖拽"""
        self.is_dragging = False
    
    def add_ripple(self):
        """添加新的波纹"""
        reverb = self.calculate_reverb()
        self.ripples.append({
            "radius": self.source_radius,
            "speed": 2 + reverb * 3,
            "alpha": 0.5
        })
    
    def get_distance_from_center(self):
        """计算声源到中心的距离"""
        center_x = self.canvas_width // 2
        center_y = self.canvas_height // 2
        return math.hypot(self.source_x - center_x, self.source_y - center_y)
    
    def calculate_pan(self):
        """计算声像参数 (-1.0 到 1.0)"""
        center_x = self.canvas_width // 2
        max_range = self.room_radius
        pan = (self.source_x - center_x) / max_range
        return max(-1.0, min(1.0, pan))
    
    def calculate_volume(self):
        """计算音量 (0 到 100)"""
        distance = self.get_distance_from_center()
        max_distance = self.room_radius
        
        # 使用平方反比衰减
        if distance == 0:
            return 100
        volume = 100 * (1 - (distance / max_distance) ** 2)
        return max(0, min(100, volume))
    
    def calculate_reverb(self):
        """计算混响参数 (0 到 1.0)"""
        distance = self.get_distance_from_center()
        max_distance = self.room_radius
        
        # 距离越远混响越大
        reverb = (distance / max_distance) ** 1.5
        return max(0.0, min(1.0, reverb))
    
    def update_audio_params(self):
        """更新VLC音频参数"""
        try:
            pan = self.calculate_pan()
            volume = self.calculate_volume()
            
            if hasattr(self.parent, 'music') and self.parent.music is not None:
                # 设置声像
                self.parent.music.audio_set_pan(pan)
                # 设置音量
                self.parent.music.audio_set_volume(volume)
                
        except Exception as e:
            print(f"Error updating audio parameters: {e}")
    
    def animate(self):
        """动画循环"""
        self.draw_scene()
        self.after(30, self.animate)
