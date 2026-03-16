"""
FileExplorer3D - world.py
Contains the World class, which manages drawable objects in the 3D environment.
"""

# imports
import pygame
from pygame.locals import *
from OpenGL.GL import *

from explorer.selector import Selector
from utils.interaction_handler import InteractionHandler

class World:
    def __init__(self):
        self.objects = []
        self.selected_object = None
        self.selector = Selector()
        self.cursor_visible = False

    def add_object(self, obj):
        """Add a drawable object to the world."""
        self.objects.append(obj)

    def deselect_object(self):
        self.selected_object = None

    def delete_object(self, obj):
        self.objects.remove(obj)
        self.deselect_object()
        
    def handle_events(self, events):
        for event in events:
            if event.type == KEYDOWN and event.key == K_ESCAPE:
                self.cursor_visible = True
                pygame.mouse.set_visible(True)
                pygame.mouse.set_pos(pygame.display.get_surface().get_width() // 2, 
                                    pygame.display.get_surface().get_height() // 2)
                self.deselect_object()
                self.selector.stop_drag()
            
            elif event.type == MOUSEBUTTONDOWN and event.button == 1:
                if self.cursor_visible:
                    self.cursor_visible = False
                    pygame.mouse.set_visible(False)
                else:
                    self.selector.handle_selection(self.objects, self.selected_object)

            elif event.type == MOUSEBUTTONUP and event.button == 1:
                self.selector.stop_drag()

            if self.selector.active_axis and self.selected_object:
                mpos = InteractionHandler.GetMousePosition()
                ray_o, ray_d = InteractionHandler.GetRay(mpos[0], mpos[1])
                new_pos = self.selector.update_drag(ray_o, ray_d)
                if new_pos:
                    self.selected_object.set_position(*new_pos)
