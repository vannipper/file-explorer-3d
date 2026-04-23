"""
FileExplorer3D - interaction_handler.py
Contains the InteractionHandler class, which handles the user's interaction with the app.
"""

# imports
import pygame
import numpy as np
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *

class InteractionHandler:
    @staticmethod
    def CtrlPressed():
        return pygame.key.get_mods() & (KMOD_CTRL | KMOD_META)
    
    @staticmethod
    def ShiftPressed():
        return pygame.key.get_mods() & (KMOD_SHIFT)

    @staticmethod
    def GetMousePosition():
        return pygame.mouse.get_pos()
    
    @staticmethod
    def ResizeWindow(newWidth, newHeight):
        newWidth  = max(newWidth,  200)
        newHeight = max(newHeight, 150)
        pygame.display.set_mode((newWidth, newHeight), DOUBLEBUF | OPENGL | RESIZABLE)
        if not pygame.mouse.get_visible():
            pygame.event.set_grab(True)
            cx, cy = newWidth // 2, newHeight // 2
            pygame.mouse.set_pos(cx, cy)

    @staticmethod
    def GetRay(mouse_x, mouse_y):
        modelview = glGetDoublev(GL_MODELVIEW_MATRIX)
        projection = glGetDoublev(GL_PROJECTION_MATRIX)
        viewport = glGetIntegerv(GL_VIEWPORT)
        real_y = viewport[3] - mouse_y
        try:
            near = gluUnProject(mouse_x, real_y, 0.0, modelview, projection, viewport)
            far = gluUnProject(mouse_x, real_y, 1.0, modelview, projection, viewport)
            ray_o = np.array(near)
            ray_d = np.array(far) - ray_o
            norm = np.linalg.norm(ray_d)
            return ray_o, (ray_d / norm if norm > 0 else ray_d)
        except:
            return np.array([0,0,0]), np.array([0,0,-1])