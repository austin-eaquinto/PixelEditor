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
            tab.commit_selection() 
            
            if 0 <= r < tab.rows and 0 <= c < tab.cols:
                tab.sel_start = (r, c)
                tab.sel_end = (r, c)
                tab.draw_grid_lines()

    def on_drag(self, tab, r, c, event=None):
        if self.mode == "move":
            # --- LAG FIX: USE VISUAL MOVE ---
            if tab.floating_pixels and self.drag_start_ref:
                dr = r - self.drag_start_ref[0]
                dc = c - self.drag_start_ref[1]
                orig_fr, orig_fc = self.drag_orig_offset
                
                new_fr = orig_fr + dr
                new_fc = orig_fc + dc
                
                # Check if we actually moved to a new grid cell before redrawing
                if (new_fr, new_fc) != tab.floating_offset:
                    # Calculate delta for the visual shift
                    delta_r = new_fr - tab.floating_offset[0]
                    delta_c = new_fc - tab.floating_offset[1]
                    
                    tab.visual_move_selection(delta_r, delta_c)
                    tab.floating_offset = (new_fr, new_fc)
                    tab.app.notify_preview()
                
        elif self.mode == "box":
            if tab.sel_start:
                r = max(0, min(tab.rows - 1, r))
                c = max(0, min(tab.cols - 1, c))
                
                tab.sel_end = (r, c)
                tab.draw_grid_lines()

    def on_release(self, tab, event=None):
        self.mode = "none"
        self.drag_start_ref = None
        self.drag_orig_offset = None