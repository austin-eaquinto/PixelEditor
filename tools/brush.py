# tools/brush.py
from tools.base import Tool
from settings import EMPTY_COLOR

class BrushTool(Tool):
    def on_click(self, tab, r, c, event=None):
        self.app.active_tab().save_state()
        self.paint(tab, r, c)

    def on_drag(self, tab, r, c, event=None):
        self.paint(tab, r, c)

    def paint(self, tab, r, c):
        # We assume 'tab' has a helper method or we access grid directly
        # For now, let's use the existing logic inside EditorTab
        # or implement it here. Let's reuse EditorTab's paint for consistency first.
        if 0 <= r < tab.rows and 0 <= c < tab.cols:
            if tab.grid_data[r][c] != self.app.active_color:
                tab.grid_data[r][c] = self.app.active_color
                # Update visual
                if (r, c) in tab.rects:
                    tab.canvas.itemconfig(tab.rects[(r, c)], fill=self.app.active_color)
                tab.app.notify_preview()