# tools/lasso.py
import tkinter as tk
from tools.base import Tool
from PIL import Image, ImageDraw

class LassoTool(Tool):
    def __init__(self, app_ref):
        super().__init__(app_ref)
        self.points = []
        self.line_id = None

    def on_click(self, tab, r, c, event=None):
        # If we already have a selection...
        if tab.state.floating_pixels:
            if not tab.point_in_selection(r, c):
                tab.commit_selection()
            else:
                # FIX: Handoff to Select Tool safely
                self.app.select_selection_tool(commit=False)
                
                # FORCE the select tool into move mode
                if isinstance(self.app.active_tool, self.app.tool_instances["select"].__class__):
                    self.app.active_tool.start_move_mode(tab, r, c)
                return

        self.points = []
        if event:
            self.points.append((event.x, event.y))

    # ... (Keep on_drag and on_release exactly as they were) ...
    def on_drag(self, tab, r, c, event=None):
        if not event: return
        self.points.append((event.x, event.y))
        if len(self.points) > 1:
            if self.line_id: tab.canvas.delete(self.line_id)
            self.line_id = tab.canvas.create_line(self.points, fill="#FF5722", width=2, tag="ui")

    def on_release(self, tab, event=None):
        if self.line_id: tab.canvas.delete(self.line_id)
        self.line_id = None
        
        if len(self.points) < 3:
            self.points = []
            return

        try:
            mask_img = Image.new('1', (tab.cols, tab.rows), 0)
            draw = ImageDraw.Draw(mask_img)
            
            grid_points = []
            for (x, y) in self.points:
                cx = tab.canvas.canvasx(x)
                cy = tab.canvas.canvasy(y)
                gc = cx / tab.pixel_size
                gr = cy / tab.pixel_size
                grid_points.append((gc, gr))
            
            draw.polygon(grid_points, fill=1, outline=1)
            
            valid_pixels = set()
            width, height = mask_img.size
            for r in range(height):
                for c in range(width):
                    if mask_img.getpixel((c, r)):
                        valid_pixels.add((r, c))
            
            if valid_pixels:
                tab.state.lift_complex_selection(valid_pixels)
                tab.draw_grid_lines()
                
        except Exception as e:
            print(f"Lasso Error: {e}")
        
        self.points = []