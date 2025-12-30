# editor_tab.py
import tkinter as tk
from settings import *

class EditorTab:
    """Represents a single Tab/Frame in the animation."""
    def __init__(self, notebook, app_ref, rows, cols, pixel_size, name="Frame"):
        self.app = app_ref 
        self.rows = rows
        self.cols = cols
        self.pixel_size = pixel_size
        
        # Data Structures
        self.grid_data = [[EMPTY_COLOR for _ in range(self.cols)] for _ in range(self.rows)]
        self.history = []
        self.redo_stack = []
        self.rects = {} 

        # UI Elements
        self.frame = tk.Frame(notebook)
        
        self.v_scroll = tk.Scrollbar(self.frame, orient=tk.VERTICAL)
        self.h_scroll = tk.Scrollbar(self.frame, orient=tk.HORIZONTAL)
        self.canvas = tk.Canvas(self.frame, bg="#cccccc",
                                xscrollcommand=self.h_scroll.set,
                                yscrollcommand=self.v_scroll.set)
        
        self.v_scroll.config(command=self.canvas.yview)
        self.h_scroll.config(command=self.canvas.xview)
        
        self.v_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.h_scroll.pack(side=tk.BOTTOM, fill=tk.X)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Bindings
        self.canvas.bind("<Button-1>", self.on_click)      
        self.canvas.bind("<B1-Motion>", self.on_drag)     
        self.canvas.bind("<Button-3>", self.start_eraser)
        self.canvas.bind("<B3-Motion>", self.drag_eraser)
        
        self.canvas.bind("<MouseWheel>", self._on_mousewheel)
        self.canvas.bind("<Shift-MouseWheel>", self._on_shift_mousewheel)

        self.draw_grid_lines()

    def draw_grid_lines(self):
        self.canvas.delete("all") 
        self.rects = {} 
        width = self.cols * self.pixel_size
        height = self.rows * self.pixel_size
        self.canvas.config(scrollregion=(0, 0, width, height))
        
        outline = "#bbbbbb" if self.app.show_grid else ""
        
        for r in range(self.rows):
            for c in range(self.cols):
                x1 = c * self.pixel_size; y1 = r * self.pixel_size
                x2 = x1 + self.pixel_size; y2 = y1 + self.pixel_size
                color = self.grid_data[r][c]
                rect = self.canvas.create_rectangle(x1, y1, x2, y2, outline=outline, fill=color)
                self.rects[(r, c)] = rect

    def save_state(self):
        # Deep copy for undo history
        state = [row[:] for row in self.grid_data]
        self.history.append(state)
        if len(self.history) > 50: self.history.pop(0)
        self.redo_stack.clear()

    def paint(self, event, specific_color=None):
        canvas_x = self.canvas.canvasx(event.x)
        canvas_y = self.canvas.canvasy(event.y)
        col = int(canvas_x // self.pixel_size)
        row = int(canvas_y // self.pixel_size)

        if 0 <= row < self.rows and 0 <= col < self.cols:
            target = specific_color if specific_color else self.app.active_color
            
            if self.grid_data[row][col] != target:
                self.grid_data[row][col] = target
                if (row, col) in self.rects:
                    outline = "#000000" if self.app.show_grid else ""
                    self.canvas.itemconfig(self.rects[(row, col)], fill=target, outline=outline)

    def flood_fill(self, start_r, start_c, target_color):
        """Standard Breadth-First Search (BFS) Flood Fill."""
        # 1. Get the color we are replacing
        original_color = self.grid_data[start_r][start_c]
        
        # 2. Don't fill if we are painting the same color
        if original_color == target_color: return

        # 3. BFS Queue
        queue = [(start_r, start_c)]
        visited = set()
        
        while queue:
            r, c = queue.pop(0)
            if (r, c) in visited: continue
            visited.add((r, c))
            
            if self.grid_data[r][c] == original_color:
                self.grid_data[r][c] = target_color
                
                # Check neighbors (Up, Down, Left, Right)
                if r > 0: queue.append((r-1, c))
                if r < self.rows - 1: queue.append((r+1, c))
                if c > 0: queue.append((r, c-1))
                if c < self.cols - 1: queue.append((r, c+1))

        # 4. Redraw everything once finished
        self.draw_grid_lines()

    # Event Handlers
    def on_click(self, event):
        if self.app.active_tool == "grab": 
            self.canvas.scan_mark(event.x, event.y)
        
        elif self.app.active_tool == "bucket":
            # --- BUCKET LOGIC ---
            canvas_x = self.canvas.canvasx(event.x)
            canvas_y = self.canvas.canvasy(event.y)
            col = int(canvas_x // self.pixel_size)
            row = int(canvas_y // self.pixel_size)
            
            if 0 <= row < self.rows and 0 <= col < self.cols:
                self.save_state() # Save Undo history first!
                self.flood_fill(row, col, self.app.active_color)
        
        else:
            self.save_state()
            self.paint(event)

    def on_drag(self, event):
        if self.app.active_tool == "grab": self.canvas.scan_dragto(event.x, event.y, gain=1)
        else: self.paint(event)

    def start_eraser(self, event):
        self.save_state()
        self.paint(event, EMPTY_COLOR)
    
    def drag_eraser(self, event):
        self.paint(event, EMPTY_COLOR)

    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")

    def _on_shift_mousewheel(self, event):
        self.canvas.xview_scroll(int(-1*(event.delta/120)), "units")