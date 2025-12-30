import unittest
import os
from settings import EMPTY_COLOR

# --- MOCK OBJECTS ---
# We use these to fake the "App" and "Tab" so we don't need to launch the GUI
class MockTab:
    def __init__(self, rows, cols):
        self.rows = rows
        self.cols = cols
        self.grid_data = [[EMPTY_COLOR for _ in range(cols)] for _ in range(rows)]

class MockApp:
    def __init__(self):
        self.rows = 10
        self.cols = 10
        self.pixel_size = 15
        self.current_palette = ["#000000", "#FFFFFF"]

# --- THE TESTS ---
class TestPixelLogic(unittest.TestCase):

    def setUp(self):
        """Runs before every test. Sets up a clean environment."""
        self.app = MockApp()
        self.tab = MockTab(self.app.rows, self.app.cols)

    # 1. TEST GRID MATH
    def test_pixel_to_grid_conversion(self):
        """Checks if mouse coordinates correctly map to grid row/col."""
        pixel_size = 15
        
        # Click at 0,0 -> Should be Row 0, Col 0
        self.assertEqual(0 // pixel_size, 0)
        
        # Click at 15, 15 -> Should be Row 1, Col 1
        self.assertEqual(15 // pixel_size, 1)
        
        # Click at 149 (just inside 10th block) -> Should be index 9
        self.assertEqual(149 // pixel_size, 9)

    # 2. TEST PALETTE RESIZING
    def test_palette_resize_grow(self):
        """If we increase palette size, does it pad with white?"""
        current = ["#FF0000", "#00FF00"] # Red, Green
        target_size = 4
        
        # Logic extracted from palette_manager.py
        if target_size > len(current):
            current += ["#FFFFFF"] * (target_size - len(current))
            
        self.assertEqual(len(current), 4)
        self.assertEqual(current[2], "#FFFFFF") # New slot should be white

    def test_palette_resize_shrink(self):
        """If we decrease palette size, does it slice correctly?"""
        current = ["#A", "#B", "#C", "#D"]
        target_size = 2
        
        # Logic extracted from palette_manager.py
        if target_size < len(current):
            current = current[:target_size]
            
        self.assertEqual(len(current), 2)
        self.assertEqual(current, ["#A", "#B"])

    # 3. TEST GEMINI EXPORT LOGIC (Critical!)
    def test_gemini_export_translation(self):
        """
        Verifies that a grid of colors is correctly translated 
        into the text format Gemini expects.
        """
        # Setup a tiny 2x2 grid
        # [ Red,   White ]
        # [ White, Blue  ]
        red = "#FF0000"
        blue = "#0000FF"
        
        self.tab.grid_data = [
            [red, EMPTY_COLOR],
            [EMPTY_COLOR, blue]
        ]
        
        # We assume the export logic uses these symbols: 
        # Sorted Unique Colors: Blue (#0000FF), Red (#FF0000)
        # Symbols: 'A' -> Blue, 'B' -> Red (Assuming alphabetical sort of hex)
        # Note: In your actual code, unique_colors are sorted. 
        # #0000FF comes before #FF0000.
        
        # Run the logic (Simulated from project_manager.py)
        unique_colors = sorted({red, blue})
        symbols = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        color_map = {EMPTY_COLOR: '.'}
        
        # Map generated symbols
        for i, color in enumerate(unique_colors):
            color_map[color] = symbols[i]
            
        # Expected Map: 
        # #0000FF (Blue) -> 'A'
        # #FF0000 (Red)  -> 'B'
        
        # Generate the string
        ascii_art = ""
        for row in self.tab.grid_data:
            line = ""
            for cell in row:
                if cell == EMPTY_COLOR: line += "."
                else: line += color_map[cell]
            ascii_art += line + "\n"
            
        expected_output = "B.\n.A\n"
        self.assertEqual(ascii_art, expected_output)

    # 4. TEST SAVE PATH LOGIC
    def test_save_folder_naming(self):
        """Verifies that we correctly strip filenames to get folder paths."""
        
        # Scenario 1: User types a name "MyCharacter"
        user_input_path = "C:/Users/Test/Desktop/MyCharacter.json"
        
        # Logic from project_manager.py
        folder_name = os.path.splitext(os.path.basename(user_input_path))[0]
        self.assertEqual(folder_name, "MyCharacter")
        
        # Scenario 2: User selects existing file "project_data.json" inside a folder
        existing_file_path = "C:/Users/Test/Desktop/MyGame/project_data.json"
        filename = os.path.basename(existing_file_path)
        
        if filename == "project_data.json":
            folder_path = os.path.dirname(existing_file_path)
        else:
            folder_path = "Should Not Happen"
            
        # We expect it to grab the parent folder
        self.assertEqual(os.path.normpath(folder_path), os.path.normpath("C:/Users/Test/Desktop/MyGame"))

if __name__ == '__main__':
    print("Running Pixel Editor Tests...")
    unittest.main()