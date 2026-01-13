# tools/bucket.py
from tools.base import Tool
from algorithms import get_connected_pixels

class BucketTool(Tool):
    def on_click(self, tab, r, c, event=None):
        self.app.active_tab().save_state()
        
        target_color = self.app.active_color
        current_color = tab.grid_data[r][c]
        
        if current_color == target_color: return
        
        pixels = get_connected_pixels(tab.grid_data, r, c)
        
        for pr, pc in pixels:
            tab.grid_data[pr][pc] = target_color
            
        tab.draw_grid_lines()
        tab.app.notify_preview()