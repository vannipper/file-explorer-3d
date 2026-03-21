"""
FileExplorer3D - main.py
This is the main file which contains all module calls and the main loop.
"""

# pip imports
import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
from config.config import Config
from utils.file_manager import FileManager
from utils.initializer import EngineInitializer
from utils.interaction_handler import InteractionHandler
from utils.renderer import Renderer
from utils.directory_scanner import DirectoryScanner

if __name__ == "__main__":
    
    # load config
    config = Config()
    config.load()

    # load root folder
    root_folder = FileManager.open_file_dialog(config)
    if not root_folder:
        exit(1)

    # initialize Pygame
    EngineInitializer.InitializePygame()
    clock = pygame.time.Clock()

    # initialize engine components
    EngineInitializer.load_last_project(config)
    world, player, selector, file_manager = EngineInitializer.InitializeEngineComponents(config)

    # video variables
    win_w, win_h = EngineInitializer.InitializeOpenGLWindow()
    mpos = InteractionHandler.GetMousePosition()

    # populate world with objects
    DirectoryScanner.fill_world(world, root_folder)
    
    # main loop
    run = True
    while run:
        dt = clock.tick(60) / 1000.0

        # Handle Pygame events
        events = pygame.event.get()
        
        new_folder = FileManager.handle_events(events, root_folder)
        if new_folder != root_folder:
            root_folder = new_folder
            DirectoryScanner.fill_world(world, root_folder)

        run = player.handle_events(events)
        world.handle_events(events)

        new_size = Renderer.handle_events(events)
        if new_size:
            win_w, win_h = new_size
        
        # update player
        player.update(dt)

        # Rendering pipeline
        Renderer.SetupFrame(win_w, win_h, config)
        player.apply_look()
        
        if config.get('should_draw_grid', True): #TODO: Add this to config class
            Renderer.DrawGrid()
        for obj in world.objects:
            Renderer.DrawObject(obj, world.selected_object)
        if config.get('should_draw_axes', True): #TODO: Add this to config class
            Renderer.DrawAxes()

        Renderer.DrawSelectedLabel(world.selected_object, win_w, win_h)
        Renderer.DrawCrosshair(win_w, win_h)

        # Flip display buffer
        pygame.display.flip()

    pygame.quit()
