"""
FileExplorer3D - rectangular_prism.py
Contains the RectangularPrism class.
"""

# imports
from OpenGL.GL import *

class RectangularPrism:
    """A 3D rectangular prism (box) with customizable dimensions."""
    
    def __init__(self, width=2.0, height=2.0, depth=2.0):
        self.width = width
        self.height = height
        self.depth = depth
        self.x = 0.0
        self.y = 0.0
        self.z = 0.0
    
    def set_position(self, x, y, z):
        """Set the position of the prism's center."""
        self.x = x
        self.y = y
        self.z = z
    
    def draw(self):
        """Draw the rectangular prism using OpenGL."""
        w, h, d = self.width / 2, self.height / 2, self.depth / 2
        
        glBegin(GL_QUADS)
        
        # front face (positive Z)
        glColor3f(1, 0, 0)
        glVertex3f(-w, -h, d)
        glVertex3f(w, -h, d)
        glVertex3f(w, h, d)
        glVertex3f(-w, h, d)
        
        # back face (negative Z)
        glColor3f(0, 1, 0)
        glVertex3f(-w, -h, -d)
        glVertex3f(-w, h, -d)
        glVertex3f(w, h, -d)
        glVertex3f(w, -h, -d)
        
        # left face (negative X)
        glColor3f(0, 0, 1)
        glVertex3f(-w, -h, -d)
        glVertex3f(-w, -h, d)
        glVertex3f(-w, h, d)
        glVertex3f(-w, h, -d)
        
        # right face (positive X)
        glColor3f(1, 1, 0)
        glVertex3f(w, -h, -d)
        glVertex3f(w, h, -d)
        glVertex3f(w, h, d)
        glVertex3f(w, -h, d)
        
        # top face (positive Y)
        glColor3f(1, 0, 1)
        glVertex3f(-w, h, -d)
        glVertex3f(-w, h, d)
        glVertex3f(w, h, d)
        glVertex3f(w, h, -d)
        
        # bottom face (negative Y)
        glColor3f(0, 1, 1)
        glVertex3f(-w, -h, -d)
        glVertex3f(w, -h, -d)
        glVertex3f(w, -h, d)
        glVertex3f(-w, -h, d)
        
        glEnd()
