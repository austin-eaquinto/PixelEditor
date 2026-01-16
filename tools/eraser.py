# tools/eraser.py
from tools.base import Tool
from settings import EMPTY_COLOR

class EraserTool(Tool):
    def __init__(self, app_ref):
        super().__init__(app_ref)
        self.prev_pos = None

    def on_click(self, tab, r, c, event=None):
        self.app.active_tab().save_state()
        self.erase(tab, r, c)
        self.prev_pos = (r, c)

    def on_drag(self, tab, r, c, event=None):
        if self.prev_pos:
            pr, pc = self.prev_pos
            if (pr, pc) != (r, c):
                from algorithms import get_line_pixels
                pixels = get_line_pixels(pr, pc, r, c)
                for lr, lc in pixels:
                    self.erase(tab, lr, lc)
        else:
            self.erase(tab, r, c)
        self.prev_pos = (r, c)

    def on_release(self, tab, event=None):
        self.prev_pos = None

    def erase(self, tab, r, c):
        # Refactored to use central method
        tab.paint_pixel(r, c, EMPTY_COLOR)
        tab.app.notify_preview()