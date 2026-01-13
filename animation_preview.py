# animation_preview.py
import tkinter as tk
from settings import EMPTY_COLOR

class AnimationPreview:
    def __init__(self, app_ref):
        self.app = app_ref
        self.is_playing = True
        self.current_frame_index = 0
        self.timer_id = None
        self.cached_frames = [] 
        self.pixel_cache = []       
        self.onion_cache = []      
        self.cache_created = False
        
        self.win = tk.Toplevel(self.app.root)
        self.win.title("Preview")
        self.win.transient(self.app.root)
        
        if self.app.pixel_size >= 10:
            self.preview_scale = 6
        else:
            self.preview_scale = 4

        self.content_w = self.app.cols * self.preview_scale
        self.content_h = self.app.rows * self.preview_scale
        
        req_w = self.content_w + 40
        req_h = self.content_h + 120
        screen_w = self.win.winfo_screenwidth()
        screen_h = self.win.winfo_screenheight()
        final_w = min(req_w, int(screen_w * 0.9))
        final_h = min(req_h, int(screen_h * 0.9))
        self.win.geometry(f"{final_w}x{final_h}")

        container = tk.Frame(self.win)
        container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.v_scroll = tk.Scrollbar(container, orient=tk.VERTICAL)
        self.h_scroll = tk.Scrollbar(container, orient=tk.HORIZONTAL)
        
        # --- ISSUE 5 FIX: WHITE BACKGROUND ---
        self.canvas = tk.Canvas(container, bg="#FFFFFF",
                                xscrollcommand=self.h_scroll.set,
                                yscrollcommand=self.v_scroll.set)
        
        self.v_scroll.config(command=self.canvas.yview)
        self.h_scroll.config(command=self.canvas.xview)
        
        self.v_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.h_scroll.pack(side=tk.BOTTOM, fill=tk.X)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.canvas.config(scrollregion=(0, 0, self.content_w, self.content_h))

        # Controls
        ctrl_frame = tk.Frame(self.win)
        ctrl_frame.pack(fill=tk.X, pady=10)
        
        self.btn_play = tk.Button(ctrl_frame, text="⏸ Pause", command=self.toggle_play, width=8)
        self.btn_play.pack(side=tk.LEFT, padx=5)
        
        tk.Label(ctrl_frame, text="Onion:").pack(side=tk.LEFT, padx=(5, 2))
        self.var_onion_mode = tk.StringVar(value="off")
        
        tk.Radiobutton(ctrl_frame, text="Off", variable=self.var_onion_mode, 
                       value="off", command=self.refresh_display).pack(side=tk.LEFT)
        tk.Radiobutton(ctrl_frame, text="Prev", variable=self.var_onion_mode, 
                       value="prev", command=self.refresh_display).pack(side=tk.LEFT)
        tk.Radiobutton(ctrl_frame, text="All", variable=self.var_onion_mode, 
                       value="all", command=self.refresh_display).pack(side=tk.LEFT)
        
        # --- ISSUE 5 FIX: TOGGLE DEFAULT TRUE ---
        self.var_white_bg = tk.BooleanVar(value=True)
        tk.Checkbutton(ctrl_frame, text="White BG", variable=self.var_white_bg, 
                       command=self.toggle_bg_color).pack(side=tk.LEFT, padx=10)

        tk.Label(ctrl_frame, text="Speed:").pack(side=tk.LEFT, padx=(5, 2))
        self.lbl_speed_val = tk.Label(ctrl_frame, text="200ms", width=5)
        self.lbl_speed_val.pack(side=tk.LEFT)
        
        self.scale_speed = tk.Scale(ctrl_frame, from_=50, to=1000, orient=tk.HORIZONTAL, 
                                    resolution=50, showvalue=0, command=self.update_speed_label)
        self.scale_speed.set(200) 
        self.scale_speed.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        self.win.protocol("WM_DELETE_WINDOW", self.close_window)
        
        # Initial Setup
        self.create_grid_objects()
        self.rebuild_frame_cache() 
        self.animate()

    def update_speed_label(self, val):
        self.lbl_speed_val.config(text=f"{val}ms")

    def create_grid_objects(self):
        self.canvas.delete("all")
        self.pixel_cache = [] 
        self.onion_cache = [] 
        
        for r in range(self.app.rows):
            row_items = []
            for c in range(self.app.cols):
                x1 = c * self.preview_scale
                y1 = r * self.preview_scale
                x2 = x1 + self.preview_scale
                y2 = y1 + self.preview_scale
                item_id = self.canvas.create_rectangle(x1, y1, x2, y2, fill="", outline="", state="hidden")
                row_items.append(item_id)
            self.onion_cache.append(row_items)

        for r in range(self.app.rows):
            for c in range(self.app.cols):
                x1 = c * self.preview_scale
                y1 = r * self.preview_scale
                x2 = x1 + self.preview_scale
                y2 = y1 + self.preview_scale
                item_id = self.canvas.create_rectangle(x1, y1, x2, y2, fill="", outline="", state="hidden")
                self.pixel_cache.append(item_id)
            
        self.cache_created = True

    def rebuild_frame_cache(self):
        frames = []
        tabs = self.app.notebook.tabs()
        for i in range(len(tabs) - 1): 
            tab_widget = self.app.root.nametowidget(tabs[i])
            tab = getattr(tab_widget, "tab_obj", None)
            if tab:
                frames.append(tab.get_flattened_data())
        self.cached_frames = frames

    def toggle_bg_color(self):
        bg = "#FFFFFF" if self.var_white_bg.get() else "#cccccc"
        self.canvas.config(bg=bg)

    def toggle_play(self):
        self.is_playing = not self.is_playing
        self.btn_play.config(text="⏸ Pause" if self.is_playing else "▶ Play")
        if self.is_playing:
            self.animate()
            
    def refresh_display(self):
        self.draw_scene(self.current_frame_index)

    def update_from_editor(self):
        self.rebuild_frame_cache() 
        self.draw_scene(self.current_frame_index)

    def animate(self):
        if not self.win.winfo_exists(): return
        
        if not self.cached_frames: 
            self.rebuild_frame_cache()
            if not self.cached_frames: return

        if self.is_playing:
            if self.current_frame_index >= len(self.cached_frames):
                self.current_frame_index = 0

            try:
                self.draw_scene(self.current_frame_index)
            except Exception as e:
                print(f"Render Error: {e}")

            self.win.title(f"Preview - Frame {self.current_frame_index + 1} / {len(self.cached_frames)}")
            
            self.current_frame_index = (self.current_frame_index + 1) % len(self.cached_frames)
            
            speed = self.scale_speed.get()
            self.timer_id = self.win.after(speed, self.animate)

    def draw_scene(self, frame_idx):
        if not self.cache_created or not self.cached_frames: return
        if frame_idx >= len(self.cached_frames): frame_idx = 0
        
        mode = self.var_onion_mode.get()
        current_grid = self.cached_frames[frame_idx]

        max_rows = min(self.app.rows, len(current_grid))
        max_cols = min(self.app.cols, len(current_grid[0])) if max_rows > 0 else 0

        for r in range(self.app.rows):
            for c in range(self.app.cols):
                onion_color = None
                
                if mode == "prev" and len(self.cached_frames) > 1:
                    prev_idx = (frame_idx - 1) % len(self.cached_frames)
                    if r < len(self.cached_frames[prev_idx]) and c < len(self.cached_frames[prev_idx][0]):
                         onion_color = self.cached_frames[prev_idx][r][c]
                
                elif mode == "all":
                    for i, frm in enumerate(self.cached_frames):
                        if i == frame_idx: continue
                        if r < len(frm) and c < len(frm[0]):
                            if frm[r][c] != EMPTY_COLOR:
                                onion_color = frm[r][c]
                                break

                onion_id = self.onion_cache[r][c]
                if onion_color and onion_color != EMPTY_COLOR:
                    self.canvas.itemconfig(onion_id, fill=onion_color, state="normal", stipple="gray50")
                else:
                    self.canvas.itemconfig(onion_id, state="hidden")

                pixel_id = self.pixel_cache[r * self.app.cols + c]
                
                if r < max_rows and c < max_cols:
                    color = current_grid[r][c]
                    if color != EMPTY_COLOR:
                        self.canvas.itemconfig(pixel_id, fill=color, state="normal")
                    else:
                        self.canvas.itemconfig(pixel_id, state="hidden")
                else:
                    self.canvas.itemconfig(pixel_id, state="hidden")

    def close_window(self):
        if self.app.preview_window == self:
            self.app.preview_window = None
            
        if self.timer_id:
            self.win.after_cancel(self.timer_id)
        self.win.destroy()