"""
FileExplorer3D - file_manager.py
Handles folder selection via native OS dialogs.
"""

from pygame.locals import *
from utils.interaction_handler import InteractionHandler


def _askdirectory(**kwargs):
    """Lazy-import tkinter so it doesn't interfere with SDL display detection."""
    from tkinter import filedialog
    return filedialog.askdirectory(**kwargs)


class FileManager:

    @staticmethod
    def open_folder_dialog(config):
        """Always prompt the user, opening in the last folder if known."""
        last_folder = config.get('last_opened_folder')
        if last_folder:
            selected = _askdirectory(initialdir=last_folder, title='Pick a Root Folder')
        else:
            selected = _askdirectory(title='Pick a Root Folder')
        if selected:
            config.set('last_opened_folder', selected)
            config.save()
        return selected

    @staticmethod
    def handle_events(events, current_dir, config):
        """Handle Ctrl+O to open a new folder. Returns new path or current_dir."""
        for event in events:
            if event.type == KEYDOWN and InteractionHandler.CtrlPressed() and event.key == K_o:
                new_folder = _askdirectory(
                    initialdir=current_dir, title='Open Root Folder'
                )
                if new_folder:
                    config.set('last_opened_folder', new_folder)
                    config.save()
                    return new_folder
        return current_dir
