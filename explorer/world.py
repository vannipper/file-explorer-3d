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
from explorer.file_tree_node import make_root
from explorer.file_index import FileIndex
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

        self.file_index = FileIndex()

    def add_object(self, obj):
        self.objects.append(obj)

    def clear(self):
        """Remove all objects and reset selection."""
        self.objects = []
        self.selected_object = None
        self.file_index.clear()
        self.selector.stop_drag()
        self._last_click_time = 0
        self._last_clicked_object = None

    def load_directory(self, path):
        """Scan path, populate scene, reset camera, persist to config."""
        node = make_root(path)
        success = DirectoryScanner.fill_world_from_node(self, node)
        if not success:
            if self._last_clicked_object:
                self._last_clicked_object.flash_error()
            return

        self.file_index.build(self.objects)

        if self.config:
            self.config.set('last_opened_folder', path)
            self.config.save()

        if self.player:
            self.player.reset_camera(
                len(self.objects), DirectoryScanner.COLS, DirectoryScanner.SPACING
            )

    def deselect_object(self):
        self.selected_object = None

    def delete_object(self, obj):
        self.file_index.delete(obj.file_name, obj.file_path)
        self.objects.remove(obj)
        self.deselect_object()

    def update(self):
        """Per-frame hover-selection: highlight whichever object the crosshair aims at."""
        if not self.cursor_visible:
            self.selected_object = self.selector.handle_selection(self.objects)

    def _activate_selected(self):
        """Called on click. Prints the file tree rooted at the selected object."""
        obj = self.selected_object
        if obj is None:
            return

        print(f"\n── {obj.file_name}")
        if obj.is_dir:
            node = make_root(obj.file_path)
            node.expand()
            self._print_tree(node, prefix="   ")
        print()

    def _print_tree(self, node, prefix=""):
        children = node.get_children()
        for i, child in enumerate(children):
            connector = "└── " if i == len(children) - 1 else "├── "
            print(f"{prefix}{connector}{child.name}")
            if child.is_dir:
                extension = "    " if i == len(children) - 1 else "│   "
                self._print_tree(child, prefix + extension)

    def handle_events(self, events):
        for event in events:
            if event.type == KEYDOWN and event.key == K_ESCAPE:
                self.cursor_visible = True
                pygame.mouse.set_visible(True)
                pygame.event.set_grab(False)
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

                    if (self._last_clicked_object is not None
                            and now - self._last_click_time < self.DOUBLE_CLICK_MS):
                        target = Selector.pick_object(self.objects)
                        if target is self._last_clicked_object:
                            if hasattr(target, 'is_dir') and target.is_dir:
                                self.load_directory(target.file_path)
                            self._last_clicked_object = None
                            self._last_click_time = 0
                            continue

                    clicked = self.selector.handle_selection(self.objects)

                    self.selected_object = clicked
                    self._last_clicked_object = clicked
                    self._last_click_time = now
                    self._activate_selected()
                    pygame.event.set_grab(True)

            elif event.type == MOUSEBUTTONUP and event.button == 1:
                self.selector.stop_drag()
