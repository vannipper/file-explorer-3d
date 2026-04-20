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
import numpy as np
from utils.directory_scanner import DirectoryScanner
from utils.interaction_handler import InteractionHandler
from utils.metadata_cache import MetadataCache
from utils.navigation_stack import NavigationStack


# ── module-level helper (no GL imports needed) ────────────────────────────

def _pick_preview_cube(folder_obj, children):
    """
    Raycast from the crosshair against the mini preview cube grid above
    folder_obj.  Returns the name of the hit entry, or None.

    Mirrors the layout constants in Renderer.DrawDirectoryPreview exactly so
    the hit-test matches what is drawn.
    """

    MAX_ITEMS  = 30
    COLS       = 6
    CUBE_SIZE  = 0.18
    CUBE_GAP   = 0.46
    LIFT       = 0.55

    base_y  = folder_obj.y + folder_obj.height / 2 + LIFT + CUBE_SIZE
    grid_w  = COLS * CUBE_GAP
    start_x = folder_obj.x - grid_w / 2 + CUBE_GAP / 2
    start_z = folder_obj.z

    mpos = InteractionHandler.GetMousePosition()
    ray_o, ray_d = InteractionHandler.GetRay(mpos[0], mpos[1])

    shown   = children[:MAX_ITEMS]
    best    = None
    min_d   = float("inf")
    HIT_R   = CUBE_SIZE * 1.6   # slightly generous hit radius

    for i, entry in enumerate(shown):
        col = i % COLS
        row = i // COLS
        cx  = start_x + col * CUBE_GAP
        cy  = base_y  + row * CUBE_GAP
        cz  = start_z

        cube_pos = np.array([cx, cy, cz])
        dist = np.linalg.norm(np.cross(ray_d, ray_o - cube_pos))
        if dist < HIT_R:
            depth = np.dot(ray_d, cube_pos - ray_o)
            if 0 < depth < min_d:
                min_d = depth
                best  = entry.name

    return best

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

        # navigation history (Unit 7 — Stacks)
        self.nav_stack = NavigationStack()

        # metadata cache (Unit 11 — Dicts)
        self.metadata_cache = MetadataCache()

        # hover tooltip tracking
        self._hover_object = None
        self._hover_start  = 0.0
        self.show_hover_tooltip = False

        # directory preview (mini 3-D grid shown above a hovered folder)
        self.hover_preview_children: list | None = None
        self._hover_preview_path: str | None = None
        # name of the mini-cube currently under the crosshair (or None)
        self.hover_preview_name: str | None = None

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

    def load_directory(self, path, push_nav=True):
        """Scan path, populate scene, reset camera, persist to config.

        push_nav=False is used internally by go_back/go_forward so that
        the navigation stack is not updated a second time (the stack
        already moved current_path before calling this method).
        """
        node = make_root(path)
        success = DirectoryScanner.fill_world_from_node(self, node)
        if not success:
            if self._last_clicked_object:
                self._last_clicked_object.flash_error()
            return

        if push_nav:
            self.nav_stack.navigate_to(path)

        self.file_index.build(self.objects)

        if self.config:
            self.config.set('last_opened_folder', path)
            self.config.save()

        if self.player:
            self.player.start_navigation_animation(
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
            newly_selected = self.selector.handle_selection(self.objects)

            # Track how long the crosshair has rested on the same object.
            # After 500 ms of stable hover, flag the tooltip for display.
            if newly_selected is not self._hover_object:
                self._hover_object      = newly_selected
                self._hover_start       = time.time()
                self.show_hover_tooltip = False
                # Reset preview when crosshair leaves a folder
                self.hover_preview_children = None
                self._hover_preview_path    = None
                self.hover_preview_name     = None
            elif newly_selected is not None and not self.show_hover_tooltip:
                if time.time() - self._hover_start >= 0.5:
                    self.show_hover_tooltip = True

            # Lazily scan a hovered directory's children once the crosshair
            # has rested on it for 500 ms (same gate as show_hover_tooltip).
            if (self.show_hover_tooltip
                    and newly_selected is not None
                    and newly_selected.is_dir
                    and self.hover_preview_children is None
                    and newly_selected.file_path != self._hover_preview_path):
                try:
                    raw = [e for e in os.scandir(newly_selected.file_path)
                            if not e.name.startswith(".")]
                    dirs  = sorted([e for e in raw if     e.is_dir(follow_symlinks=False)],
                                    key=lambda e: e.name.lower())
                    files = sorted([e for e in raw if not e.is_dir(follow_symlinks=False)],
                                    key=lambda e: e.name.lower())
                    self.hover_preview_children = dirs + files
                except PermissionError:
                    self.hover_preview_children = []
                self._hover_preview_path = newly_selected.file_path

            # Raycast against mini preview cubes to find which one the
            # crosshair is aimed at, and expose its name for the tooltip.
            if (newly_selected is not None
                    and newly_selected.is_dir
                    and self.hover_preview_children):
                self.hover_preview_name = _pick_preview_cube(
                    newly_selected,
                    self.hover_preview_children,
                )
            else:
                self.hover_preview_name = None

            self.selected_object = newly_selected
        else:
            self.show_hover_tooltip = False
            self.hover_preview_name = None

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

            elif event.type == KEYDOWN and not self.cursor_visible:
                alt = pygame.key.get_mods() & KMOD_ALT
                if event.key == K_BACKSPACE or (event.key == K_LEFT and alt):
                    path = self.nav_stack.go_back()
                    if path:
                        self.load_directory(path, push_nav=False)
                elif event.key == K_RIGHT and alt:
                    path = self.nav_stack.go_forward()
                    if path:
                        self.load_directory(path, push_nav=False)

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
                    pygame.event.set_grab(True)

            elif event.type == MOUSEBUTTONUP and event.button == 1:
                self.selector.stop_drag()
