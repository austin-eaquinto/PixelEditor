# tools/line.py
from tools.base import Tool
from algorithms import get_line_pixels

class LineTool(Tool):
    def __init__(self, app_ref):
        super().__init__(app_ref)
        self.start_pos = None
        self.snapshot_grid = None

    def on_click(self, tab, r, c, event=None):
        # 1. Commit any existing selection
        tab.commit_selection()
        
        # 2. Save History (Undo point)
        tab.save_state()
        
        # 3. Store Starting Position
        self.start_pos = (r, c)
        
        # 4. Take a temporary snapshot of the grid *before* the line
        #    We will use this to "wipe" the preview line while dragging.
        self.snapshot_grid = [row[:] for row in tab.grid_data]
        
        # Draw the single dot
        self.draw_preview_line(tab, r, c)

    def on_drag(self, tab, r, c, event=None):
        if not self.start_pos: return
        self.draw_preview_line(tab, r, c)

    def on_release(self, tab, event=None):
        # Finalize the drawing (already done by the last drag update)
        self.start_pos = None
        self.snapshot_grid = None

    def draw_preview_line(self, tab, end_r, end_c):
        # 1. Restore the grid to how it looked before we started dragging
        #    (This erases the line from the *previous* drag frame)
        if self.snapshot_grid:
            tab.grid_data = [row[:] for row in self.snapshot_grid]
        
        # 2. Calculate the line
        sr, sc = self.start_pos
        pixels = get_line_pixels(sr, sc, end_r, end_c)
        
        # 3. Draw the new line
        color = self.app.active_color
        for r, c in pixels:
            if 0 <= r < tab.rows and 0 <= c < tab.cols:
                tab.grid_data[r][c] = color
        
        # 4. Update UI
        tab.draw_grid_lines()
        tab.app.notify_preview()