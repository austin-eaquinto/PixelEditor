from tools.base import Tool
from algorithms import get_rectangle_pixels, get_ellipse_pixels

class ShapeTool(Tool):
    """
    Base class for Rectangle and Ellipse tools.
    Uses 'Dirty Pixel' rendering for lag-free previews.
    """
    def __init__(self, app_ref):
        super().__init__(app_ref)
        self.start_pos = None
        self.prev_pixels = set()
        self.shape_type = "rect" # 'rect' or 'ellipse'

    def on_click(self, tab, r, c, event=None):
        tab.commit_selection()
        tab.save_state()
        self.start_pos = (r, c)
        self.prev_pixels = set()
        self.update_preview(tab, r, c)

    def on_drag(self, tab, r, c, event=None):
        if not self.start_pos: return
        self.update_preview(tab, r, c)

    def on_release(self, tab, event=None):
        if not self.start_pos: return
        
        # 1. VISUAL CLEANUP (Revert highlighted pixels)
        for (pr, pc) in self.prev_pixels:
            if (pr, pc) in tab.rects:
                original_color = tab.grid_data[pr][pc]
                tab.canvas.itemconfig(tab.rects[(pr, pc)], fill=original_color)
                
        # 2. CALCULATE FINAL SHAPE
        if event:
            canvas_x = tab.canvas.canvasx(event.x)
            canvas_y = tab.canvas.canvasy(event.y)
            end_c = int(canvas_x // tab.pixel_size)
            end_r = int(canvas_y // tab.pixel_size)
        else:
            return

        sr, sc = self.start_pos
        pixels = self._get_shape_pixels(sr, sc, end_r, end_c)
        
        # 3. COMMIT TO DATA
        color = self.app.active_color
        for r, c in pixels:
            tab.paint_pixel(r, c, color)
            
        self.start_pos = None
        self.prev_pixels = set()
        tab.app.notify_preview()

    def update_preview(self, tab, end_r, end_c):
        sr, sc = self.start_pos
        raw_pixels = self._get_shape_pixels(sr, sc, end_r, end_c)
        
        # 1. MIRROR LOGIC
        new_pixels = set()
        for (r, c) in raw_pixels:
            new_pixels.add((r, c))
            if tab.mirror_x: new_pixels.add((r, (tab.cols - 1) - c))
            if tab.mirror_y: new_pixels.add(((tab.rows - 1) - r, c))
            if tab.mirror_x and tab.mirror_y: new_pixels.add(((tab.rows - 1) - r, (tab.cols - 1) - c))

        valid_pixels = {(r, c) for (r, c) in new_pixels if 0 <= r < tab.rows and 0 <= c < tab.cols}

        # 2. DIFF RENDERING
        to_draw = valid_pixels - self.prev_pixels
        to_clear = self.prev_pixels - valid_pixels
        color = self.app.active_color

        for (r, c) in to_draw:
            if (r, c) in tab.rects:
                tab.canvas.itemconfig(tab.rects[(r, c)], fill=color)
        
        for (r, c) in to_clear:
            if (r, c) in tab.rects:
                tab.canvas.itemconfig(tab.rects[(r, c)], fill=tab.grid_data[r][c])

        self.prev_pixels = valid_pixels

    def _get_shape_pixels(self, r1, c1, r2, c2):
        if self.shape_type == "rect":
            return get_rectangle_pixels(r1, c1, r2, c2)
        elif self.shape_type == "ellipse":
            return get_ellipse_pixels(r1, c1, r2, c2)
        return []

class RectangleTool(ShapeTool):
    def __init__(self, app_ref):
        super().__init__(app_ref)
        self.shape_type = "rect"

class EllipseTool(ShapeTool):
    def __init__(self, app_ref):
        super().__init__(app_ref)
        self.shape_type = "ellipse"