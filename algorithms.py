# algorithms.py
import math

def get_connected_pixels(grid, start_r, start_c):
    """
    Performs a Breadth-First Search (BFS) to find all connected pixels 
    matching the color at (start_r, start_c).
    
    Returns: A list of (r, c) tuples.
    """
    rows = len(grid)
    cols = len(grid[0]) if rows > 0 else 0
    
    target_color = grid[start_r][start_c]
    
    queue = [(start_r, start_c)]
    visited = set()
    connected_pixels = []
    
    # Standard BFS Loop
    while queue:
        r, c = queue.pop(0)
        
        if (r, c) in visited: continue
        visited.add((r, c))
        
        if grid[r][c] == target_color:
            connected_pixels.append((r, c))
            
            # Check Neighbors (Up, Down, Left, Right)
            if r > 0: queue.append((r-1, c))
            if r < rows - 1: queue.append((r+1, c))
            if c > 0: queue.append((r, c-1))
            if c < cols - 1: queue.append((r, c+1))
            
    return connected_pixels

def get_line_pixels(start_r, start_c, end_r, end_c):
    """
    Returns a list of (r, c) tuples using Bresenham's Line Algorithm.
    """
    pixels = []
    
    x1, y1 = start_c, start_r
    x2, y2 = end_c, end_r
    
    dx = abs(x2 - x1)
    dy = abs(y2 - y1)
    
    sx = 1 if x1 < x2 else -1
    sy = 1 if y1 < y2 else -1
    
    err = dx - dy
    
    while True:
        pixels.append((y1, x1))
        
        if x1 == x2 and y1 == y2:
            break
            
        e2 = 2 * err
        if e2 > -dy:
            err -= dy
            x1 += sx
        if e2 < dx:
            err += dx
            y1 += sy
            
    return pixels

def get_rectangle_pixels(r1, c1, r2, c2):
    """Returns the perimeter pixels of a rectangle defined by two corners."""
    pixels = set()
    
    min_r, max_r = min(r1, r2), max(r1, r2)
    min_c, max_c = min(c1, c2), max(c1, c2)
    
    # Top and Bottom rows
    for c in range(min_c, max_c + 1):
        pixels.add((min_r, c))
        pixels.add((max_r, c))
        
    # Left and Right columns
    for r in range(min_r, max_r + 1):
        pixels.add((r, min_c))
        pixels.add((r, max_c))
        
    return list(pixels)

def get_ellipse_pixels(r1, c1, r2, c2):
    """
    Returns pixels for an ellipse fitting inside the bounding box (r1,c1) to (r2,c2).
    Uses a standard trigonometric approach for simplicity and coverage.
    """
    pixels = set()
    
    min_r, max_r = min(r1, r2), max(r1, r2)
    min_c, max_c = min(c1, c2), max(c1, c2)
    
    height = max_r - min_r
    width = max_c - min_c
    
    center_r = min_r + height / 2.0
    center_c = min_c + width / 2.0
    
    a = width / 2.0
    b = height / 2.0
    
    if a == 0 or b == 0:
        return get_line_pixels(min_r, min_c, max_r, max_c)

    # Step size based on circumference to ensure no gaps
    circumference = math.pi * (3*(a+b) - math.sqrt((3*a + b) * (a + 3*b)))
    steps = int(circumference * 1.5) # 1.5x Over-sample to fill gaps
    if steps == 0: steps = 4

    for i in range(steps):
        theta = 2 * math.pi * i / steps
        # Calculate pixel position relative to center
        r = int(round(center_r + b * math.sin(theta)))
        c = int(round(center_c + a * math.cos(theta)))
        pixels.add((r, c))
        
    return list(pixels)