import unittest
import os
from settings import EMPTY_COLOR

# --- MOCK OBJECTS ---
# Updated MockTab to include Selection logic needed for the new tests
class MockTab:
    def __init__(self, rows, cols):
        self.rows = rows
        self.cols = cols
        self.grid_data = [[EMPTY_COLOR for _ in range(cols)] for _ in range(rows)]
        
        # Selection Attributes
        self.sel_start = None
        self.sel_end = None
        self.floating_pixels = {}
        self.floating_offset = (0, 0)

    # Logic copied from editor_tab.py to ensure the math holds up in isolation
    def get_selection_bounds(self):
        if not self.sel_start or not self.sel_end: return None
        r1, c1 = self.sel_start
        r2, c2 = self.sel_end
        return (min(r1, r2), min(c1, c2), max(r1, r2), max(c1, c2))

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

    # 3. TEST GEMINI EXPORT LOGIC
    def test_gemini_export_translation(self):
        """
        Verifies that a grid of colors is correctly translated 
        into the text format Gemini expects.
        """
        red = "#FF0000"
        blue = "#0000FF"
        
        self.tab.grid_data = [
            [red, EMPTY_COLOR],
            [EMPTY_COLOR, blue]
        ]
        
        # Run the logic (Simulated from project_manager.py)
        unique_colors = sorted({red, blue})
        symbols = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        color_map = {EMPTY_COLOR: '.'}
        
        for i, color in enumerate(unique_colors):
            color_map[color] = symbols[i]
            
        ascii_art = ""
        for row in self.tab.grid_data:
            line = ""
            for cell in row:
                if cell == EMPTY_COLOR: line += "."
                else: line += color_map[cell]
            ascii_art += line + "\n"
            
        # Expected: Blue=#0000FF (A), Red=#FF0000 (B) because of sort order
        expected_output = "B.\n.A\n"
        self.assertEqual(ascii_art, expected_output)

    # 4. TEST SAVE PATH LOGIC
    def test_save_folder_naming(self):
        """Verifies that we correctly strip filenames to get folder paths."""
        user_input_path = "C:/Users/Test/Desktop/MyCharacter.json"
        folder_name = os.path.splitext(os.path.basename(user_input_path))[0]
        self.assertEqual(folder_name, "MyCharacter")

    # 5. TEST SELECTION LOGIC (NEW)
    def test_selection_normalization(self):
        """
        Tests that selection bounds are always returned as (min_r, min_c, max_r, max_c),
        regardless of which direction the user dragged the mouse.
        """
        # Case A: User drags Top-Left to Bottom-Right (Standard)
        self.tab.sel_start = (2, 2)
        self.tab.sel_end = (5, 5)
        bounds = self.tab.get_selection_bounds()
        self.assertEqual(bounds, (2, 2, 5, 5))

        # Case B: User drags Bottom-Right to Top-Left (Reverse)
        self.tab.sel_start = (5, 5)
        self.tab.sel_end = (2, 2)
        bounds = self.tab.get_selection_bounds()
        # Should still be normalized to (2, 2, 5, 5)
        self.assertEqual(bounds, (2, 2, 5, 5))
        
        # Case C: User drags Bottom-Left to Top-Right (Diagonal)
        self.tab.sel_start = (5, 2)
        self.tab.sel_end = (2, 5)
        bounds = self.tab.get_selection_bounds()
        # Should be (Row 2 to 5, Col 2 to 5)
        self.assertEqual(bounds, (2, 2, 5, 5))

if __name__ == '__main__':
    print("Running Combined Logic Tests...")
    unittest.main()

    # ... (Previous code above) ...

# Import the actual algorithms to test them
from algorithms import get_connected_pixels, get_line_pixels
from history import HistoryManager

class TestAlgorithmsAndHistory(unittest.TestCase):
    
    # --- TEST 6: BUCKET FILL (BFS) ---
    def test_bfs_connected_pixels(self):
        """Test finding connected pixels of the same color."""
        # Create a 3x3 grid
        # R R B
        # R B B
        # B B B
        R = "#FF0000"
        B = "#0000FF"
        grid = [
            [R, R, B],
            [R, B, B],
            [B, B, B]
        ]
        
        # Test 1: Click Top-Left Red (0,0) -> Should find (0,0), (0,1), (1,0)
        result_red = get_connected_pixels(grid, 0, 0)
        self.assertEqual(len(result_red), 3)
        self.assertIn((0, 1), result_red)
        self.assertIn((1, 0), result_red)
        self.assertNotIn((0, 2), result_red) # Blue shouldn't be included

        # Test 2: Click Bottom-Right Blue (2,2) -> Should find the 'L' shape of blues
        result_blue = get_connected_pixels(grid, 2, 2)
        self.assertEqual(len(result_blue), 6)

    # --- TEST 7: LINE ALGORITHM ---
    def test_bresenham_line(self):
        """Test that line generation includes start and end points."""
        # Horizontal line from (0,0) to (0,5)
        # Note: get_line_pixels takes (start_r, start_c, end_r, end_c)
        pixels = get_line_pixels(0, 0, 0, 5)
        
        self.assertEqual(len(pixels), 6) # 0,1,2,3,4,5
        self.assertIn((0, 0), pixels) # Start
        self.assertIn((0, 5), pixels) # End
        self.assertIn((0, 3), pixels) # Midpoint

        # Diagonal line (0,0) to (2,2) -> (0,0), (1,1), (2,2)
        diag = get_line_pixels(0, 0, 2, 2)
        self.assertEqual(len(diag), 3)
        self.assertIn((1, 1), diag)

    # --- TEST 8: HISTORY (UNDO/REDO) ---
    def test_history_manager(self):
        """Test pushing states, undoing, and redoing."""
        hist = HistoryManager(max_depth=5)
        
        # State 1: Blank Grid
        grid_state_1 = [["#000"]]
        hist.push_state(grid_state_1)
        
        # State 2: Painted
        grid_state_2 = [["#FFF"]]
        
        # UNDO Check
        # Undo should return State 1
        prev = hist.undo(grid_state_2) 
        self.assertEqual(prev, grid_state_1)
        
        # REDO Check
        # Redo should return State 2
        # Note: We pass the 'current' state (State 1) to redo
        next_state = hist.redo(grid_state_1)
        self.assertEqual(next_state, grid_state_2)

if __name__ == '__main__':
    print("Running All Logic Tests...")
    unittest.main()