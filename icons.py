# icons.py
import tkinter as tk

def create_icon(type_name):
    """Generates 16x16 icons programmatically."""
    img = tk.PhotoImage(width=16, height=16)
    
    def p(x, y, color):
        try: img.put(color, (x, y))
        except: pass

    if type_name == "brush":
        color = "#000000"
        for i in range(3, 13):
            p(i, i, color); p(i+1, i, color)

    elif type_name == "eraser":
        color = "#000000"
        for x in range(3, 13): p(x, 3, color); p(x, 12, color)
        for y in range(3, 13): p(3, y, color); p(12, y, color)

    elif type_name == "bucket":
        # A simple paint bucket / jar
        color = "#000000"
        # Main container
        for x in range(4, 12): p(x, 12, color) # Bottom
        for y in range(6, 12): p(4, y, color); p(11, y, color) # Sides
        # Handle/Top
        for x in range(4, 12): p(x, 5, color)
        # "Paint" drip
        p(10, 4, color); p(11, 3, color)

    elif type_name == "gemini":
        # CHANGED: White color to stand out on the Purple button
        color = "#FFFFFF"
        for i in range(2, 14):
            p(8, i, color); p(i, 8, color)
        p(7,7, color); p(9,9,color); p(7,9,color); p(9,7,color)
    
    elif type_name == "play":
        # Green Play Triangle
        color = "#4CAF50"
        for x in range(4, 14):
            # Logic: Draw a triangle pointing right
            # height grows as x moves right
            height = (x - 4)
            for y in range(4, 4 + height * 2 + 1):
                if y <= 12: # Clip to bottom
                     p(x, 8 - height + (y - 4), color)

    return img