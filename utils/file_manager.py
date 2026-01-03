import tkinter as tk
from tkinter import filedialog, messagebox
import json
import os

class FileManager:
    def __init__(self):
        self.root = tk.Tk()
        self.root.withdraw()
        self.current_file_path = None
        self.extension = ".zpf"
        self.default_file_types = [("Zenith Project Files", f"*{self.extension}"), ("All Files", "*.*")]

    def open_file_dialog(self, title="Open Zenith Project", file_types=None):
        """Opens a file dialog with optional custom file types."""
        types = file_types if file_types else self.default_file_types
        file_path = filedialog.askopenfilename(title=title, filetypes=types)
        if file_path:
            # We only track the project path if we are opening a project file
            if file_path.endswith(self.extension):
                self.current_file_path = file_path
            return file_path
        return None

    def save_file_dialog(self, title="Save Zenith Project", file_types=None):
        """Opens a save dialog with optional custom file types."""
        types = file_types if file_types else self.default_file_types
        file_path = filedialog.asksaveasfilename(
            title=title,
            defaultextension=self.extension,
            filetypes=types
        )
        if file_path:
            if file_path.endswith(self.extension):
                self.current_file_path = file_path
            return file_path
        return None

    def ask_save_changes(self):
        """Prompts the user about unsaved changes. Returns True (Yes), False (No), or None (Cancel)."""
        return messagebox.askyesnocancel("Unsaved Changes", "You have unsaved changes. Do you want to save them before exiting?")

    def save_to_path(self, path, world_data):
        try:
            with open(path, 'w') as f:
                json.dump(world_data, f, indent=4)
            self.current_file_path = path
            return True
        except Exception as e:
            print(f"Failed to save project: {e}")
            return False

    def load_from_path(self, path):
        try:
            if not os.path.exists(path): return None
            with open(path, 'r') as f:
                data = json.load(f)
            self.current_file_path = path
            return data
        except Exception as e:
            print(f"Failed to load project: {e}")
            return None