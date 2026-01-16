# tools/line.py
from tools.base import Tool
from algorithms import get_line_pixels

class LineTool(Tool):
    def __init__(self, app_ref):
        super().__init__(app_ref)
        self.start_pos = None
        # Stores the set of (r, c) tuples currently highlighted in the preview
        self.prev_pixels = set()

    def on_click(self, tab, r, c, event=None):
        tab.commit_selection()
        tab.save_state()
        self.start_pos = (r, c)
        self.prev_pixels = set()
        
        # Trigger the first draw immediately
        self.update_preview(tab, r, c)

    def on_drag(self, tab, r, c, event=None):
        if not self.start_pos: return
        self.update_preview(tab, r, c)

    def on_release(self, tab, event=None):
        if not self.start_pos: return

        # 1. VISUAL CLEANUP: Restore the grid's visual state completely
        # We revert every pixel we touched back to its "true" data color.
        # This prevents "ghost" pixels from getting stuck if the line moved slightly.
        for (pr, pc) in self.prev_pixels:
            if (pr, pc) in tab.rects:
                original_color = tab.grid_data[pr][pc]
                tab.canvas.itemconfig(tab.rects[(pr, pc)], fill=original_color)
        
        # 2. DATA COMMIT: Calculate the final line and write it to the grid logic
        # We use the event coordinates for precision if available
        if event:
            canvas_x = tab.canvas.canvasx(event.x)
            canvas_y = tab.canvas.canvasy(event.y)
            end_c = int(canvas_x // tab.pixel_size)
            end_r = int(canvas_y // tab.pixel_size)
        else:
            # Fallback (rare)
            # We can't trust r/c passed in args because on_release might be out of bounds
            # But usually event is present.
            return 

        sr, sc = self.start_pos
        pixels = get_line_pixels(sr, sc, end_r, end_c)
        
        # Write to data using the central method (handles symmetry & bounds)
        color = self.app.active_color
        for r, c in pixels:
            tab.paint_pixel(r, c, color)

        # Cleanup
        self.start_pos = None
        self.prev_pixels = set()
        tab.app.notify_preview()

    def update_preview(self, tab, end_r, end_c):
        """
        Calculates the line, applies symmetry, and efficiently updates 
        ONLY the pixels that differ from the last frame.
        """
        sr, sc = self.start_pos
        raw_pixels = get_line_pixels(sr, sc, end_r, end_c)
        
        # 1. Calculate the new set of pixels to be highlighted (including mirrors)
        new_pixels = set()
        for (r, c) in raw_pixels:
            # Original
            new_pixels.add((r, c))
            # Mirrors
            if tab.mirror_x:
                new_pixels.add((r, (tab.cols - 1) - c))
            if tab.mirror_y:
                new_pixels.add(((tab.rows - 1) - r, c))
            if tab.mirror_x and tab.mirror_y:
                new_pixels.add(((tab.rows - 1) - r, (tab.cols - 1) - c))

        # 2. FILTER: Only keep valid coordinates
        valid_pixels = {
            (r, c) for (r, c) in new_pixels 
            if 0 <= r < tab.rows and 0 <= c < tab.cols
        }

        # 3. DIFF: Find what changed
        # Pixels to turn ON (in new, not in old)
        to_draw = valid_pixels - self.prev_pixels
        # Pixels to turn OFF (in old, not in new)
        to_clear = self.prev_pixels - valid_pixels

        color = self.app.active_color

        # 4. UPDATE CANVAS
        # Turn ON
        for (r, c) in to_draw:
            if (r, c) in tab.rects:
                tab.canvas.itemconfig(tab.rects[(r, c)], fill=color)
        
        # Turn OFF (Restore to what is actually in grid_data)
        for (r, c) in to_clear:
            if (r, c) in tab.rects:
                original_color = tab.grid_data[r][c]
                tab.canvas.itemconfig(tab.rects[(r, c)], fill=original_color)

        # 5. Store state for next frame
        self.prev_pixels = valid_pixels