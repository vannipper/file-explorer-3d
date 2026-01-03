import os
import pygame
from pygame.locals import *
from obj.rectangular_prism import RectangularPrism

class ProjectManager:
    """Handles file I/O, window titles, and project persistence."""
    def __init__(self, state, world, file_manager, config):
        self.state = state
        self.world = world
        self.file_manager = file_manager
        self.config = config

    def update_title(self):
        path = self.file_manager.current_file_path
        project_name = os.path.basename(path) if path else "Untitled Project"
        asterisk = "*" if self.state.has_unsaved_changes else ""
        pygame.display.set_caption(f"Zenith Engine - {project_name}{asterisk}")

    def get_save_data(self):
        return {
            "objects": [{"type": "cube", "x": o.x, "y": o.y, "z": o.z} for o in self.world.objects]
        }

    def process_action(self, action, auto_path=None):
        """Processes menu actions and returns a 'force_editor' flag if needed."""
        if not action or action == "STAY_OPEN": return False
        
        if action == "exit":
            self.handle_exit()
            return False

        # Determine if we need to show a dialog
        is_dialog = action in ["new_project", "open_project", "save_as_project"]
        if action == "save_project" and self.file_manager.current_file_path is None:
            is_dialog = True

        if is_dialog:
            pygame.event.set_grab(False)
            pygame.mouse.set_visible(True)
            pygame.event.pump()

        if action == "new_project":
            self.world.objects = []
            self.file_manager.current_file_path = None
            self.state.has_unsaved_changes = False
            self.config.set("last_project_path", None)
            self.config.save()
            self.update_title()

        elif action == "open_project":
            path = auto_path or self.file_manager.open_file_dialog()
            if path:
                data = self.file_manager.load_from_path(path)
                if data:
                    self.world.objects = []
                    for obj_data in data.get("objects", []):
                        cube = RectangularPrism(1, 1, 1)
                        cube.set_position(obj_data['x'], obj_data['y'], obj_data['z'])
                        self.world.add_object(cube)
                    self.state.has_unsaved_changes = False
                    self.config.set("last_project_path", path)
                    self.config.save()
                    self.update_title()

        elif action == "save_project" or action == "save_as_project":
            path = self.file_manager.current_file_path if action == "save_project" else None
            path = path or self.file_manager.save_file_dialog()
            if path:
                if self.file_manager.save_to_path(path, self.get_save_data()):
                    self.state.has_unsaved_changes = False
                    self.config.set("last_project_path", path)
                    self.config.save()
                    self.update_title()

        elif action == "add_cube":
            new_cube = RectangularPrism(1.0, 1.0, 1.0)
            new_cube.set_position(0, 0.5, 0)
            self.world.add_object(new_cube)
            self.state.has_unsaved_changes = True
            self.update_title()

        elif action == "delete":
            if self.state.selected_obj and self.state.selected_obj in self.world.objects:
                self.world.objects.remove(self.state.selected_obj)
                self.state.selected_obj = None
                self.state.has_unsaved_changes = True
                self.update_title()

        # Focus Management: Ping OS to bring window back to front
        if is_dialog:
            surf = pygame.display.get_surface()
            if surf:
                pygame.display.set_mode(surf.get_size(), DOUBLEBUF | OPENGL | RESIZABLE)
            return True # Signal force_editor

        return False

    def handle_exit(self):
        if self.state.has_unsaved_changes:
            pygame.event.set_grab(False)
            pygame.mouse.set_visible(True)
            res = self.file_manager.ask_save_changes()
            if res is True:
                self.process_action("save_project")
                self.state.running = False
            elif res is False:
                self.state.running = False
            else: # Cancel
                if not self.state.editor_mode:
                    pygame.event.set_grab(True)
                    pygame.mouse.set_visible(False)
        else:
            self.state.running = False