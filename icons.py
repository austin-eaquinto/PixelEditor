# icons.py
import tkinter as tk
import os

# Define where icons live
ICON_DIR = "assets/icons"

def create_icon(type_name):
    """
    Tries to load {type_name}.png from assets/icons.
    Falls back to procedural generation if file not found.
    """
    # 1. Ensure directory exists
    if not os.path.exists(ICON_DIR):
        try:
            os.makedirs(ICON_DIR)
        except:
            pass # Permissions error or similar

    # 2. Try loading PNG
    file_path = os.path.join(ICON_DIR, f"{type_name}.png")
    if os.path.exists(file_path):
        try:
            # Tkinter handles PNGs natively in modern versions
            return tk.PhotoImage(file=file_path)
        except Exception as e:
            print(f"Failed to load icon {file_path}: {e}")

    # 3. FALLBACK: Procedural Generation (Old Code)
    return _generate_procedural_icon(type_name)

def _generate_procedural_icon(type_name):
    """Generates 16x16 icons programmatically (Legacy Fallback)."""
    img = tk.PhotoImage(width=16, height=16)
    
    def p(x, y, color):
        try: img.put(color, (x, y))
        except: pass

    if type_name == "brush":
        handle, ferrule, tip = "#8D6E63", "#BDBDBD", "#000000"
        for i in range(8, 14): p(i, i, handle); p(i+1, i, handle)
        p(6, 6, ferrule); p(7, 6, ferrule); p(6, 7, ferrule)
        p(4, 4, tip); p(5, 4, tip); p(4, 5, tip); p(3, 3, tip)

    elif type_name == "eraser":
        c = "#000000"
        for x in range(3, 13): p(x, 3, c); p(x, 12, c)
        for y in range(3, 13): p(3, y, c); p(12, y, c)

    elif type_name == "bucket":
        c = "#000000"
        for x in range(4, 12): p(x, 12, c)
        for y in range(6, 12): p(4, y, c); p(11, y, c)
        for x in range(4, 12): p(x, 5, c)
        p(10, 4, c); p(11, 3, c)

    elif type_name == "line":
        c = "#000000"
        for i in range(3, 13): p(i, i, c); p(i+1, i, c)

    elif type_name == "magic_wand":
        c, star = "#000000", "#FF5722"
        for i in range(6, 14): p(i, i, c)
        p(4, 4, star); p(4, 2, star); p(2, 4, star); p(6, 4, star); p(4, 6, star)
    
    elif type_name == "picker":
        c, liq = "#000000", "#2196F3"
        for i in range(4, 9): p(i, i, c); p(i+1, i, c); p(i, i+1, c)
        p(3, 3, c)
        for i in range(9, 13): p(i, i, liq); p(i+1, i, liq); p(i, i+1, liq)

    elif type_name == "select":
        c = "#000000"
        for x in range(2, 14, 2): p(x, 2, c); p(x, 13, c)
        for y in range(2, 14, 2): p(2, y, c); p(13, y, c)
    
    elif type_name == "lasso":
        c = "#000000"
        # Draw a loop shape
        p(5, 4, c); p(6, 3, c); p(7, 3, c); p(8, 4, c)
        p(9, 5, c); p(10, 6, c); p(10, 7, c); p(9, 8, c)
        p(8, 9, c); p(7, 10, c); p(6, 11, c); p(5, 12, c)
        p(4, 11, c); p(4, 10, c); p(5, 9, c)
        # The "rope" end
        p(11, 8, c); p(12, 9, c)
    
    elif type_name == "rect":
        c = "#000000"
        for x in range(3, 13): p(x, 4, c); p(x, 11, c)
        for y in range(4, 12): p(3, y, c); p(12, y, c)
            
    elif type_name == "ellipse":
        c = "#000000"
        p(7, 3, c); p(8, 3, c); p(7, 12, c); p(8, 12, c)
        p(3, 7, c); p(3, 8, c); p(12, 7, c); p(12, 8, c)
        p(4, 5, c); p(5, 4, c); p(10, 4, c); p(11, 5, c)
        p(4, 10, c); p(5, 11, c); p(10, 11, c); p(11, 10, c)

    elif type_name == "gemini":
        c = "#FFFFFF"
        for i in range(2, 14): p(8, i, c); p(i, 8, c)
        p(7,7, c); p(9,9,c); p(7,9,c); p(9,7,c)
    
    elif type_name == "play":
        c = "#4CAF50"
        for x in range(4, 14):
            height = (x - 4)
            for y in range(4, 4 + height * 2 + 1):
                if y <= 12: p(x, 8 - height + (y - 4), c)

    return img