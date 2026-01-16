# tools/picker.py
from tools.base import Tool

class EyedropperTool(Tool):
    def on_click(self, tab, r, c, event=None):
        if 0 <= r < tab.rows and 0 <= c < tab.cols:
            picked_color = tab.grid_data[r][c]
            
            # Update the main app state with the new color
            self.app.set_active_color(picked_color)
            
            # Optional feedback (could be a toast or just the UI update)
            print(f"Picked color: {picked_color}")

    def on_drag(self, tab, r, c, event=None):
        # Allow dragging to scan for colors
        self.on_click(tab, r, c, event)