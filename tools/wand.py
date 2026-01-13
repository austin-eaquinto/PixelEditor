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
        if tab.floating_pixels and tab.point_in_selection(r, c):
             self.drag_start_ref = (r, c)
             self.drag_orig_offset = tab.floating_offset
             return

        tab.commit_selection()
        
        if not (0 <= r < tab.rows and 0 <= c < tab.cols): return
        if tab.grid_data[r][c] == EMPTY_COLOR: return

        tab.save_state()

        selected_pixels = get_connected_pixels(tab.grid_data, r, c)
        
        if not selected_pixels: return

        min_r = min(p[0] for p in selected_pixels)
        max_r = max(p[0] for p in selected_pixels)
        min_c = min(p[1] for p in selected_pixels)
        max_c = max(p[1] for p in selected_pixels)
        
        tab.floating_pixels = {}
        tab.floating_offset = (min_r, min_c)
        
        for pr, pc in selected_pixels:
            rel_r = pr - min_r
            rel_c = pc - min_c
            tab.floating_pixels[(rel_r, rel_c)] = tab.grid_data[pr][pc]
            tab.grid_data[pr][pc] = EMPTY_COLOR 
            
        tab.sel_start = (min_r, min_c)
        tab.sel_end = (max_r, max_c)
        
        self.drag_start_ref = (r, c)
        self.drag_orig_offset = tab.floating_offset
        tab.draw_grid_lines()

    def on_drag(self, tab, r, c, event=None):
        # --- LAG FIX: USE VISUAL MOVE ---
        if tab.floating_pixels and self.drag_start_ref:
            dr = r - self.drag_start_ref[0]
            dc = c - self.drag_start_ref[1]
            orig_fr, orig_fc = self.drag_orig_offset
            
            new_fr = orig_fr + dr
            new_fc = orig_fc + dc
            
            if (new_fr, new_fc) != tab.floating_offset:
                delta_r = new_fr - tab.floating_offset[0]
                delta_c = new_fc - tab.floating_offset[1]
                
                tab.visual_move_selection(delta_r, delta_c)
                tab.floating_offset = (new_fr, new_fc)
                tab.app.notify_preview()

    def on_release(self, tab, event=None):
        self.drag_start_ref = None
        self.drag_orig_offset = None