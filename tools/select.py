# tools/select.py
from tools.base import Tool
from settings import EMPTY_COLOR

class SelectTool(Tool):
    def __init__(self, app_ref):
        super().__init__(app_ref)
        self.drag_start_ref = None
        self.drag_orig_offset = None
        self.mode = "none" # "box" or "move"

    def on_click(self, tab, r, c, event=None):
        # Check if clicking inside an existing selection
        if tab.point_in_selection(r, c):
            # MODE: MOVE EXISTING PIXELS
            self.mode = "move"
            if not tab.floating_pixels:
                tab.lift_selection_to_float()
            
            self.drag_start_ref = (r, c)
            self.drag_orig_offset = tab.floating_offset
            
        else:
            # MODE: NEW SELECTION BOX
            self.mode = "box"
            tab.commit_selection() # Clear old one
            
            if 0 <= r < tab.rows and 0 <= c < tab.cols:
                tab.sel_start = (r, c)
                tab.sel_end = (r, c)
                tab.draw_grid_lines()

    def on_drag(self, tab, r, c, event=None):
        if self.mode == "move":
            # Moving pixels
            if tab.floating_pixels and self.drag_start_ref:
                dr = r - self.drag_start_ref[0]
                dc = c - self.drag_start_ref[1]
                orig_fr, orig_fc = self.drag_orig_offset
                
                tab.floating_offset = (orig_fr + dr, orig_fc + dc)
                tab.draw_grid_lines()
                tab.app.notify_preview()
                
        elif self.mode == "box":
            # Dragging selection box
            if tab.sel_start:
                # Constrain to grid
                r = max(0, min(tab.rows - 1, r))
                c = max(0, min(tab.cols - 1, c))
                
                tab.sel_end = (r, c)
                tab.draw_grid_lines()

    def on_release(self, tab, event=None):
        self.mode = "none"
        self.drag_start_ref = None
        self.drag_orig_offset = None