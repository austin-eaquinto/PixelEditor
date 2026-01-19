# editor_state.py
from settings import *
from history import HistoryManager

class EditorState:
    """
    Manages the pure data of an Editor Tab: 
    - Grid Colors
    - Selection State (Floating pixels)
    - Undo/Redo History
    """
    def __init__(self, rows, cols):
        self.rows = rows
        self.cols = cols
        
        # Grid Data: 2D Array [row][col]
        self.grid_data = [[EMPTY_COLOR for _ in range(self.cols)] for _ in range(self.rows)]
        
        # History
        self.history_manager = HistoryManager()
        
        # Selection / Floating Layer
        self.sel_start = None
        self.sel_end = None
        self.floating_pixels = None # Dict {(r, c): color}
        self.floating_offset = None # (r, c)
        
        # Symmetry Settings (Data relevant to logic)
        self.mirror_x = False
        self.mirror_y = False

    def save_state(self):
        self.history_manager.push_state(self.grid_data)

    def undo(self):
        return self.history_manager.undo(self.grid_data)

    def redo(self):
        return self.history_manager.redo(self.grid_data)

    def get_selection_bounds(self):
        if not self.sel_start or not self.sel_end: return None
        r1, c1 = self.sel_start
        r2, c2 = self.sel_end
        return (min(r1, r2), min(c1, c2), max(r1, r2), max(c1, c2))

    def point_in_selection(self, r, c):
        """Checks if a point is inside the active selection bounds."""
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

    def get_flattened_data(self):
        """Returns the grid with floating selection merged in (for previews/export)."""
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

    def commit_selection_to_grid(self):
        """Merges floating pixels permanently into grid_data."""
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
            return True
        return False

    def lift_selection(self):
        """Cuts the selected area from the grid into floating_pixels."""
        if self.floating_pixels: return False
        bounds = self.get_selection_bounds()
        if not bounds: return False
        
        self.save_state()
        r1, c1, r2, c2 = bounds
        self.floating_pixels = {}
        self.floating_offset = (r1, c1)
        
        for r in range(r1, r2 + 1):
            for c in range(c1, c2 + 1):
                self.floating_pixels[(r - r1, c - c1)] = self.grid_data[r][c]
                self.grid_data[r][c] = EMPTY_COLOR
        return True

    # --- SELECTION TRANSFORMATIONS ---

    def rotate_selection(self):
        """Rotates the floating selection 90 degrees Clockwise."""
        if not self.floating_pixels: return
        
        # 1. Calculate current bounds
        max_r = max(k[0] for k in self.floating_pixels.keys())
        max_c = max(k[1] for k in self.floating_pixels.keys())
        
        new_pixels = {}
        
        # 2. Rotate Math: (r, c) -> (c, max_r - r)
        # Note: We rotate relative to the selection's own bounding box
        for (r, c), color in self.floating_pixels.items():
            new_r = c
            new_c = max_r - r
            new_pixels[(new_r, new_c)] = color
            
        self.floating_pixels = new_pixels
        
        # Swap dimensions for the selection box
        # The offset (top-left) stays the same for now, or we could center it. 
        # Keeping top-left is standard for pixel editors.

    def flip_selection_h(self):
        """Flips floating selection Horizontally."""
        if not self.floating_pixels: return
        max_c = max(k[1] for k in self.floating_pixels.keys())
        
        new_pixels = {}
        for (r, c), color in self.floating_pixels.items():
            new_pixels[(r, max_c - c)] = color
        self.floating_pixels = new_pixels

    def flip_selection_v(self):
        """Flips floating selection Vertically."""
        if not self.floating_pixels: return
        max_r = max(k[0] for k in self.floating_pixels.keys())
        
        new_pixels = {}
        for (r, c), color in self.floating_pixels.items():
            new_pixels[(max_r - r, c)] = color
        self.floating_pixels = new_pixels

    def resize_selection(self, scale_x, scale_y):
        """
        Resizes the floating selection using Nearest Neighbor.
        scale_x/y are floats (e.g., 2.0 for double size, 0.5 for half).
        """
        if not self.floating_pixels: return
        
        max_r = max(k[0] for k in self.floating_pixels.keys())
        max_c = max(k[1] for k in self.floating_pixels.keys())
        width = max_c + 1
        height = max_r + 1
        
        new_w = int(width * scale_x)
        new_h = int(height * scale_y)
        
        if new_w < 1: new_w = 1
        if new_h < 1: new_h = 1
        
        new_pixels = {}
        
        # Nearest Neighbor Interpolation
        for r in range(new_h):
            for c in range(new_w):
                # Map back to original coordinate space
                orig_r = int(r / scale_y)
                orig_c = int(c / scale_x)
                
                # Clamp (safe-guard)
                orig_r = min(orig_r, height - 1)
                orig_c = min(orig_c, width - 1)
                
                if (orig_r, orig_c) in self.floating_pixels:
                    new_pixels[(r, c)] = self.floating_pixels[(orig_r, orig_c)]
                    
        self.floating_pixels = new_pixels
    
    def lift_complex_selection(self, valid_pixels_set):
        """
        Lifts a specific set of (r,c) tuples into the floating layer.
        Used by the Lasso tool.
        """
        if self.floating_pixels: return False
        if not valid_pixels_set: return False
        
        self.save_state()
        
        # 1. Calculate Bounding Box of the irregular shape
        min_r = min(p[0] for p in valid_pixels_set)
        max_r = max(p[0] for p in valid_pixels_set)
        min_c = min(p[1] for p in valid_pixels_set)
        max_c = max(p[1] for p in valid_pixels_set)
        
        self.floating_pixels = {}
        self.floating_offset = (min_r, min_c)
        
        # 2. Lift ONLY the pixels in the set
        for (r, c) in valid_pixels_set:
            if 0 <= r < self.rows and 0 <= c < self.cols:
                # Store relative to the top-left of the bounding box
                self.floating_pixels[(r - min_r, c - min_c)] = self.grid_data[r][c]
                self.grid_data[r][c] = EMPTY_COLOR
                
        # 3. Set the standard selection box around the irregular shape
        self.sel_start = (min_r, min_c)
        self.sel_end = (max_r, max_c)
        return True