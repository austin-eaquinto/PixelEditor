# tools/grab.py
from tools.base import Tool

class GrabTool(Tool):
    def on_click(self, tab, r, c, event=None):
        # Start the scan (scroll)
        tab.canvas.scan_mark(event.x, event.y)

    def on_drag(self, tab, r, c, event=None):
        # Drag the canvas
        tab.canvas.scan_dragto(event.x, event.y, gain=1)