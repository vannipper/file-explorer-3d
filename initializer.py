"""
FileExplorer3D - initializer.py
Contains the EngineInitializer class, which handles all Pygame, OpenGL, etc. initialization.
"""

# imports
import os
import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *

class EngineInitializer:
    """Sets up OS-specific requirements, the window, and OpenGL context."""
    
    VERSION = "Pre-Alpha 0.1"
    
    def __init__(self, config):
        # TODO: Remove any class properties that aren't necessary
        self.config = config
        self.width = 0
        self.height = 0
        self.display_info = None
        self.splash_active = False
        self.splash_start_time = None
        self.splash_surface = None
        self.splash_image = None
        self.splash_size = (0, 0)
        self.world = None
        self.player = None
        self.menu_bar = None
        self.gizmo = None
        self.file_manager = None
        self.project_manager = None

    def initialize_pygame(self):
        """Initialize Pygame and display info."""
        pygame.init()
        self.display_info = pygame.display.Info()
        
    def initialize_engine_components(self, state):
        """Initialize all engine components (world, player, etc.)."""
        
        # import here to avoid circular dependencies
        # TODO: Move imports to the top of the file
        from obj.world import World
        from obj.player import Player
        from editor.gizmo import Gizmo
        from utils.file_manager import FileManager
        from utils.project_manager import ProjectManager
        
        self.world = World(self.config)
        self.player = Player(self.config)
        self.gizmo = Gizmo()
        self.file_manager = FileManager()
        self.project_manager = ProjectManager(state, self.world, self.file_manager, self.config, self.VERSION)
        
        return self.world, self.player, self.gizmo, self.file_manager, self.project_manager

    def finalize_engine_window(self):
        """Creates OpenGL window minimized so splash stays visible."""
        if not self.display_info or self.display_info.current_w == -1:
            self.display_info = pygame.display.Info()
        
        self.width = self.display_info.current_w
        self.height = self.display_info.current_h
        os.environ['SDL_VIDEO_WINDOW_POS'] = "0,0"
        
        pygame.display.set_mode((self.width, self.height), DOUBLEBUF | OPENGL | RESIZABLE)
        pygame.display.set_caption(f"Zenith Engine {self.VERSION}")
        
        # self._set_app_icon("zenith_ico_DRAFT.png") # TODO: Change this path to FileExplorer3D .png
        self._setup_opengl()
        
        return self.width, self.height
    
    # TODO: Project loading will likely be unnecessary for this app. Remove this function
    def load_last_project(self):
        """Load the last opened project if it exists."""
        last_path = self.config.get("last_project_path")
        
        if last_path and os.path.exists(last_path):
            self.project_manager.process_action("open_project", auto_path=last_path)
            return True
        else:
            self.project_manager.update_title()
            return False

    def _set_app_icon(self, icon_path):
        """Sets the window icon after the display mode is established."""
        try:
            if os.path.exists(icon_path):
                icon_surface = pygame.image.load(icon_path)
                pygame.display.set_icon(icon_surface)
        except Exception as e:
            print(f"Initializer: Icon load failed: {e}")

    def _setup_opengl(self):
        """Sets up the initial OpenGL state."""
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glEnable(GL_DEPTH_TEST)
        glClearColor(0.1, 0.1, 0.15, 1.0)
