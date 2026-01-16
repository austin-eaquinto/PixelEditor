# editor_tab.py
import tkinter as tk
from settings import *
from history import HistoryManager
from algorithms import get_line_pixels

class EditorTab:
    """Represents a single Tab/Frame in the animation."""
    def __init__(self, notebook, app_ref, rows, cols, pixel_size, name="Frame"):
        self.app = app_ref 
        self.rows = rows
        self.cols = cols
        self.pixel_size = pixel_size
        self.prev_right_click_pos = None

        # --- SYMMETRY STATE ---
        self.mirror_x = False
        self.mirror_y = False
        
        # Data Structures
        self.grid_data = [[EMPTY_COLOR for _ in range(self.cols)] for _ in range(self.rows)]
        
        self.history_manager = HistoryManager() 

        self.rects = {} 

        # --- SELECTION STATE ---
        self.sel_start = None 
        self.sel_end = None    
        self.sel_rect_id = None
        
        # Floating Layer
        self.floating_pixels = None 
        self.floating_offset = None 

        # UI Elements
        self.frame = tk.Frame(notebook)
        
        self.v_scroll = tk.Scrollbar(self.frame, orient=tk.VERTICAL)
        self.h_scroll = tk.Scrollbar(self.frame, orient=tk.HORIZONTAL)
        self.canvas = tk.Canvas(self.frame, bg="#cccccc",
                                xscrollcommand=self.h_scroll.set,
                                yscrollcommand=self.v_scroll.set)
        
        self.v_scroll.config(command=self.canvas.yview)
        self.h_scroll.config(command=self.canvas.xview)
        
        self.v_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.h_scroll.pack(side=tk.BOTTOM, fill=tk.X)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Bindings
        self.canvas.bind("<Button-1>", self.on_click)      
        self.canvas.bind("<B1-Motion>", self.on_drag) 
        self.canvas.bind("<ButtonRelease-1>", self.on_release)    
        self.canvas.bind("<Button-3>", self.start_eraser_override)
        self.canvas.bind("<B3-Motion>", self.drag_eraser_override)
        self.canvas.bind("<ButtonRelease-3>", self.stop_eraser_override)
        
        self.canvas.bind("<MouseWheel>", self._on_mousewheel)
        self.canvas.bind("<Shift-MouseWheel>", self._on_shift_mousewheel)

        self.draw_grid_lines()

    def draw_grid_lines(self):
        self.canvas.delete("all") 
        self.rects = {} 
        self.sel_rect_id = None

        width = self.cols * self.pixel_size
        height = self.rows * self.pixel_size
        self.canvas.config(scrollregion=(0, 0, width, height))
        
        # 1. Draw Base Pixels
        for r in range(self.rows):
            for c in range(self.cols):
                if r >= len(self.grid_data) or c >= len(self.grid_data[0]): continue
                color = self.grid_data[r][c]
                x1, y1 = c * self.pixel_size, r * self.pixel_size
                rect = self.canvas.create_rectangle(x1, y1, x1+self.pixel_size, y1+self.pixel_size, 
                                                    outline="", fill=color)
                self.rects[(r, c)] = rect

        # 2. Draw Floating Pixels (Tag them "floating")
        if self.floating_pixels and self.floating_offset:
            fr, fc = self.floating_offset
            for (lr, lc), color in self.floating_pixels.items():
                if color == EMPTY_COLOR: continue
                ar, ac = fr + lr, fc + lc
                x1, y1 = ac * self.pixel_size, ar * self.pixel_size
                self.canvas.create_rectangle(x1, y1, x1+self.pixel_size, y1+self.pixel_size,
                                             outline="", fill=color, tags="floating")

        # 3. Draw Grid Lines
        if self.app.show_grid:
            grid_color = "#bbbbbb"
            for c in range(self.cols + 1):
                x = c * self.pixel_size
                self.canvas.create_line(x, 0, x, height, fill=grid_color)
            for r in range(self.rows + 1):
                y = r * self.pixel_size
                self.canvas.create_line(0, y, width, y, fill=grid_color)

        # 4. Draw Selection Box (Tag it "ui")
        if self.sel_start and self.sel_end:
            r1, c1, r2, c2 = self.get_selection_bounds()
            if self.floating_pixels:
                h = r2 - r1 + 1
                w = c2 - c1 + 1
                fr, fc = self.floating_offset
                x1 = fc * self.pixel_size
                y1 = fr * self.pixel_size
                x2 = (fc + w) * self.pixel_size
                y2 = (fr + h) * self.pixel_size
            else:
                x1 = c1 * self.pixel_size
                y1 = r1 * self.pixel_size
                x2 = (c2 + 1) * self.pixel_size
                y2 = (r2 + 1) * self.pixel_size

            self.sel_rect_id = self.canvas.create_rectangle(x1, y1, x2, y2, 
                                                            outline="black", dash=(4, 4), width=2, tags="ui")

    def visual_move_selection(self, dr, dc):
        """
        Moves the floating layer and selection box instantly using canvas.move
        instead of redrawing the entire grid.
        """
        if not self.floating_pixels: return
        
        # Convert grid delta to pixel delta
        dx = dc * self.pixel_size
        dy = dr * self.pixel_size
        
        # Move objects tagged "floating" (the pixels) and "ui" (the selection box)
        self.canvas.move("floating", dx, dy)
        self.canvas.move("ui", dx, dy)

    def get_selection_bounds(self):
        if not self.sel_start or not self.sel_end: return None
        r1, c1 = self.sel_start
        r2, c2 = self.sel_end
        return (min(r1, r2), min(c1, c2), max(r1, r2), max(c1, c2))

    def point_in_selection(self, r, c):
        if self.floating_pixels and self.floating_offset:
             bounds = self.get_selection_bounds()
             if not bounds: return False
             orig_r1, orig_c1, orig_r2, orig_c2 = bounds
             h, w = orig_r2 - orig_r1, orig_c2 - orig_c1
             fr, fc = self.floating_offset
             return (fr <= r <= fr + h) and (fc <= c <= fc + w)
        bounds = self.get_selection_bounds()
        if not bounds: return False
        r1, c1, r2, c2 = bounds
        return (r1 <= r <= r2) and (c1 <= c <= c2)

    def commit_selection(self):
        if self.floating_pixels and self.floating_offset:
            self.save_state()
            fr, fc = self.floating_offset
            for (lr, lc), color in self.floating_pixels.items():
                ar, ac = fr + lr, fc + lc
                if 0 <= ar < self.rows and 0 <= ac < self.cols:
                    if color != EMPTY_COLOR:
                        self.grid_data[ar][ac] = color
            self.floating_pixels = None
            self.floating_offset = None
            self.app.notify_preview()
            
        self.sel_start = None
        self.sel_end = None
        self.draw_grid_lines()

    def lift_selection_to_float(self):
        if self.floating_pixels: return 
        bounds = self.get_selection_bounds()
        if not bounds: return
        self.save_state()
        r1, c1, r2, c2 = bounds
        self.floating_pixels = {}
        self.floating_offset = (r1, c1)
        for r in range(r1, r2 + 1):
            for c in range(c1, c2 + 1):
                self.floating_pixels[(r - r1, c - c1)] = self.grid_data[r][c]
                self.grid_data[r][c] = EMPTY_COLOR
        self.draw_grid_lines()

    def copy_to_clipboard(self):
        if self.floating_pixels:
            self.app.clipboard = self.floating_pixels.copy()
            return True
        bounds = self.get_selection_bounds()
        if not bounds: return False
        r1, c1, r2, c2 = bounds
        data = {}
        for r in range(r1, r2 + 1):
            for c in range(c1, c2 + 1):
                 data[(r - r1, c - c1)] = self.grid_data[r][c]
        self.app.clipboard = data
        return True

    def paste_from_clipboard(self, clipboard_data):
        if not clipboard_data: return
        self.commit_selection()
        if not clipboard_data: return
        max_r = max(k[0] for k in clipboard_data.keys())
        max_c = max(k[1] for k in clipboard_data.keys())
        self.sel_start = (0, 0)
        self.sel_end = (max_r, max_c)
        self.floating_pixels = clipboard_data.copy()
        self.floating_offset = (0, 0)
        self.draw_grid_lines()
        self.app.notify_preview()

    def move_selection_by_offset(self, dr, dc):
        if not self.sel_start: return
        if not self.floating_pixels: self.lift_selection_to_float()
        curr_r, curr_c = self.floating_offset
        self.floating_offset = (curr_r + dr, curr_c + dc)
        self.draw_grid_lines()
        self.app.notify_preview()

    # --- HISTORY METHODS ---
    def save_state(self):
        self.history_manager.push_state(self.grid_data)
        
    def perform_undo(self):
        new_state = self.history_manager.undo(self.grid_data)
        if new_state:
            self.grid_data = new_state
            self.rows = len(self.grid_data)
            self.cols = len(self.grid_data[0]) if self.rows > 0 else 0
            self.sel_start = None
            self.sel_end = None
            self.floating_pixels = None
            self.draw_grid_lines()
            self.app.notify_preview()

    def perform_redo(self):
        new_state = self.history_manager.redo(self.grid_data)
        if new_state:
            self.grid_data = new_state
            self.rows = len(self.grid_data)
            self.cols = len(self.grid_data[0]) if self.rows > 0 else 0
            self.draw_grid_lines()
            self.app.notify_preview()

    def get_flattened_data(self):
        """Returns the grid with any active selection overlayed."""
        if not self.floating_pixels:
            return self.grid_data
        
        temp = [row[:] for row in self.grid_data]
        
        if self.floating_offset:
            fr, fc = self.floating_offset
            for (lr, lc), color in self.floating_pixels.items():
                r, c = fr + lr, fc + lc
                if 0 <= r < self.rows and 0 <= c < self.cols:
                    if color != EMPTY_COLOR:
                        temp[r][c] = color
        return temp

    # --- DELEGATED EVENTS ---
    def on_click(self, event):
        canvas_x = self.canvas.canvasx(event.x)
        canvas_y = self.canvas.canvasy(event.y)
        c = int(canvas_x // self.pixel_size)
        r = int(canvas_y // self.pixel_size)
        if self.app.active_tool:
            self.app.active_tool.on_click(self, r, c, event)

    def on_drag(self, event):
        canvas_x = self.canvas.canvasx(event.x)
        canvas_y = self.canvas.canvasy(event.y)
        c = int(canvas_x // self.pixel_size)
        r = int(canvas_y // self.pixel_size)
        if self.app.active_tool:
            self.app.active_tool.on_drag(self, r, c, event)

    def on_release(self, event):
        if self.app.active_tool:
            self.app.active_tool.on_release(self, event)

    # --- RIGHT CLICK OVERRIDES ---
    def start_eraser_override(self, event):
        self.commit_selection()
        self.save_state()
        
        # Calculate grid position
        canvas_x = self.canvas.canvasx(event.x)
        canvas_y = self.canvas.canvasy(event.y)
        c = int(canvas_x // self.pixel_size)
        r = int(canvas_y // self.pixel_size)
        
        # Erase and initialize previous position
        self._manual_erase(r, c)
        self.prev_right_click_pos = (r, c)
    
    def drag_eraser_override(self, event):
        canvas_x = self.canvas.canvasx(event.x)
        canvas_y = self.canvas.canvasy(event.y)
        c = int(canvas_x // self.pixel_size)
        r = int(canvas_y // self.pixel_size)

        # Interpolate line if we have a previous position
        if self.prev_right_click_pos:
            pr, pc = self.prev_right_click_pos
            if (pr, pc) != (r, c):
                pixels = get_line_pixels(pr, pc, r, c)
                for lr, lc in pixels:
                    self._manual_erase(lr, lc)
        else:
            self._manual_erase(r, c)
            
        self.prev_right_click_pos = (r, c)

    def stop_eraser_override(self, event):
        self.prev_right_click_pos = None

    def _manual_erase(self, r, c):
        # Forward to the new central method
        self.paint_pixel(r, c, EMPTY_COLOR)
        self.app.notify_preview()

    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")

    def _on_shift_mousewheel(self, event):
        self.canvas.xview_scroll(int(-1*(event.delta/120)), "units")
    
    def paint_pixel(self, r, c, color):
        """
        Central method to paint a pixel. 
        Handles Bounds Checking, Visual Updates, and Symmetry.
        """
        # 1. Paint the primary pixel
        self._set_single_pixel(r, c, color)

        # 2. Handle Mirror X
        if self.mirror_x:
            mirror_c = (self.cols - 1) - c
            self._set_single_pixel(r, mirror_c, color)
            
        # 3. Handle Mirror Y
        if self.mirror_y:
            mirror_r = (self.rows - 1) - r
            self._set_single_pixel(mirror_r, c, color)
            
        # 4. Handle Mirror X + Y (The diagonal corner)
        if self.mirror_x and self.mirror_y:
            mirror_c = (self.cols - 1) - c
            mirror_r = (self.rows - 1) - r
            self._set_single_pixel(mirror_r, mirror_c, color)

    def _set_single_pixel(self, r, c, color):
        """Internal helper to actually set data and canvas."""
        if 0 <= r < self.rows and 0 <= c < self.cols:
            if self.grid_data[r][c] != color:
                self.grid_data[r][c] = color
                if (r, c) in self.rects:
                    self.canvas.itemconfig(self.rects[(r, c)], fill=color)