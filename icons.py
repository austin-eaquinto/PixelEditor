# icons.py
import tkinter as tk

def create_icon(type_name):
    """Generates 16x16 icons programmatically."""
    img = tk.PhotoImage(width=16, height=16)
    
    def p(x, y, color):
        try: img.put(color, (x, y))
        except: pass

    if type_name == "brush":
        # --- ISSUE 3 FIX: REAL BRUSH ICON ---
        handle = "#8D6E63" # Brown
        ferrule = "#BDBDBD" # Metal
        tip = "#000000"     # Ink
        
        # Handle (diagonal)
        for i in range(8, 14): p(i, i, handle); p(i+1, i, handle)
        
        # Ferrule
        p(6, 6, ferrule); p(7, 6, ferrule); p(6, 7, ferrule)
        
        # Tip
        p(4, 4, tip); p(5, 4, tip); p(4, 5, tip); p(3, 3, tip)

    elif type_name == "eraser":
        color = "#000000"
        for x in range(3, 13): p(x, 3, color); p(x, 12, color)
        for y in range(3, 13): p(3, y, color); p(12, y, color)

    elif type_name == "bucket":
        color = "#000000"
        for x in range(4, 12): p(x, 12, color)
        for y in range(6, 12): p(4, y, color); p(11, y, color)
        for x in range(4, 12): p(x, 5, color)
        p(10, 4, color); p(11, 3, color)

    elif type_name == "line":
        color = "#000000"
        # A simple diagonal line (Distinct from the new brush)
        for i in range(3, 13):
            p(i, i, color)
            p(i+1, i, color)

    elif type_name == "magic_wand":
        color = "#000000"
        for i in range(6, 14): p(i, i, color)
        star_c = "#FF5722" 
        p(4, 4, star_c) 
        p(4, 2, star_c); p(2, 4, star_c) 
        p(6, 4, star_c); p(4, 6, star_c)

    elif type_name == "select":
        color = "#000000"
        for x in range(2, 14, 2): 
            p(x, 2, color); p(x, 13, color)
        for y in range(2, 14, 2): 
            p(2, y, color); p(13, y, color)

    elif type_name == "gemini":
        color = "#FFFFFF"
        for i in range(2, 14):
            p(8, i, color); p(i, 8, color)
        p(7,7, color); p(9,9,color); p(7,9,color); p(9,7,color)
    
    elif type_name == "play":
        color = "#4CAF50"
        for x in range(4, 14):
            height = (x - 4)
            for y in range(4, 4 + height * 2 + 1):
                if y <= 12: p(x, 8 - height + (y - 4), color)

    return img