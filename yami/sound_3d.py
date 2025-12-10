"""3D Sound Mixer Frame"""

import math
import tkinter as tk
import customtkinter as ctk
import logging
import vlc


class Sound3DFrame(ctk.CTkFrame):
    """3D Audio Mixer with Canvas Interaction"""
    
    def __init__(self, parent):
        super().__init__(
            parent,
            width=600,
            height=400
        )
        self.parent = parent
        self.music_player = parent.music
        
        # 3D Sound parameters
        self.room_radius = 180
        self.listener_radius = 10
        self.source_radius = 8
        
        # Source position (normalized -1 to 1 for x and y)
        self.source_x = 0
        self.source_y = 0
        
        # Reverb parameters
        self.max_reverb = 10.0
        self.min_reverb = 0.0
        
        # Drag state
        self.dragging = False
        
        # Create canvas
        self.canvas = tk.Canvas(self, 
                               width=400, 
                               height=400,
                               bg="#1e1e1e",
                               highlightthickness=0)
        self.canvas.pack(pady=20)
        
        # Create control panel
        self.control_panel = ctk.CTkFrame(self)
        self.control_panel.pack(fill=tk.X, padx=20, pady=10)
        
        self.panning_label = ctk.CTkLabel(self.control_panel, text="声像: 0.0")
        self.panning_label.pack(side=tk.LEFT, padx=20)
        
        self.volume_label = ctk.CTkLabel(self.control_panel, text="音量: 100%")
        self.volume_label.pack(side=tk.LEFT, padx=20)
        
        self.reverb_label = ctk.CTkLabel(self.control_panel, text="混响: 0%")
        self.reverb_label.pack(side=tk.LEFT, padx=20)
        
        # Setup canvas bindings
        self.canvas.bind("<ButtonPress-1>", self.start_drag)
        self.canvas.bind("<B1-Motion>", self.drag_source)
        self.canvas.bind("<ButtonRelease-1>", self.stop_drag)
        
        # Initialize VLC audio effects
        try:
            self.initialize_audio_effects()
        except Exception as e:
            print(f"Warning: Could not initialize audio effects: {e}")
        
        # Draw initial scene
        self.draw_scene()
        
        # Start animation loop
        self.animation_loop()
        
        logging.debug("initialized 3D sound frame")
    
    def initialize_audio_effects(self):
        """Initialize VLC audio effects for panning, volume and reverb"""
        try:
            self.music_player.audio_set_volume(100)
            self.music_player.audio_set_pan(0.0)
            
            # Initialize reverb effect
            try:
                self.reverb_effect = self.music_player.add_equalizer()
            except:
                # Fall back if equalizer isn't available
                self.reverb_effect = None
        except Exception as e:
            print(f"Warning: Could not initialize audio effects: {e}")
            self.reverb_effect = None
    
    def start_drag(self, event):
        """Start dragging the sound source"""
        # Convert canvas coordinates to normalized coordinates
        x = event.x - 200
        y = event.y - 200
        distance = math.hypot(x, y)
        
        # Check if click is on source
        if distance <= self.source_radius + 5:
            self.dragging = True
    
    def drag_source(self, event):
        """Drag the sound source"""
        if not self.dragging:
            return
            
        # Get canvas coordinates relative to center
        x = event.x - 200
        y = event.y - 200
        distance = math.hypot(x, y)
        
        # Limit to room radius
        if distance > self.room_radius:
            ratio = self.room_radius / distance
            x *= ratio
            y *= ratio
            distance = self.room_radius
        
        # Update source position
        self.source_x = x / self.room_radius
        self.source_y = y / self.room_radius
        
        # Update audio parameters
        self.update_audio_parameters(distance)
        
        # Redraw scene
        self.draw_scene()
    
    def stop_drag(self, event):
        """Stop dragging the sound source"""
        self.dragging = False
    
    def update_audio_parameters(self, distance):
        """Update audio based on source position"""
        try:
            # Update panning (-1.0 to 1.0)
            pan = self.source_x
            self.music_player.audio_set_pan(pan)
            self.panning_label.configure(text=f"声像: {pan:.1f}")
            
            # Update volume based on distance (inverse square law)
            max_distance = self.room_radius
            normalized_distance = distance / max_distance
            volume = max(0, 100 * (1 - normalized_distance ** 2))
            self.music_player.audio_set_volume(int(volume))
            self.volume_label.configure(text=f"音量: {int(volume)}%")
            
            # Update reverb based on distance to wall
            distance_to_wall = self.room_radius - distance
            reverb_amount = (distance_to_wall / self.room_radius) * 100
            self.reverb_label.configure(text=f"混响: {int(reverb_amount)}%")
            
            # Apply reverb effect if available
            if self.reverb_effect:
                reverb_value = (distance_to_wall / self.room_radius) * self.max_reverb
                # Set reverb using equalizer bands to simulate effect
                try:
                    for i in range(self.reverb_effect.get_band_count()):
                        freq = self.reverb_effect.get_band_frequency(i)
                        if freq < 1000:
                            self.reverb_effect.set_amp_at_index(i, reverb_value)
                except:
                    pass
        except Exception as e:
            print(f"Warning: Could not update audio parameters: {e}")
    
    def draw_scene(self):
        """Draw the 3D sound scene"""
        self.canvas.delete("all")
        
        # Draw room
        self.canvas.create_oval(200 - self.room_radius, 200 - self.room_radius,
                               200 + self.room_radius, 200 + self.room_radius,
                               outline="#444444", width=2)
        
        # Draw listener at center
        self.canvas.create_oval(200 - self.listener_radius, 200 - self.listener_radius,
                               200 + self.listener_radius, 200 + self.listener_radius,
                               fill="#00ff00", outline="#ffffff")
        
        # Draw sound source
        source_pos_x = 200 + self.source_x * self.room_radius
        source_pos_y = 200 + self.source_y * self.room_radius
        
        self.canvas.create_oval(source_pos_x - self.source_radius, source_pos_y - self.source_radius,
                               source_pos_x + self.source_radius, source_pos_y + self.source_radius,
                               fill="#ff0066", outline="#ffffff", width=2)
        
        # Draw reverb visualization
        distance_to_wall = self.room_radius - math.hypot(self.source_x * self.room_radius, self.source_y * self.room_radius)
        reverb_intensity = (distance_to_wall / self.room_radius) * 3
        
        for i in range(1, 4):
            alpha = int(255 * (1 - i/4) * reverb_intensity)
            if alpha <= 0:
                continue
            radius = self.source_radius + i * 10 * reverb_intensity
            self.canvas.create_oval(source_pos_x - radius, source_pos_y - radius,
                                   source_pos_x + radius, source_pos_y + radius,
                                   outline=f"#{alpha:02x}{alpha:02x}ff", width=1)
    
    def animation_loop(self):
        """Update animation effects"""
        self.draw_scene()
        self.after(30, self.animation_loop)
    
    def reset(self):
        """Reset source position to center"""
        self.source_x = 0
        self.source_y = 0
        self.update_audio_parameters(0)
        self.draw_scene()
