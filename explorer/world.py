"""
FileExplorer3D - world.py
Contains the World class, which manages drawable objects in the 3D environment.
"""

# imports
from pygame.locals import *
from OpenGL.GL import *

from explorer.selector import Selector
from utils.interaction_handler import InteractionHandler

# TODO: Inspect if this class is used
class World:
    def __init__(self, config):
        self.objects = []
        self.selected_obj = None
        self.selector = Selector()
        self.should_draw_axes = config.get("show_axes", True)

    def add_object(self, obj):
        """Add a drawable object to the world."""
        self.objects.append(obj)

    def deselect_object(self):
        self.selected_obj = None

    def delete_object(self, obj):
        self.objects.remove(obj)
        self.deselect_object()
    
    def draw_axes(self):
        """Draw world-space coordinate axes with higher priority (always on top)."""
        if not self.should_draw_axes:
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
        if not self.draw_axes:
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
        
        # NOTE: Object drawing is now handled in the main render loop 
        # to allow for selection highlighting and gizmos.
        for obj in self.objects:
            glPushMatrix()
            glTranslatef(obj.x, obj.y, obj.z)
            obj.draw()
            glPopMatrix()

    def handle_events(self, events):
        for event in events:
            if event.type == KEYDOWN and event.key == K_ESCAPE:
                self.deselect_object()
                self.selector.stop_drag()
            
            elif event.type == MOUSEBUTTONDOWN and event.button == 1:
                self.selector.handle_selection() # TODO: write this code
            elif event.type == MOUSEBUTTONUP and event.button == 1:
                self.selector.stop_drag()

            if self.selector.active_axis and self.selected_obj:
                mpos = InteractionHandler.GetMousePosition()
                ray_o, ray_d = InteractionHandler.get_ray(mpos[0], mpos[1])
                new_pos = self.selector.update_drag(ray_o, ray_d)
                if new_pos:
                    self.selected_obj.set_position(*new_pos)
