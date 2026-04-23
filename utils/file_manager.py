"""
FileExplorer3D - file_manager.py
Handles folder selection via native OS dialogs.
"""

import os
from pygame.locals import *
from utils.interaction_handler import InteractionHandler


def _askdirectory(**kwargs):
    """Lazy-import tkinter so it doesn't interfere with SDL display detection."""
    from tkinter import filedialog
    return filedialog.askdirectory(**kwargs)


class FileManager:

    @staticmethod
    def resolve_startup_directory(config) -> str:
        """Return the directory to open on launch — last used folder, or home."""
        last = config.get('last_opened_folder')
        if last and os.path.isdir(last):
            return last
        return os.path.expanduser('~')

    @staticmethod
    def handle_events(events, current_dir, config):
        """Handle Ctrl+O to open a new folder. Returns the chosen path or None."""
        for event in events:
            if event.type == KEYDOWN and InteractionHandler.CtrlPressed() and event.key == K_o:
                chosen = _askdirectory(initialdir=current_dir, title='Open Folder')
                if chosen:
                    config.set('last_opened_folder', chosen)
                    config.save()
                    return chosen
        return None
