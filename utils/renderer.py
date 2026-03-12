"""
FileExplorer3D - renderer.py
Contains the Renderer class, which handles the rendering of objects
"""

# imports
from pygame.locals import *
from utils.interaction_handler import InteractionHandler

class Renderer:
    @staticmethod
    def RenderObjects(objects): #TODO: Write method
        pass

    @staticmethod
    def RenderAxes(axes): #TODO: Write method
        pass

    @staticmethod
    def handle_events(events):
        for event in events:
            if event.type == VIDEORESIZE:
                InteractionHandler.ResizeWindow(event.size)
                return event.size
        return 1280, 720