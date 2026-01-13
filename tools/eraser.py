# tools/eraser.py
from tools.base import Tool
from settings import EMPTY_COLOR

class EraserTool(Tool):
    def on_click(self, tab, r, c, event=None):
        self.app.active_tab().save_state()
        self.erase(tab, r, c)

    def on_drag(self, tab, r, c, event=None):
        self.erase(tab, r, c)

    def erase(self, tab, r, c):
        if 0 <= r < tab.rows and 0 <= c < tab.cols:
            if tab.grid_data[r][c] != EMPTY_COLOR:
                tab.grid_data[r][c] = EMPTY_COLOR
                if (r, c) in tab.rects:
                    tab.canvas.itemconfig(tab.rects[(r, c)], fill=EMPTY_COLOR)
                tab.app.notify_preview()