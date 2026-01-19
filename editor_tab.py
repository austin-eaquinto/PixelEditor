# editor_tab.py
import tkinter as tk
from settings import *
from algorithms import get_line_pixels

# NEW IMPORTS
from editor_state import EditorState
from editor_renderer import EditorRenderer

class EditorTab:
    """
    Controller class that coordinates State (Data) and Renderer (Visuals).
    Maintains compatibility with existing Tools and Main logic.
    """
    def __init__(self, notebook, app_ref, rows, cols, pixel_size, name="Frame"):
        self.app = app_ref
        self.frame = tk.Frame(notebook)
        
        # 1. Initialize Components
        self.state = EditorState(rows, cols)
        self.renderer = EditorRenderer(self.frame, app_ref, pixel_size)
        
        # 2. Input State (Controller logic)
        self.prev_right_click_pos = None

        # 3. Setup Bindings
        self._bind_events()

        # 4. Initial Draw
        self.draw_grid_lines()

    # --- PROXY PROPERTIES (Backward Compatibility) ---
    # These ensure main.py and tools don't break.
    
    @property
    def grid_data(self): return self.state.grid_data
    @grid_data.setter
    def grid_data(self, val): self.state.grid_data = val

    @property
    def rows(self): return self.state.rows
    @rows.setter
    def rows(self, val): self.state.rows = val

    @property
    def cols(self): return self.state.cols
    @cols.setter
    def cols(self, val): self.state.cols = val

    @property
    def pixel_size(self): return self.renderer.pixel_size
    @pixel_size.setter
    def pixel_size(self, val): self.renderer.pixel_size = val

    @property
    def canvas(self): return self.renderer.canvas
    
    @property
    def rects(self): return self.renderer.rects

    @property
    def sel_start(self): return self.state.sel_start
    @sel_start.setter
    def sel_start(self, val): self.state.sel_start = val

    @property
    def sel_end(self): return self.state.sel_end
    @sel_end.setter
    def sel_end(self, val): self.state.sel_end = val
    
    @property
    def floating_pixels(self): return self.state.floating_pixels
    @floating_pixels.setter
    def floating_pixels(self, val): self.state.floating_pixels = val
    
    @property
    def floating_offset(self): return self.state.floating_offset
    @floating_offset.setter
    def floating_offset(self, val): self.state.floating_offset = val

    @property
    def mirror_x(self): return self.state.mirror_x
    @mirror_x.setter
    def mirror_x(self, val): self.state.mirror_x = val
    
    @property
    def mirror_y(self): return self.state.mirror_y
    @mirror_y.setter
    def mirror_y(self, val): self.state.mirror_y = val

    # --- DELEGATED METHODS ---

    def draw_grid_lines(self):
        self.renderer.draw_grid(self.state)

    def visual_move_selection(self, dr, dc):
        self.renderer.move_floating_visuals(dr, dc)

    def get_selection_bounds(self):
        return self.state.get_selection_bounds()

    def point_in_selection(self, r, c):
        return self.state.point_in_selection(r, c)

    def get_flattened_data(self):
        return self.state.get_flattened_data()

    def save_state(self):
        self.state.save_state()

    # --- LOGIC ACTIONS (Controller) ---

    def commit_selection(self):
        """Commits floating pixels to data and redraws."""
        if self.state.commit_selection_to_grid():
            self.app.notify_preview()
            
        self.sel_start = None
        self.sel_end = None
        self.draw_grid_lines()

    def lift_selection_to_float(self):
        """Lifts selection from data to floating and redraws."""
        if self.state.lift_selection():
            self.draw_grid_lines()

    def copy_to_clipboard(self):
        if self.state.floating_pixels:
            self.app.clipboard = self.state.floating_pixels.copy()
            return True
        bounds = self.get_selection_bounds()
        if not bounds: return False
        r1, c1, r2, c2 = bounds
        data = {}
        for r in range(r1, r2 + 1):
            for c in range(c1, c2 + 1):
                 data[(r - r1, c - c1)] = self.state.grid_data[r][c]
        self.app.clipboard = data
        return True

    def paste_from_clipboard(self, clipboard_data):
        if not clipboard_data: return
        self.commit_selection()
        
        max_r = max(k[0] for k in clipboard_data.keys())
        max_c = max(k[1] for k in clipboard_data.keys())
        self.state.sel_start = (0, 0)
        self.state.sel_end = (max_r, max_c)
        self.state.floating_pixels = clipboard_data.copy()
        self.state.floating_offset = (0, 0)
        self.draw_grid_lines()
        self.app.notify_preview()

    def move_selection_by_offset(self, dr, dc):
        if not self.state.sel_start: return
        if not self.state.floating_pixels: self.lift_selection_to_float()
        curr_r, curr_c = self.state.floating_offset
        self.state.floating_offset = (curr_r + dr, curr_c + dc)
        self.draw_grid_lines()
        self.app.notify_preview()

    def perform_undo(self):
        new_state = self.state.undo() # No arguments passed
        if new_state:
            self.state.grid_data = new_state
            # We ONLY restore dimensions (because that is data)
            # We do NOT restore pixel_size (Zoom), so it persists!
            self.state.rows = len(new_state)
            self.state.cols = len(new_state[0]) if self.state.rows > 0 else 0
            
            self.state.sel_start = None
            self.state.sel_end = None
            self.state.floating_pixels = None
            self.draw_grid_lines()
            self.app.notify_preview()

    def perform_redo(self):
        new_state = self.state.redo() # No arguments passed
        if new_state:
            self.state.grid_data = new_state
            self.state.rows = len(new_state)
            self.state.cols = len(new_state[0]) if self.state.rows > 0 else 0
            
            self.draw_grid_lines()
            self.app.notify_preview()

    # --- PAINT LOGIC (The most important Controller Function) ---
    def paint_pixel(self, r, c, color):
        """
        Coordinates State update and Renderer update.
        Handles Symmetry logic here (Controller responsibility).
        """
        # 1. Paint Primary
        self._paint_single(r, c, color)

        # 2. Mirror X
        if self.state.mirror_x:
            self._paint_single(r, (self.cols - 1) - c, color)
            
        # 3. Mirror Y
        if self.state.mirror_y:
            self._paint_single((self.rows - 1) - r, c, color)
            
        # 4. Mirror XY
        if self.state.mirror_x and self.state.mirror_y:
            self._paint_single((self.rows - 1) - r, (self.cols - 1) - c, color)

    def _paint_single(self, r, c, color):
        """Helper to update both data and view for one cell."""
        if 0 <= r < self.rows and 0 <= c < self.cols:
            if self.state.grid_data[r][c] != color:
                self.state.grid_data[r][c] = color
                self.renderer.update_pixel(r, c, color)

    # --- INPUT BINDINGS ---
    def _bind_events(self):
        c = self.renderer.canvas
        c.bind("<Button-1>", self.on_click)      
        c.bind("<B1-Motion>", self.on_drag) 
        c.bind("<ButtonRelease-1>", self.on_release)    
        c.bind("<Button-3>", self.start_eraser_override)
        c.bind("<B3-Motion>", self.drag_eraser_override)
        c.bind("<ButtonRelease-3>", self.stop_eraser_override)
        c.bind("<MouseWheel>", self._on_mousewheel)
        c.bind("<Shift-MouseWheel>", self._on_shift_mousewheel)

    # --- EVENT HANDLERS (Delegates) ---
    def on_click(self, event):
        canvas_x = self.renderer.canvas.canvasx(event.x)
        canvas_y = self.renderer.canvas.canvasy(event.y)
        c = int(canvas_x // self.pixel_size)
        r = int(canvas_y // self.pixel_size)
        if self.app.active_tool:
            self.app.active_tool.on_click(self, r, c, event)

    def on_drag(self, event):
        canvas_x = self.renderer.canvas.canvasx(event.x)
        canvas_y = self.renderer.canvas.canvasy(event.y)
        c = int(canvas_x // self.pixel_size)
        r = int(canvas_y // self.pixel_size)
        if self.app.active_tool:
            self.app.active_tool.on_drag(self, r, c, event)

    def on_release(self, event):
        if self.app.active_tool:
            self.app.active_tool.on_release(self, event)

    def start_eraser_override(self, event):
        self.commit_selection()
        self.save_state()
        canvas_x = self.renderer.canvas.canvasx(event.x)
        canvas_y = self.renderer.canvas.canvasy(event.y)
        c = int(canvas_x // self.pixel_size)
        r = int(canvas_y // self.pixel_size)
        self._manual_erase(r, c)
        self.prev_right_click_pos = (r, c)

    def drag_eraser_override(self, event):
        canvas_x = self.renderer.canvas.canvasx(event.x)
        canvas_y = self.renderer.canvas.canvasy(event.y)
        c = int(canvas_x // self.pixel_size)
        r = int(canvas_y // self.pixel_size)
        if self.prev_right_click_pos:
            pr, pc = self.prev_right_click_pos
            if (pr, pc) != (r, c):
                pixels = get_line_pixels(pr, pc, r, c)
                for lr, lc in pixels: self._manual_erase(lr, lc)
        else:
            self._manual_erase(r, c)
        self.prev_right_click_pos = (r, c)

    def stop_eraser_override(self, event):
        self.prev_right_click_pos = None

    def _manual_erase(self, r, c):
        self.paint_pixel(r, c, EMPTY_COLOR)
        self.app.notify_preview()

    def _on_mousewheel(self, event):
        self.renderer.canvas.yview_scroll(int(-1*(event.delta/120)), "units")

    def _on_shift_mousewheel(self, event):
        self.renderer.canvas.xview_scroll(int(-1*(event.delta/120)), "units")
    
    def fast_update_selection(self, r, c):
        if self.state.sel_start:
            r1, c1 = self.state.sel_start
            # Normalize bounds
            min_r, max_r = min(r1, r), max(r1, r)
            min_c, max_c = min(c1, c), max(c1, c)
            self.renderer.update_selection_box_coords(min_r, min_c, max_r, max_c)
    
    def apply_transformation(self, type_name, **kwargs):
        """Applies a transform and updates the UI."""
        if not self.state.floating_pixels: return
        
        self.save_state() # Save before transforming
        
        if type_name == "rotate":
            self.state.rotate_selection()
        elif type_name == "flip_h":
            self.state.flip_selection_h()
        elif type_name == "flip_v":
            self.state.flip_selection_v()
        elif type_name == "resize":
            self.state.resize_selection(kwargs.get("sx", 1.0), kwargs.get("sy", 1.0))
            
        # Recalculate selection bounds based on new shape
        max_r = max(k[0] for k in self.state.floating_pixels.keys())
        max_c = max(k[1] for k in self.state.floating_pixels.keys())
        
        # Keep the start (top-left) where it is
        start_r, start_c = self.state.floating_offset
        self.state.sel_start = (start_r, start_c)
        self.state.sel_end = (start_r + max_r, start_c + max_c)
        
        self.draw_grid_lines()
        self.app.notify_preview()