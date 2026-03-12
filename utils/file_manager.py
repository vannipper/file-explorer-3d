"""
FileExplorer3D - file_manager.py
Contains the FileManager class, which allows users to select parent folders on their computer.
"""

# imports
import tkinter as tk
from tkinter import filedialog
import json
import os

# TODO: Try to make this class static
class FileManager:
    def __init__(self):
        self.root = tk.Tk()
        self.root.withdraw()

    # TODO: This function can be repurposed for selecting parent folders
    def load_from_path(self, project_dir):
        try:
            json_path = os.path.join(project_dir, self.project_filename)
            if not os.path.exists(json_path): return None
            with open(json_path, 'r') as f:
                data = json.load(f)
            self.current_project_path = project_dir
            return data
        except Exception as e:
            print(f"Failed to load project: {e}")
            return None
    
    # TODO: This function can be repurposed for selecting parent folders
    def open_file_dialog(self, title="Open File", file_types=None):
        return filedialog.askopenfilename(title=title, filetypes=file_types or [("All Files", "*.*")])
