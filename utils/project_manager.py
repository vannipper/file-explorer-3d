"""
FileExplorer3D - project_manager.py
Contains the ProjectManager class, which saves and loads project files.
NOTE: This class won't be used. I am keeping some dummy code for reference
"""

# imports
from pygame.locals import *
from env.rectangular_prism import RectangularPrism

# TODO: Try to make this a static class
class ProjectManager:
    """Manages project lifecycle: new, open, save, and scene modifications."""
    
    def __init__(self, state, file_manager, config, version="Pre-Alpha 0.1"):
        self.state = state
        self.file_manager = file_manager
        self.config = config
        self.version = version

    def open_parent_folder(self): # TODO: Repurpose for opening parent folder
        path = self.file_manager.open_project_dialog()
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
