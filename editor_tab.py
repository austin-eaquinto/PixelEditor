# editor_tab.py
import tkinter as tk
from settings import *

class EditorTab:
    """Represents a single Tab/Frame in the animation."""
    def __init__(self, notebook, app_ref, rows, cols, pixel_size, name="Frame"):
        self.app = app_ref 
        self.rows = rows
        self.cols = cols
        self.pixel_size = pixel_size
        
        # Data Structures
        self.grid_data = [[EMPTY_COLOR for _ in range(self.cols)] for _ in range(self.rows)]
        self.history = []
        self.redo_stack = []
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
        self.canvas.bind("<Button-3>", self.start_eraser)
        self.canvas.bind("<B3-Motion>", self.drag_eraser)
        
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

        # 2. Draw Floating Pixels
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

        # 4. Draw Selection Box
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
        
        # FIX: Safer Empty Check
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

    def save_state(self):
        if not self.grid_data or not self.grid_data[0]: return 
        
        state = [row[:] for row in self.grid_data]
        self.history.append(state)
        if len(self.history) > 50: self.history.pop(0)
        self.redo_stack.clear()
        
    def perform_undo(self):
        if self.history:
            potential_state = self.history[-1]
            if not potential_state or not potential_state[0]:
                self.history.pop()
                return

            self.redo_stack.append([row[:] for row in self.grid_data])
            self.grid_data = self.history.pop()
            
            self.rows = len(self.grid_data)
            self.cols = len(self.grid_data[0]) if self.rows > 0 else 0
            
            self.sel_start = None
            self.sel_end = None
            self.floating_pixels = None
            self.draw_grid_lines()
            self.app.notify_preview()

    def perform_redo(self):
        if self.redo_stack:
            self.history.append([row[:] for row in self.grid_data])
            self.grid_data = self.redo_stack.pop()
            self.rows = len(self.grid_data)
            self.cols = len(self.grid_data[0]) if self.rows > 0 else 0
            self.draw_grid_lines()
            self.app.notify_preview()

    # --- NEW HELPER FOR PREVIEW ---
    def get_flattened_data(self):
        """Returns the grid with any active selection overlayed."""
        # 1. If no floating pixels, return raw grid
        if not self.floating_pixels:
            return self.grid_data
        
        # 2. Deep copy to avoid messing up real data
        temp = [row[:] for row in self.grid_data]
        
        # 3. Stamp floating pixels onto the temp copy
        if self.floating_offset:
            fr, fc = self.floating_offset
            for (lr, lc), color in self.floating_pixels.items():
                r, c = fr + lr, fc + lc
                if 0 <= r < self.rows and 0 <= c < self.cols:
                    if color != EMPTY_COLOR:
                        temp[r][c] = color
        return temp

    def on_click(self, event):
        canvas_x = self.canvas.canvasx(event.x)
        canvas_y = self.canvas.canvasy(event.y)
        c = int(canvas_x // self.pixel_size)
        r = int(canvas_y // self.pixel_size)
        
        if self.app.active_tool == "select":
            if self.point_in_selection(r, c):
                if not self.floating_pixels:
                    self.lift_selection_to_float()
                self.drag_start_ref = (r, c)
                self.drag_orig_offset = self.floating_offset
            else:
                self.commit_selection() 
                if 0 <= r < self.rows and 0 <= c < self.cols:
                    self.sel_start = (r, c)
                    self.sel_end = (r, c)
                    self.draw_grid_lines()
        elif self.app.active_tool == "grab": 
            self.canvas.scan_mark(event.x, event.y)
        elif self.app.active_tool == "bucket":
            self.commit_selection()
            if 0 <= r < self.rows and 0 <= c < self.cols:
                self.save_state()
                self.flood_fill(r, c, self.app.active_color)
                self.app.notify_preview()
        else:
            self.commit_selection()
            self.save_state()
            self.paint(event)
            self.app.notify_preview()

    def on_drag(self, event):
        canvas_x = self.canvas.canvasx(event.x)
        canvas_y = self.canvas.canvasy(event.y)
        c = int(canvas_x // self.pixel_size)
        r = int(canvas_y // self.pixel_size)

        if self.app.active_tool == "select":
            if self.floating_pixels and hasattr(self, 'drag_start_ref'):
                dr = r - self.drag_start_ref[0]
                dc = c - self.drag_start_ref[1]
                orig_fr, orig_fc = self.drag_orig_offset
                self.floating_offset = (orig_fr + dr, orig_fc + dc)
                self.draw_grid_lines()
                self.app.notify_preview()
            elif self.sel_start:
                r = max(0, min(self.rows-1, r))
                c = max(0, min(self.cols-1, c))
                self.sel_end = (r, c)
                self.draw_grid_lines()
        elif self.app.active_tool == "grab": 
            self.canvas.scan_dragto(event.x, event.y, gain=1)
        else: 
            self.paint(event)
            self.app.notify_preview()

    def on_release(self, event):
        if hasattr(self, 'drag_start_ref'):
            del self.drag_start_ref

    def paint(self, event, specific_color=None):
        canvas_x = self.canvas.canvasx(event.x)
        canvas_y = self.canvas.canvasy(event.y)
        col = int(canvas_x // self.pixel_size)
        row = int(canvas_y // self.pixel_size)

        if 0 <= row < self.rows and 0 <= col < self.cols:
            target = specific_color if specific_color else self.app.active_color
            if self.grid_data[row][col] != target:
                self.grid_data[row][col] = target
                if (row, col) in self.rects:
                    self.canvas.itemconfig(self.rects[(row, col)], fill=target)

    def flood_fill(self, start_r, start_c, target_color):
        original_color = self.grid_data[start_r][start_c]
        if original_color == target_color: return
        queue = [(start_r, start_c)]
        visited = set()
        while queue:
            r, c = queue.pop(0)
            if (r, c) in visited: continue
            visited.add((r, c))
            if self.grid_data[r][c] == original_color:
                self.grid_data[r][c] = target_color
                if r > 0: queue.append((r-1, c))
                if r < self.rows - 1: queue.append((r+1, c))
                if c > 0: queue.append((r, c-1))
                if c < self.cols - 1: queue.append((r, c+1))
        self.draw_grid_lines()

    def start_eraser(self, event):
        self.commit_selection()
        self.save_state()
        self.paint(event, EMPTY_COLOR)
        self.app.notify_preview()
    
    def drag_eraser(self, event):
        self.paint(event, EMPTY_COLOR)
        self.app.notify_preview()

    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")

    def _on_shift_mousewheel(self, event):
        self.canvas.xview_scroll(int(-1*(event.delta/120)), "units")