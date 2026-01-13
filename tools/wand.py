# tools/wand.py
from tools.base import Tool
from settings import EMPTY_COLOR
from algorithms import get_connected_pixels

class MagicWandTool(Tool):
    def __init__(self, app_ref):
        super().__init__(app_ref)
        self.drag_start_ref = None
        self.drag_orig_offset = None

    def on_click(self, tab, r, c, event=None):
        # 1. Always commit previous selection first
        tab.commit_selection()
        
        # 2. Check bounds
        if not (0 <= r < tab.rows and 0 <= c < tab.cols):
            return

        # 3. Save State (History)
        tab.save_state()

        # 4. Perform Magic Wand Selection (BFS)
        selected_pixels = get_connected_pixels(tab.grid_data, r, c)
        
        if not selected_pixels: 
            return

        # 5. Calculate Bounds
        min_r = min(p[0] for p in selected_pixels)
        max_r = max(p[0] for p in selected_pixels)
        min_c = min(p[1] for p in selected_pixels)
        max_c = max(p[1] for p in selected_pixels)
        
        # 6. Lift to Floating Layer
        tab.floating_pixels = {}
        tab.floating_offset = (min_r, min_c)
        
        for pr, pc in selected_pixels:
            rel_r = pr - min_r
            rel_c = pc - min_c
            tab.floating_pixels[(rel_r, rel_c)] = tab.grid_data[pr][pc]
            tab.grid_data[pr][pc] = EMPTY_COLOR 
            
        tab.sel_start = (min_r, min_c)
        tab.sel_end = (max_r, max_c)
        
        # 7. Initialize Immediate Dragging
        self.drag_start_ref = (r, c)
        self.drag_orig_offset = tab.floating_offset

        # 8. Update UI
        tab.draw_grid_lines()

    def on_drag(self, tab, r, c, event=None):
        # Handle moving the floating pixels
        if tab.floating_pixels and self.drag_start_ref:
            dr = r - self.drag_start_ref[0]
            dc = c - self.drag_start_ref[1]
            orig_fr, orig_fc = self.drag_orig_offset
            
            tab.floating_offset = (orig_fr + dr, orig_fc + dc)
            tab.draw_grid_lines()
            tab.app.notify_preview()

    def on_release(self, tab, event=None):
        self.drag_start_ref = None
        self.drag_orig_offset = None