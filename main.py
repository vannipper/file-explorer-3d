"""
FileExplorer3D - main.py
Main entry point: initializes engine components and runs the main loop.
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

    EngineInitializer.InitializePygame()
    clock = pygame.time.Clock()

    world, player, selector, _ = EngineInitializer.InitializeEngineComponents(config)
    world.player = player
    world.config = config
    world.load_bookmarks_from_config()

    win_w, win_h = EngineInitializer.InitializeOpenGLWindow(config)

    if world.bookmarks_panel_visible:
        world.cursor_visible = True
        pygame.mouse.set_visible(True)
        pygame.event.set_grab(False)

    world.request_directory_load(FileManager.resolve_startup_directory(config), new_root=True)

    run = True
    while run:
        dt = clock.tick(60) / 1000.0
        events = pygame.event.get()

        new_folder = None
        if not world.is_loading:
            new_folder = FileManager.handle_events(events, world.current_directory, config)
        if new_folder:
            world.request_directory_load(new_folder, new_root=True)

        run = player.handle_events(events)
        world.handle_events(events)

        new_size = Renderer.handle_events(events)
        if new_size:
            win_w, win_h = new_size
            logical_w, logical_h = pygame.display.get_surface().get_size()
            config.set('window_width', logical_w)
            config.set('window_height', logical_h)
            config.save()

        player.update(dt)
        world.update()

        Renderer.SetupFrame(win_w, win_h, config)
        player.apply_look()

        if config.get('show_grid', True):
            Renderer.DrawGrid()
        for obj in world.objects:
            Renderer.DrawObject(obj, world.selected_object, world.is_bookmarked(obj.file_path))
        if config.get('show_axes', True):
            Renderer.DrawAxes()

        Renderer.DrawNavArrows(world.nav_stack, win_w, win_h)
        Renderer.DrawBookmarksPanel(world, win_w, win_h)
        if world.is_loading:
            Renderer.DrawLoadingBadge(world.loading_message, win_w, win_h)
        if world.selected_object:
            meta = world.metadata_cache.get(world.selected_object.file_path)
            Renderer.DrawInfoPanel(world.selected_object, meta, win_w, win_h)
        if world.show_hover_tooltip and world.selected_object and not world.selected_object.is_dir:
            meta = world.metadata_cache.get_if_cached(world.selected_object.file_path)
            Renderer.DrawHoverTooltip(world.selected_object, meta, win_w, win_h)
        if world.selected_object and world.hover_preview_children is not None:
            Renderer.DrawDirectoryPreview(
                world.selected_object,
                world.hover_preview_children,
                win_w, win_h,
                world.hover_preview_name
            )
        Renderer.DrawCrosshair(win_w, win_h)
        Renderer.DrawShortcutsPopup(world.shortcuts_popup_visible, win_w, win_h)

        pygame.display.flip()
        world.process_pending_directory_load()

    world.sync_bookmarks_to_config()
    pygame.quit()
