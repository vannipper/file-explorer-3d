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

class EngineInitializer:
    """Sets up OS-specific requirements, the window, and OpenGL context."""

    @staticmethod
    def InitializePygame():
        pygame.init()
    
    @staticmethod
    def InitializeEngineComponents(config):
        """Initialize all engine components (world, player, etc.)."""
        
        world = World()
        player = Player(config)
        selector = Selector()

        return world, player, selector, None

    # self._set_app_icon("zenith_ico_DRAFT.png") # TODO: Change this path to FileExplorer3D .png

    @staticmethod
    def InitializeOpenGLWindow(config):
        win_w = config.get('window_width', 1280)
        win_h = config.get('window_height', 720)

        pygame.display.set_mode((win_w, win_h), DOUBLEBUF | OPENGL | RESIZABLE)
        pygame.display.set_caption("FileExplorer3D")
        project_root = os.path.dirname(os.path.dirname(__file__))
        icon_path = os.path.join(project_root, "fileexplorer3d_icon.png")
        EngineInitializer.setAppIcon(icon_path)
        pygame.mouse.set_visible(False)
        pygame.event.set_grab(True)

        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glEnable(GL_DEPTH_TEST)
        glClearColor(0.1, 0.1, 0.15, 1.0)

        # Return actual framebuffer size (differs from logical size on Retina)
        viewport = glGetIntegerv(GL_VIEWPORT)
        return int(viewport[2]), int(viewport[3])
    
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
