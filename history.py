# history.py
class HistoryManager:
    """
    Manages the Undo/Redo stacks for a grid of data.
    """
    def __init__(self, max_depth=50):
        self.history = []     
        self.redo_stack = []  
        self.max_depth = max_depth

    def push_state(self, current_grid):
        """Saves the current state."""
        if not current_grid: return
        # Deep copy to ensure we save a snapshot, not a reference
        snapshot = [row[:] for row in current_grid]
        self.history.append(snapshot)
        if len(self.history) > self.max_depth:
            self.history.pop(0)
        self.redo_stack.clear()

    def undo(self, current_grid):
        """Returns the previous state grid. Saves current to Redo."""
        if not self.history: return None
        
        redo_snapshot = [row[:] for row in current_grid]
        self.redo_stack.append(redo_snapshot)
        
        return self.history.pop()

    def redo(self, current_grid):
        """Returns the next state grid."""
        if not self.redo_stack: return None

        history_snapshot = [row[:] for row in current_grid]
        self.history.append(history_snapshot)
        
        return self.redo_stack.pop()