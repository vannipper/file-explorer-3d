"""
FileExplorer3D - editor_state.py
Contains the EditorState class, which holds information about the editor session.
"""

class EditorState:
    """Encapsulates the current state of the editor/game session."""
    def __init__(self):
        self.editor_mode = True
        self.has_unsaved_changes = False
        self.selected_obj = None
        self.running = True
