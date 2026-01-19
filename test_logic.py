# test_logic.py
import unittest
import os
from settings import EMPTY_COLOR
from editor_state import EditorState
from project_manager import ProjectManager
from history import HistoryManager

# --- MOCKING APP REFERENCE ---
class MockApp:
    def __init__(self):
        self.rows = 10
        self.cols = 10
        self.pixel_size = 15
        self.current_palette = ["#000000", "#FFFFFF"]
        self.notebook = None # Not needed for logic tests
        self.root = None

# --- THE TESTS ---
class TestPixelLogic(unittest.TestCase):

    def setUp(self):
        """Runs before every test."""
        self.app = MockApp()
        # WE NOW TEST THE REAL LOGIC CLASS, NOT A MOCK
        self.state = EditorState(self.app.rows, self.app.cols)

    # 1. TEST GRID STATE
    def test_grid_initialization(self):
        """Check if grid is created with correct dimensions and empty color."""
        self.assertEqual(len(self.state.grid_data), 10)
        self.assertEqual(len(self.state.grid_data[0]), 10)
        self.assertEqual(self.state.grid_data[0][0], EMPTY_COLOR)

    # 2. TEST SELECTION LOGIC (Using the new EditorState methods)
    def test_selection_normalization(self):
        """Test that selection bounds are always (min, max)."""
        self.state.sel_start = (5, 5)
        self.state.sel_end = (2, 2)
        
        # This method is now in EditorState
        bounds = self.state.get_selection_bounds()
        self.assertEqual(bounds, (2, 2, 5, 5))

    def test_point_in_selection(self):
        """Test the point_in_selection logic."""
        self.state.sel_start = (0, 0)
        self.state.sel_end = (2, 2)
        
        self.assertTrue(self.state.point_in_selection(1, 1))
        self.assertFalse(self.state.point_in_selection(5, 5))

    # 3. TEST HISTORY MANAGER (Via EditorState)
    def test_undo_redo_integration(self):
        """Test that EditorState correctly uses HistoryManager."""
        # State 0: Empty
        self.state.save_state()
        
        # State 1: Paint pixel
        self.state.grid_data[0][0] = "#FF0000"
        
        # Undo -> Should revert to Empty
        prev = self.state.undo()
        self.assertEqual(prev[0][0], EMPTY_COLOR)
        
        # Redo -> Should return to Red
        next_st = self.state.redo()
        self.assertEqual(next_st[0][0], "#FF0000")

    # 4. TEST PROJECT MANAGER (Export Logic)
    def test_gemini_export_format(self):
        """
        Verifies that ProjectManager correctly translates grid data 
        into the text format, without needing the GUI.
        """
        pm = ProjectManager(self.app)
        
        # Setup a dummy state
        self.state.grid_data = [
            ["#FF0000", EMPTY_COLOR],
            [EMPTY_COLOR, "#0000FF"]
        ]
        
        # We Mock the tab object just enough to pass it to the function
        # The function expects an object with .grid_data
        class DummyTab:
            pass
        dummy = DummyTab()
        dummy.grid_data = self.state.grid_data
        
        # Generate content
        content = pm.generate_tab_content(dummy)
        
        # Verify it contains the palette definition
        self.assertIn("palette =", content)
        self.assertIn("my_pixel_art =", content)
        # Verify the ASCII map (A/B depending on sort order)
        self.assertIn(".", content) 

if __name__ == '__main__':
    print("Running Refactored Logic Tests...")
    unittest.main()