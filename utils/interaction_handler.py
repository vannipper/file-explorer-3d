import pygame
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

    @staticmethod
    def is_mouse_in_ui(menu_bar, mpos):
        if mpos[1] <= menu_bar.height: return True
        for item in menu_bar.items:
            if item.is_open and item.children:
                r = item.children[0].rect
                if pygame.Rect(r.left, r.top, item.submenu_width, item.submenu_height).collidepoint(mpos):
                    return True
        return False