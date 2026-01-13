# tools/base.py

class Tool:
    """
    Abstract base class for all tools.
    """
    def __init__(self, app_ref):
        self.app = app_ref

    def on_click(self, tab, r, c, event=None):
        """Called when the mouse is clicked (Button-1)."""
        pass

    def on_drag(self, tab, r, c, event=None):
        """Called when the mouse is dragged (B1-Motion)."""
        pass

    def on_release(self, tab, event=None):
        """Called when the mouse is released."""
        pass