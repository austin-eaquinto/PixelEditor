# algorithms.py

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