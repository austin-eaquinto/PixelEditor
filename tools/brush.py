# tools/brush.py
from tools.base import Tool

class BrushTool(Tool):
    def __init__(self, app_ref):
        super().__init__(app_ref)
        self.prev_pos = None

    def on_click(self, tab, r, c, event=None):
        self.app.active_tab().save_state()
        self.paint(tab, r, c)
        self.prev_pos = (r, c)

    def on_drag(self, tab, r, c, event=None):
        # (Same interpolation logic as before, just calling self.paint)
        if self.prev_pos:
            pr, pc = self.prev_pos
            if (pr, pc) != (r, c):
                from algorithms import get_line_pixels
                pixels = get_line_pixels(pr, pc, r, c)
                for lr, lc in pixels:
                    self.paint(tab, lr, lc)
        else:
            self.paint(tab, r, c)
        self.prev_pos = (r, c)

    def on_release(self, tab, event=None):
        self.prev_pos = None

    def paint(self, tab, r, c):
        # Refactored to use the Tab's central method
        tab.paint_pixel(r, c, self.app.active_color)
        tab.app.notify_preview()