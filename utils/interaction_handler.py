"""
FileExplorer3D - interaction_handler.py
Contains the InteractionHandler class, which handles the user's interaction screen.
"""

# imports
import numpy as np
from OpenGL.GL import *
from OpenGL.GLU import *

class InteractionHandler:
    """Handles 3D math, raycasting, and object selection."""
    @staticmethod
    def get_ray(mouse_x, mouse_y):
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
