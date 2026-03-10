"""
FileExplorer3D - world.py
Contains the World class, which manages drawable objects in the 3D environment.
"""

# imports
from OpenGL.GL import *

# TODO: Inspect if this class is used
class World:
    def __init__(self, config=None):
        self.objects = []
        self.config = config
    
    def add_object(self, obj):
        """Add a drawable object to the world."""
        self.objects.append(obj)
    
    def draw_axes(self):
        """Draw world-space coordinate axes with higher priority (always on top)."""
        if self.config and not self.config.get("show_axes", True):
            return
        
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
    
    def draw_floor(self, size=20, step=1):
        """Draw a grid floor."""
        if self.config and not self.config.get("show_grid", True):
            return
        
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
    
    def draw_all(self):
        """Draw floor and axes."""
        self.draw_floor()
        self.draw_axes()
        
        # Note: Object drawing is now handled in the main render loop 
        # to allow for selection highlighting and gizmos.
        for obj in self.objects:
            glPushMatrix()
            glTranslatef(obj.x, obj.y, obj.z)
            obj.draw()
            glPopMatrix()