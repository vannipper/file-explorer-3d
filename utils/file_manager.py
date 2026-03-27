"""
FileExplorer3D - file_manager.py
Contains the FileManager class, which allows users to select parent folders on their computer.
"""

# imports
from tkinter import filedialog
from pygame.locals import *
from utils.interaction_handler import InteractionHandler

class FileManager:

    @staticmethod
    def open_file_dialog(config):
        last_folder = config.get('last_opened_folder')
        if last_folder:
            return filedialog.askdirectory(initialdir=last_folder, title='Pick a Root Folder')
        return filedialog.askdirectory(title='Pick a Root Folder')

    @staticmethod
    def handle_events(events, root):
        for event in events:
            if event.type == KEYDOWN and InteractionHandler.CtrlPressed() and event.key == K_o:
                new_folder = filedialog.askdirectory(initialdir=root, title='Open Root Folder')
                if new_folder:
                    root = new_folder
        return root
