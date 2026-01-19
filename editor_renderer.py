# editor_renderer.py
import tkinter as tk
from settings import *

class EditorRenderer:
    """
    Handles all visual aspects of an Editor Tab:
    - Canvas creation
    - Drawing pixels/grid
    - Visual selection box
    """
    def __init__(self, parent_frame, app_ref, pixel_size):
        self.app = app_ref
        self.pixel_size = pixel_size
        self.rects = {} # Cache {(r,c): item_id}
        self.sel_rect_id = None
        
        # UI Setup
        self.v_scroll = tk.Scrollbar(parent_frame, orient=tk.VERTICAL)
        self.h_scroll = tk.Scrollbar(parent_frame, orient=tk.HORIZONTAL)
        self.canvas = tk.Canvas(parent_frame, bg="#cccccc",
                                xscrollcommand=self.h_scroll.set,
                                yscrollcommand=self.v_scroll.set)
        
        self.v_scroll.config(command=self.canvas.yview)
        self.h_scroll.config(command=self.canvas.xview)
        
        self.v_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.h_scroll.pack(side=tk.BOTTOM, fill=tk.X)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    def update_pixel(self, r, c, color):
        """Updates a single pixel's color on the canvas."""
        if (r, c) in self.rects:
            self.canvas.itemconfig(self.rects[(r, c)], fill=color)

    def draw_grid(self, state):
        """Full redraw of the grid based on state."""
        self.canvas.delete("all")
        self.rects = {}
        self.sel_rect_id = None

        width = state.cols * self.pixel_size
        height = state.rows * self.pixel_size
        self.canvas.config(scrollregion=(0, 0, width, height))

        # 1. Base Pixels
        for r in range(state.rows):
            for c in range(state.cols):
                color = state.grid_data[r][c]
                x1, y1 = c * self.pixel_size, r * self.pixel_size
                rect = self.canvas.create_rectangle(x1, y1, x1+self.pixel_size, y1+self.pixel_size, 
                                                    outline="", fill=color)
                self.rects[(r, c)] = rect

        # 2. Floating Pixels
        if state.floating_pixels and state.floating_offset:
            fr, fc = state.floating_offset
            for (lr, lc), color in state.floating_pixels.items():
                if color == EMPTY_COLOR: continue
                ar, ac = fr + lr, fc + lc
                x1, y1 = ac * self.pixel_size, ar * self.pixel_size
                self.canvas.create_rectangle(x1, y1, x1+self.pixel_size, y1+self.pixel_size,
                                             outline="", fill=color, tags="floating")

        # 3. Grid Lines
        if self.app.show_grid:
            grid_color = "#bbbbbb"
            for c in range(state.cols + 1):
                x = c * self.pixel_size
                self.canvas.create_line(x, 0, x, height, fill=grid_color)
            for r in range(state.rows + 1):
                y = r * self.pixel_size
                self.canvas.create_line(0, y, width, y, fill=grid_color)

        # 4. Selection Box
        self.draw_selection_box(state)

    def draw_selection_box(self, state):
        if self.sel_rect_id: self.canvas.delete(self.sel_rect_id)
        
        if state.sel_start and state.sel_end:
            r1, c1, r2, c2 = state.get_selection_bounds()
            
            if state.floating_pixels:
                h = r2 - r1 + 1
                w = c2 - c1 + 1
                fr, fc = state.floating_offset
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

    def move_floating_visuals(self, dr, dc):
        """Efficiently moves the floating layer without a full redraw."""
        dx = dc * self.pixel_size
        dy = dr * self.pixel_size
        self.canvas.move("floating", dx, dy)
        self.canvas.move("ui", dx, dy)
    
    def update_selection_box_coords(self, r1, c1, r2, c2):
        """Moves the selection box visuals without redrawing the whole grid."""
        # 1. Calculate new coordinates
        if self.app.active_tab().state.floating_pixels:
            # If we have a floating selection, it works differently (offset based)
            # This optimization is mainly for the initial BOX creation
            return 
            
        x1 = c1 * self.pixel_size
        y1 = r1 * self.pixel_size
        x2 = (c2 + 1) * self.pixel_size
        y2 = (r2 + 1) * self.pixel_size

        # 2. Update the existing rectangle or create it
        if self.sel_rect_id:
            self.canvas.coords(self.sel_rect_id, x1, y1, x2, y2)
            self.canvas.tag_raise(self.sel_rect_id) # Keep it on top
        else:
            # Create it if it doesn't exist
            self.sel_rect_id = self.canvas.create_rectangle(x1, y1, x2, y2, 
                                                            outline="black", dash=(4, 4), width=2, tags="ui")