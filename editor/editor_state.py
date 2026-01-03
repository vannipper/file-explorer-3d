class EditorState:
    """Encapsulates the current state of the editor/game session."""
    def __init__(self):
        self.editor_mode = True
        self.has_unsaved_changes = False
        self.selected_obj = None
        self.running = True