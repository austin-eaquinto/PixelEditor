# animation_preview.py
import tkinter as tk
from settings import EMPTY_COLOR

class AnimationPreview:
    def __init__(self, app_ref):
        self.app = app_ref
        self.is_playing = True
        self.current_frame_index = 0
        self.frames = [] # Will hold the grid_data of each tab
        self.timer_id = None
        
        # UI Setup
        self.win = tk.Toplevel(self.app.root)
        self.win.title("Preview")
        self.win.geometry("300x350")
        self.win.transient(self.app.root)
        
        # Canvas (Scaled up so it's easy to see)
        self.preview_scale = 10 if self.app.pixel_size < 10 else 5
        # Calculate canvas size based on grid
        cw = self.app.cols * self.preview_scale
        ch = self.app.rows * self.preview_scale
        
        # Scrollable Frame wrapper in case the sprite is huge
        container = tk.Frame(self.win)
        container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.canvas = tk.Canvas(container, bg="#cccccc", width=min(cw, 280), height=min(ch, 200))
        self.canvas.pack()

        # Controls
        ctrl_frame = tk.Frame(self.win)
        ctrl_frame.pack(fill=tk.X, pady=10)
        
        self.btn_play = tk.Button(ctrl_frame, text="⏸ Pause", command=self.toggle_play, width=10)
        self.btn_play.pack(side=tk.LEFT, padx=10)
        
        tk.Label(ctrl_frame, text="Speed (ms):").pack(side=tk.LEFT)
        self.scale_speed = tk.Scale(ctrl_frame, from_=50, to=1000, orient=tk.HORIZONTAL, resolution=50)
        self.scale_speed.set(200) # Default 5FPS
        self.scale_speed.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        self.win.protocol("WM_DELETE_WINDOW", self.close_window)
        
        # Start
        self.refresh_frame_data()
        self.animate()

    def refresh_frame_data(self):
        """Grabs the current state of all tabs."""
        self.frames = []
        tabs = self.app.notebook.tabs()
        for i in range(len(tabs) - 1): # Skip "+" tab
            tab_widget = self.app.root.nametowidget(tabs[i])
            tab = getattr(tab_widget, "tab_obj", None)
            if tab:
                self.frames.append(tab.grid_data)

    def toggle_play(self):
        self.is_playing = not self.is_playing
        self.btn_play.config(text="⏸ Pause" if self.is_playing else "▶ Play")
        if self.is_playing:
            self.animate()

    def animate(self):
        if not self.frames or not self.win.winfo_exists(): return
        
        if self.is_playing:
            # 1. Draw current frame
            self.draw_frame(self.frames[self.current_frame_index])
            
            # 2. Advance index
            self.current_frame_index = (self.current_frame_index + 1) % len(self.frames)
            
            # 3. Schedule next loop
            speed = self.scale_speed.get()
            self.timer_id = self.win.after(speed, self.animate)

    def draw_frame(self, grid_data):
        self.canvas.delete("all")
        # Center the drawing if canvas is bigger than sprite
        for r, row in enumerate(grid_data):
            for c, color in enumerate(row):
                if color != EMPTY_COLOR:
                    x1 = c * self.preview_scale
                    y1 = r * self.preview_scale
                    x2 = x1 + self.preview_scale
                    y2 = y1 + self.preview_scale
                    self.canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline="")

    def close_window(self):
        if self.timer_id:
            self.win.after_cancel(self.timer_id)
        self.win.destroy()