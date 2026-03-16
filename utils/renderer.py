"""
FileExplorer3D - renderer.py
Contains the Renderer class, which handles the rendering of objects
"""

# imports
import numpy as np
from pygame.locals import *
from utils.interaction_handler import InteractionHandler
from OpenGL.GL import *
from OpenGL.GLU import *

class Renderer:
    @staticmethod
    def handle_events(events):
        for event in events:
            if event.type == VIDEORESIZE:
                InteractionHandler.ResizeWindow(*event.size)
                return event.size
        return 1280, 720

    @staticmethod
    def SetupFrame(win_w, win_h, config):
        glViewport(0, 0, win_w, win_h)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glEnable(GL_DEPTH_TEST)
        
        glEnable(GL_LIGHTING); glEnable(GL_LIGHT0); glEnable(GL_COLOR_MATERIAL)
        glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)
        glLightfv(GL_LIGHT0, GL_POSITION, [5, 10, 5, 1])
        
        glMatrixMode(GL_PROJECTION); glLoadIdentity()
        aspect = win_w / win_h if win_h > 0 else 1
        gluPerspective(config.get("fov", 70), aspect, 0.1, 1000.0)
        
        glMatrixMode(GL_MODELVIEW); glLoadIdentity()

    @staticmethod
    def DrawGrid(size=20, step=1):
        glDisable(GL_LIGHTING)
        glColor3f(0.3, 0.3, 0.3)
        glBegin(GL_LINES)
        for i in range(-size, size + 1, step):
            # lines parallel to X
            glVertex3f(-size, 0, i)
            glVertex3f(size, 0, i)
            # lines parallel to Z
            glVertex3f(i, 0, -size)
            glVertex3f(i, 0, size)
        glEnd()
        glEnable(GL_LIGHTING)

    @staticmethod
    def DrawObject(object, selected_object):
        glPushMatrix()
        glTranslatef(object.x, object.y, object.z)
        if object == selected_object:
            glPushAttrib(GL_LIGHTING_BIT)
            glMaterialfv(GL_FRONT, GL_EMISSION, [0.0, 0.2, 0.0, 1.0])
            glColor3f(0.4, 1.0, 0.4)
            object.draw()
            glPopAttrib()
        else:
            glMaterialfv(GL_FRONT, GL_EMISSION, [0.0, 0.0, 0.0, 1.0])
            object.draw()
        glPopMatrix()

    @staticmethod
    def DrawAxes():
        # Disable depth testing so axes are always visible
        glDisable(GL_DEPTH_TEST)
        glDisable(GL_LIGHTING)
        
        glLineWidth(2.0)  # Make axes slightly thicker for visibility
        glBegin(GL_LINES)
        # X axis (red)
        glColor3f(1, 0, 0)
        glVertex3f(0, 0, 0)
        glVertex3f(5, 0, 0)

        # Y axis (green)
        glColor3f(0, 1, 0)
        glVertex3f(0, 0, 0)
        glVertex3f(0, 5, 0)

        # Z axis (blue)
        glColor3f(0, 0, 1)
        glVertex3f(0, 0, 0)
        glVertex3f(0, 0, 5)
        glEnd()
        glLineWidth(1.0)
        
        # Re-enable depth testing for everything else
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_LIGHTING)

    @staticmethod
    def HighlightSelectedObject(selected_object, selector): # TODO: Find out what this does
        glDisable(GL_DEPTH_TEST)
        selector.draw(np.array([selected_object.x, selected_object.y, selected_object.z]))
        glColor3f(1.0, 1.0, 1.0)
        glEnable(GL_DEPTH_TEST)
        glDisable(GL_LIGHTING); glDisable(GL_DEPTH_TEST)
