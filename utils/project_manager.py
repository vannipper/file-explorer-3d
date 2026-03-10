"""
FileExplorer3D - project_manager.py
Contains the ProjectManager class, which saves and loads project files.
"""

# imports
import os
import pygame

from obj.rectangular_prism import RectangularPrism

class ProjectManager:
    """Manages project lifecycle: new, open, save, and scene modifications."""
    
    def __init__(self, state, world, file_manager, config, version="Pre-Alpha 0.1"):
        self.state = state
        self.world = world
        self.file_manager = file_manager
        self.config = config
        self.version = version

    def update_title(self):
        """Updates the window title with the project name and unsaved change status."""
        path = self.file_manager.current_project_path
        project_name = os.path.basename(path) if path else "Untitled Project"
        asterisk = "*" if self.state.has_unsaved_changes else ""
        pygame.display.set_caption(f"Zenith Engine {self.version} - {project_name}{asterisk}")

    def get_save_data(self):
        """Serializes current scene objects into a dictionary format."""
        objects_data = []
        for obj in self.world.objects:
            objects_data.append({
                "type": "cube", # defaults to cube object
                "x": obj.x, "y": obj.y, "z": obj.z
            })
        return {"objects": objects_data}

    def process_action(self, action, auto_path=None):
        """Handles menu and shortcut actions."""
        if not action: return False
        
        if action == "exit":
            self.handle_exit()
            return False

        if action == "new_project":
            self.world.objects = []
            self.file_manager.current_project_path = None
            self.state.has_unsaved_changes = False
            self.update_title()

        elif action == "open_project":
            path = auto_path or self.file_manager.open_project_dialog()
            if path:
                data = self.file_manager.load_from_path(path)
                if data:
                    self.world.objects = []
                    for d in data.get("objects", []):
                        obj = RectangularPrism(1, 1, 1) # default to cube object
                        obj.set_position(d['x'], d['y'], d['z'])
                        self.world.add_object(obj)
                    
                    self.state.has_unsaved_changes = False
                    self.config.set("last_project_path", path)
                    self.config.save()
                    self.update_title()

        elif action == "save_project" or action == "save_as_project":
            path = self.file_manager.current_project_path if action == "save_project" else None
            path = path or self.file_manager.save_project_dialog()
            if path:
                if self.file_manager.save_to_path(path, self.get_save_data()):
                    self.state.has_unsaved_changes = False
                    self.config.set("last_project_path", path)
                    self.config.save()
                    self.update_title()

        elif action == "add_cube":
            cube = RectangularPrism(1, 1, 1)
            cube.set_position(0, 0.5, 0)
            self.world.add_object(cube)
            self.state.has_unsaved_changes = True
            self.update_title()

        elif action == "delete":
            if self.state.selected_obj:
                self.world.objects.remove(self.state.selected_obj)
                self.state.selected_obj = None
                self.state.has_unsaved_changes = True
                self.update_title()

        return True

    def handle_exit(self):
        """Checks for unsaved changes before quitting."""
        if self.state.has_unsaved_changes:
            res = self.file_manager.ask_save_changes()
            if res is True: # Yes
                path = self.file_manager.current_project_path or self.file_manager.save_project_dialog()
                if path and self.file_manager.save_to_path(path, self.get_save_data()):
                    self.state.running = False
            elif res is False: # No
                self.state.running = False
            # If cancel, do nothing
        else:
            self.state.running = False
