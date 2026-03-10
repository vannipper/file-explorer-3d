import tkinter as tk
from tkinter import filedialog, messagebox
import json
import os
import shutil

class FileManager:
    def __init__(self):
        self.root = tk.Tk()
        self.root.withdraw()
        self.current_project_path = None # Directory path
        self.extension = ".zenith"
        self.project_filename = "project.json"

    def open_project_dialog(self):
        """Opens a directory dialog to select a .zenith project folder."""
        path = filedialog.askdirectory(title="Open Zenith Project Folder")
        if path:
            if os.path.exists(os.path.join(path, self.project_filename)):
                self.current_project_path = path
                return path
            else:
                messagebox.showerror("Error", "Selected folder is not a valid Zenith project.")
        return None

    def save_project_dialog(self, title="Create New Project Folder"):
        """Opens a dialog to name a new project directory."""
        path = filedialog.asksaveasfilename(title=title)
        if path:
            if not path.endswith(self.extension):
                path += self.extension
            
            if not os.path.exists(path):
                os.makedirs(path)
                os.makedirs(os.path.join(path, "assets"))
            
            self.current_project_path = path
            return path
        return None

    def handle_model_import_workflow(self, project_save_callback):
        """
        Handles the UI workflow for importing an OBJ model.
        Returns (rel_obj_path, abs_obj_path) or None. 
        Texture selection has been removed.
        """
        # 1. Select OBJ
        obj_path = self.open_file_dialog(title="Import .OBJ", file_types=[("OBJ Files", "*.obj")])
        if not obj_path: return None

        # 2. Ensure project exists
        if not self.current_project_path:
            path = self.save_project_dialog(title="Create Project Folder to Store Assets")
            if not path: return None
            project_save_callback(path)

        # 3. Import OBJ asset
        rel_obj_path = self.import_asset(obj_path)
        abs_obj_path = self.get_full_path(rel_obj_path)

        return rel_obj_path, abs_obj_path

    def import_asset(self, source_path):
        """Copies an external file into the project's asset folder and returns relative path."""
        if not self.current_project_path:
            return source_path
        
        assets_dir = os.path.join(self.current_project_path, "assets")
        if not os.path.exists(assets_dir):
            os.makedirs(assets_dir)
            
        filename = os.path.basename(source_path)
        dest_path = os.path.join(assets_dir, filename)
        
        if os.path.abspath(source_path) != os.path.abspath(dest_path):
            shutil.copy2(source_path, dest_path)
            
        return os.path.join("assets", filename)

    def get_full_path(self, relative_path):
        """Converts an internal project path to an absolute system path."""
        if not self.current_project_path or not relative_path or os.path.isabs(relative_path):
            return relative_path
        return os.path.abspath(os.path.join(self.current_project_path, relative_path))

    def save_to_path(self, project_dir, world_data):
        try:
            json_path = os.path.join(project_dir, self.project_filename)
            with open(json_path, 'w') as f:
                json.dump(world_data, f, indent=4)
            self.current_project_path = project_dir
            return True
        except Exception as e:
            print(f"Failed to save project: {e}")
            return False

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
    
    def open_file_dialog(self, title="Open File", file_types=None):
        return filedialog.askopenfilename(title=title, filetypes=file_types or [("All Files", "*.*")])

    def ask_save_changes(self):
        return messagebox.askyesnocancel("Unsaved Changes", "You have unsaved changes. Save before proceeding?")