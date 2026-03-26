"""
FileExplorer3D - world.py
Contains the World class, which manages drawable objects in the 3D environment.
"""

import os
import time
import pygame
from pygame.locals import *
from OpenGL.GL import *

from explorer.selector import Selector
from utils.interaction_handler import InteractionHandler
from utils.directory_scanner import DirectoryScanner


class World:
    DOUBLE_CLICK_MS = 300

    def __init__(self):
        self.objects = []
        self.selected_object = None
        self.selector = Selector()
        self.cursor_visible = False
        self.current_directory = None

        # set by main after construction
        self.player = None
        self.config = None

        # double-click tracking
        self._last_click_time = 0
        self._last_clicked_object = None

    def add_object(self, obj):
        self.objects.append(obj)

    def clear(self):
        """Remove all objects and reset selection."""
        self.objects = []
        self.selected_object = None
        self.selector.stop_drag()
        self._last_click_time = 0
        self._last_clicked_object = None

    def load_directory(self, path):
        """Scan path, populate scene, reset camera, persist to config."""
        success = DirectoryScanner.fill_world(self, path)
        if not success:
            # permission denied — flash the clicked folder red
            if self._last_clicked_object:
                self._last_clicked_object.flash_error()
            return

        if self.config:
            self.config.set('last_opened_folder', path)
            self.config.save()

        if self.player:
            self.player.reset_camera(
                len(self.objects), DirectoryScanner.COLS, DirectoryScanner.SPACING
            )

    def deselect_object(self):
        self.selected_object = None

    def handle_events(self, events):
        for event in events:
            if event.type == KEYDOWN and event.key == K_ESCAPE:
                self.cursor_visible = True
                pygame.mouse.set_visible(True)
                pygame.mouse.set_pos(
                    pygame.display.get_surface().get_width() // 2,
                    pygame.display.get_surface().get_height() // 2,
                )
                self.deselect_object()
                self.selector.stop_drag()

            elif event.type == KEYDOWN and event.key == K_BACKSPACE:
                if self.current_directory and not self.cursor_visible:
                    parent = os.path.dirname(self.current_directory)
                    if parent != self.current_directory:
                        self.load_directory(parent)

            elif event.type == MOUSEBUTTONDOWN and event.button == 1:
                if self.cursor_visible:
                    self.cursor_visible = False
                    pygame.mouse.set_visible(False)
                else:
                    now = time.time() * 1000

                    # Check double-click BEFORE gizmo can intercept
                    if (self._last_clicked_object is not None
                            and now - self._last_click_time < self.DOUBLE_CLICK_MS):
                        target = Selector.pick_object(self.objects)
                        if target is self._last_clicked_object:
                            self._handle_double_click(target)
                            self._last_clicked_object = None
                            self._last_click_time = 0
                            continue

                    # Normal selection (includes gizmo interaction)
                    clicked = self.selector.handle_selection(
                        self.objects, self.selected_object
                    )
                    if self.selector.active_axis is not None:
                        continue

                    self.selected_object = clicked
                    self._last_clicked_object = clicked
                    self._last_click_time = now

            elif event.type == MOUSEBUTTONUP and event.button == 1:
                self.selector.stop_drag()

            if self.selector.active_axis and self.selected_object:
                mpos = InteractionHandler.GetMousePosition()
                ray_o, ray_d = InteractionHandler.GetRay(mpos[0], mpos[1])
                new_pos = self.selector.update_drag(ray_o, ray_d)
                if new_pos is not None:
                    self.selected_object.set_position(*new_pos)

    def _handle_double_click(self, obj):
        """Enter a folder on double-click; no-op for files."""
        if hasattr(obj, 'is_dir') and obj.is_dir:
            self.load_directory(obj.file_path)
