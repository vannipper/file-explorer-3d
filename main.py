"""
FileExplorer3D - main.py
This is the main file which contains all module calls and the main loop.
"""

import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
from config.config import Config
from utils.file_manager import FileManager
from utils.initializer import EngineInitializer
from utils.renderer import Renderer

if __name__ == "__main__":
    config = Config()

    # Select root folder before Pygame starts (tkinter dialog)
    root_folder = FileManager.open_folder_dialog(config)
    if not root_folder:
        exit(1)

    # Initialize Pygame & OpenGL
    EngineInitializer.InitializePygame()
    clock = pygame.time.Clock()

    world, player, selector, _ = EngineInitializer.InitializeEngineComponents(config)
    world.player = player
    world.config = config

    win_w, win_h = EngineInitializer.InitializeOpenGLWindow(config)
    _surf = pygame.display.get_surface()
    win_w, win_h = _surf.get_width(), _surf.get_height()

    # Load initial directory
    world.load_directory(root_folder)

    # Main loop
    run = True
    while run:
        dt = clock.tick(60) / 1000.0
        events = pygame.event.get()

        new_folder = FileManager.handle_events(events, world.current_directory, config)
        if new_folder != world.current_directory:
            world.load_directory(new_folder)

        run = player.handle_events(events)
        world.handle_events(events)

        new_size = Renderer.handle_events(events)
        if new_size:
            win_w, win_h = new_size
            logical_w, logical_h = pygame.display.get_surface().get_size()
            config.set('window_width', logical_w)
            config.set('window_height', logical_h)
            config.save()

        player.update(dt, win_w, win_h)
        world.update()

        # Rendering
        Renderer.SetupFrame(win_w, win_h, config)
        player.apply_look()

        if config.get('show_grid', True):
            Renderer.DrawGrid()
        for obj in world.objects:
            Renderer.DrawObject(obj, world.selected_object)
        if config.get('show_axes', True):
            Renderer.DrawAxes()

        Renderer.DrawNavArrows(world.nav_stack, win_w, win_h)
        Renderer.DrawSelectedLabel(world.selected_object, win_w, win_h)
        if world.selected_object:
            meta = world.metadata_cache.get(world.selected_object.file_path)
            Renderer.DrawInfoPanel(world.selected_object, meta, win_w, win_h)
        if world.show_hover_tooltip and world.selected_object:
            meta = world.metadata_cache.get_if_cached(world.selected_object.file_path)
            Renderer.DrawHoverTooltip(world.selected_object, meta, win_w, win_h)
        Renderer.DrawCrosshair(win_w, win_h)

        pygame.display.flip()

    pygame.quit()
