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
from explorer.world import World
from env.player import Player
from explorer.selector import Selector
from utils.file_manager import FileManager

VERSION = "- *Development"

class EngineInitializer:
    """Sets up OS-specific requirements, the window, and OpenGL context."""

    @staticmethod
    def InitializePygame():
        """Initialize Pygame and display info."""
        pygame.init()
        pygame.mouse.set_visible(False)
    
    @staticmethod
    def InitializeEngineComponents(config):
        """Initialize all engine components (world, player, etc.)."""
        
        world = World(config)
        player = Player(config)
        selector = Selector()
        file_manager = FileManager()
        
        return world, player, selector, file_manager

    @staticmethod
    def InitializeOpenGLWindow():
        """Creates OpenGL window minimized so splash stays visible."""
        di = pygame.display.Info()
    
        os.environ['SDL_VIDEO_WINDOW_POS'] = "0,0"
        pygame.display.set_mode((di.current_w, di.current_h), DOUBLEBUF | OPENGL | RESIZABLE)
        pygame.display.set_caption(f"FileExplorer3D {VERSION}")
        
        # self._set_app_icon("zenith_ico_DRAFT.png") # TODO: Change this path to FileExplorer3D .png

        # setup openGL 
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glEnable(GL_DEPTH_TEST)
        glClearColor(0.1, 0.1, 0.15, 1.0)
        
        return di.current_w, di.current_h
    
    # TODO: Repurpose this to loading the last opened parent folder
    @staticmethod
    def load_last_project(config):
        """Load the last opened project if it exists."""
        last_path = config.get("last_project_path")

    @staticmethod
    def setAppIcon(icon_path):
        """Sets the window icon after the display mode is established."""
        try:
            if os.path.exists(icon_path):
                icon_surface = pygame.image.load(icon_path)
                pygame.display.set_icon(icon_surface)
        except Exception as e:
            print(f"Initializer: Icon load failed: {e}")

    @staticmethod
    def setupOpenGL():
        """Sets up the initial OpenGL state."""
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glEnable(GL_DEPTH_TEST)
        glClearColor(0.1, 0.1, 0.15, 1.0)
