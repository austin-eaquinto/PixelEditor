# history.py
import copy

class HistoryManager:
    """
    Manages the Undo/Redo stacks for a grid of data.
    """
    def __init__(self, max_depth=50):
        self.history = []     # Past states
        self.redo_stack = []  # Future states (after undo)
        self.max_depth = max_depth

    def push_state(self, current_grid):
        """Saves the current state before a change occurs."""
        if not current_grid: return
        
        # Deep copy to ensure we save a snapshot, not a reference
        snapshot = [row[:] for row in current_grid]
        
        self.history.append(snapshot)
        if len(self.history) > self.max_depth:
            self.history.pop(0)
            
        # Pushing a new action always clears the Redo history
        self.redo_stack.clear()

    def undo(self, current_grid):
        """
        Returns the previous state grid. 
        Also saves 'current_grid' into the Redo stack.
        Returns None if nothing to undo.
        """
        if not self.history:
            return None
        
        # 1. Push current state to Redo
        redo_snapshot = [row[:] for row in current_grid]
        self.redo_stack.append(redo_snapshot)
        
        # 2. Pop previous state from History
        prev_state = self.history.pop()
        return prev_state

    def redo(self, current_grid):
        """
        Returns the next state grid.
        Also saves 'current_grid' back into History.
        Returns None if nothing to redo.
        """
        if not self.redo_stack:
            return None

        # 1. Push current state back to History
        history_snapshot = [row[:] for row in current_grid]
        self.history.append(history_snapshot)
        
        # 2. Pop next state from Redo
        next_state = self.redo_stack.pop()
        return next_state