"""
FileExplorer3D - world.py
Contains the World class, which manages drawable objects in the 3D environment.
"""

import os
import time
import threading
import pygame
from pygame.locals import *
from OpenGL.GL import *

from explorer.selector import Selector
from explorer.file_tree_node import make_root
from explorer.file_index import FileIndex
from explorer.symlink_graph import SymlinkGraph
import numpy as np
from utils.directory_scanner import DirectoryScanner
from utils.interaction_handler import InteractionHandler
from utils.doubly_linked_list import DoublyLinkedList
from utils.metadata_cache import MetadataCache
from utils.navigation_stack import NavigationStack
from utils.renderer import Renderer


def _pick_preview_cube(folder_obj, children):
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
    HIT_R   = CUBE_SIZE * 1.6

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
    BOOKMARK_PANEL_WIDTH = 460
    BOOKMARK_PANEL_MARGIN = 12
    BOOKMARK_PANEL_TOP = 12
    BOOKMARK_PANEL_BOTTOM = 12
    BOOKMARK_PANEL_MAX_HEIGHT = 560
    BOOKMARK_ROW_HEIGHT = 54
    BOOKMARK_ROW_GAP = 8
    BOOKMARK_ICON_SIZE = 22
    BOOKMARK_HEADER_HEIGHT = 42
    BOOKMARK_FOOTER_HEIGHT = 38
    BOOKMARK_ACCESS_CACHE_TTL = 2.0
    SYMLINK_SECTION_GAP = 10
    SYMLINK_HEADER_HEIGHT = 34
    SYMLINK_ROW_HEIGHT = 54
    SYMLINK_ROW_GAP = 8
    SYMLINK_MAX_ROWS = 4
    SYMLINK_RECORD_CACHE_TTL = 2.0

    def __init__(self):
        self.objects = []
        self.object_by_path = {}
        self.selected_object = None
        self.selector = Selector()
        self.cursor_visible = False
        self.current_directory = None

        self.player = None
        self.config = None

        self._last_click_time = 0
        self._last_clicked_object = None

        self.file_index = FileIndex()
        self.bookmarks = DoublyLinkedList()
        self.bookmarks_panel_visible = True
        self.bookmarks_page_index = 0
        self._bookmark_access_cache = {}

        self.nav_stack = NavigationStack()
        self.metadata_cache = MetadataCache()
        self.symlink_graph = SymlinkGraph()

        self._hover_object = None
        self._hover_start  = 0.0
        self.show_hover_tooltip = False

        self.hover_preview_children: list | None = None
        self._hover_preview_path: str | None = None
        self.hover_preview_name: str | None = None

        # Cache for symlink records shown in the panel — refreshed by TTL, not per frame.
        self._symlink_record_cache: list | None = None
        self._symlink_record_cache_time: float = 0.0
        self._symlink_record_cache_dir: str | None = None
        self._symlink_refresh_thread: threading.Thread | None = None
        self._symlink_refresh_lock = threading.Lock()

    # ── object management ────────────────────────────────────────────────────

    def add_object(self, obj):
        self.objects.append(obj)
        self.object_by_path[obj.file_path] = obj

    def clear(self):
        self.objects = []
        self.object_by_path = {}
        self.selected_object = None
        self.file_index.clear()
        self.selector.stop_drag()
        self._last_click_time = 0
        self._last_clicked_object = None
        self._symlink_record_cache = None
        self._symlink_refresh_thread = None

    def get_object_by_path(self, file_path):
        return self.object_by_path.get(file_path)

    # ── bookmarks ────────────────────────────────────────────────────────────

    def load_bookmarks_from_config(self):
        if not self.config:
            return
        records = self.config.get('bookmarks', [])
        if not isinstance(records, list):
            records = []
        self.bookmarks = DoublyLinkedList.from_records(records)
        self.bookmarks_page_index = 0

    def get_bookmark_entries(self):
        return self.bookmarks.to_records()

    def get_bookmark_page_size(self, win_h):
        available_height = min(
            self.BOOKMARK_PANEL_MAX_HEIGHT,
            max(180, win_h - self.BOOKMARK_PANEL_TOP - self.BOOKMARK_PANEL_BOTTOM),
        )
        usable_height = max(0, available_height - self.BOOKMARK_HEADER_HEIGHT - self.BOOKMARK_FOOTER_HEIGHT)
        row_stride = self.BOOKMARK_ROW_HEIGHT + self.BOOKMARK_ROW_GAP
        return max(1, usable_height // row_stride)

    def get_bookmark_page_count(self, win_h):
        page_size = self.get_bookmark_page_size(win_h)
        total = len(self.bookmarks)
        return max(1, (total + page_size - 1) // page_size)

    def get_bookmark_page_entries(self, win_h):
        entries = self.get_bookmark_entries()
        page_size = self.get_bookmark_page_size(win_h)
        page_count = max(1, (len(entries) + page_size - 1) // page_size)
        self.bookmarks_page_index = max(0, min(self.bookmarks_page_index, page_count - 1))
        start = self.bookmarks_page_index * page_size
        end = start + page_size
        return entries[start:end], page_size, page_count

    def next_bookmark_page(self, win_h):
        page_count = self.get_bookmark_page_count(win_h)
        if self.bookmarks_page_index < page_count - 1:
            self.bookmarks_page_index += 1

    def previous_bookmark_page(self):
        if self.bookmarks_page_index > 0:
            self.bookmarks_page_index -= 1

    def _clamp_bookmark_page(self, win_h):
        page_count = self.get_bookmark_page_count(win_h)
        self.bookmarks_page_index = max(0, min(self.bookmarks_page_index, page_count - 1))

    def sync_bookmarks_to_config(self):
        if not self.config:
            return
        self.config.set('bookmarks', self.bookmarks.to_records())
        self.config.save()

    def is_bookmarked(self, path):
        return self.bookmarks.contains(path)

    def _entry_name_from_path(self, path):
        name = os.path.basename(os.path.normpath(path))
        return name or path

    def _bookmark_payload(self, target_object=None):
        if target_object is not None:
            return target_object.file_name, target_object.file_path, target_object.is_dir
        if self.current_directory:
            return (
                self._entry_name_from_path(self.current_directory),
                self.current_directory,
                True,
            )
        return None

    def toggle_bookmark(self, target_object=None):
        payload = self._bookmark_payload(target_object)
        if payload is None:
            return None

        name, full_path, is_dir = payload
        if self.bookmarks.contains(full_path):
            self.bookmarks.remove(full_path)
            self.sync_bookmarks_to_config()
            return False

        self.bookmarks.add_to_front(name, full_path, is_dir)
        self.sync_bookmarks_to_config()
        self.bookmarks_page_index = 0
        return True

    def remove_bookmark(self, full_path):
        removed = self.bookmarks.remove(full_path)
        if removed:
            self.sync_bookmarks_to_config()
        return removed

    def toggle_bookmarks_panel(self):
        self.cursor_visible = not self.cursor_visible
        self.bookmarks_panel_visible = self.cursor_visible
        pygame.mouse.set_visible(self.cursor_visible)
        pygame.event.set_grab(not self.cursor_visible)
        if self.cursor_visible:
            surface = pygame.display.get_surface()
            if surface:
                pygame.mouse.set_pos(surface.get_width() // 2, surface.get_height() // 2)

    # ── navigation ───────────────────────────────────────────────────────────

    def _follow_link_target(self, obj):
        target_path = getattr(obj, "link_target_path", None)
        if not target_path or getattr(obj, "link_broken", False):
            obj.flash_error()
            return False

        if os.path.isdir(target_path):
            self.load_directory(target_path)
            return True

        if os.path.exists(target_path):
            parent = os.path.dirname(target_path)
            if not parent:
                obj.flash_error()
                return False
            self.load_directory(parent)
            self.selected_object = self.get_object_by_path(target_path)
            return True

        obj.flash_error()
        return False

    def open_bookmark(self, full_path, is_dir):
        if is_dir:
            self.load_directory(full_path)
            return

        parent = os.path.dirname(full_path)
        if parent:
            self.load_directory(parent)
            self.selected_object = self.get_object_by_path(full_path)

    def open_symlink_record(self, record):
        source_path = record.get("source_path")
        source_obj = self.get_object_by_path(source_path)
        if source_obj is not None:
            return self._follow_link_target(source_obj)

        target_path = record.get("target_path")
        if not target_path or target_path == "(unresolved)":
            return False

        if os.path.isdir(target_path):
            self.load_directory(target_path)
            return True

        if os.path.exists(target_path):
            parent = os.path.dirname(target_path)
            if parent:
                self.load_directory(parent)
                self.selected_object = self.get_object_by_path(target_path)
                return True

        return False

    def load_directory(self, path, push_nav=True, new_root=False):
        node = make_root(path)
        success = DirectoryScanner.fill_world_from_node(self, node)
        if not success:
            if self._last_clicked_object:
                self._last_clicked_object.flash_error()
            return

        if new_root:
            self.nav_stack = NavigationStack()

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

    # ── bookmark access cache ────────────────────────────────────────────────

    def _get_bookmark_access_flags(self, full_path, is_dir):
        now = time.time()
        cached = self._bookmark_access_cache.get(full_path)
        if cached and (now - cached['timestamp']) <= self.BOOKMARK_ACCESS_CACHE_TTL:
            return cached['flags']

        exists = os.path.exists(full_path)
        is_protected = False

        if exists:
            try:
                if is_dir:
                    with os.scandir(full_path) as entries:
                        next(entries, None)
                else:
                    with open(full_path, 'rb'):
                        pass
            except PermissionError:
                is_protected = True
            except OSError:
                is_protected = True

        flags = {'exists': exists, 'is_protected': is_protected}
        self._bookmark_access_cache[full_path] = {'timestamp': now, 'flags': flags}

        expired = [k for k, v in self._bookmark_access_cache.items()
                   if (now - v['timestamp']) > self.BOOKMARK_ACCESS_CACHE_TTL]
        for k in expired:
            del self._bookmark_access_cache[k]

        return flags

    # ── symlink record cache ─────────────────────────────────────────────────

    def _get_visible_symlink_records(self):
        """Return cached symlink records, triggering a background refresh when stale."""
        now = time.time()
        cache_stale = (
            self._symlink_record_cache is None
            or self._symlink_record_cache_dir != self.current_directory
            or (now - self._symlink_record_cache_time) > self.SYMLINK_RECORD_CACHE_TTL
        )

        if cache_stale:
            # Serve stale cache immediately; kick off a refresh in the background
            # only if one isn't already running.
            refresh_needed = (
                self._symlink_refresh_thread is None
                or not self._symlink_refresh_thread.is_alive()
            )
            if refresh_needed:
                snapshot = [
                    (obj.file_name, obj.file_path, obj.link_target_path, obj.link_broken)
                    for obj in self.objects
                    if getattr(obj, "is_link", False)
                ]
                thread = threading.Thread(
                    target=self._refresh_symlink_cache,
                    args=(snapshot, self.current_directory),
                    daemon=True,
                )
                self._symlink_refresh_thread = thread
                thread.start()

        with self._symlink_refresh_lock:
            return list(self._symlink_record_cache) if self._symlink_record_cache is not None else []

    def _refresh_symlink_cache(self, snapshot, directory):
        """Run on a background thread: stat each symlink target and update the cache."""
        records = []
        for name, path, target_path, link_broken in snapshot:
            exists = bool(target_path and not link_broken and os.path.exists(target_path))
            is_dir = bool(target_path and exists and os.path.isdir(target_path))
            is_protected = False
            if exists:
                try:
                    if is_dir:
                        with os.scandir(target_path) as entries:
                            next(entries, None)
                    else:
                        with open(target_path, "rb"):
                            pass
                except (PermissionError, OSError):
                    is_protected = True

            records.append({
                "kind": "symlink",
                "name": name,
                "path": path,
                "source_path": path,
                "target_path": target_path or "(unresolved)",
                "is_dir": is_dir,
                "exists": exists,
                "is_protected": is_protected,
                "link_broken": link_broken,
            })

        records.sort(key=lambda item: item["name"].lower())

        with self._symlink_refresh_lock:
            self._symlink_record_cache = records
            self._symlink_record_cache_time = time.time()
            self._symlink_record_cache_dir = directory

    # ── panel layout ─────────────────────────────────────────────────────────

    def get_bookmark_panel_layout(self, win_w, win_h):
        if not self.bookmarks_panel_visible:
            return None

        page_records, page_size, page_count = self.get_bookmark_page_entries(win_h)
        display_records = []
        for record in page_records:
            flags = self._get_bookmark_access_flags(record['path'], record['is_dir'])
            display_records.append({**record, **flags, 'kind': 'bookmark'})

        symlink_records_all = self._get_visible_symlink_records()
        symlink_records = symlink_records_all[:self.SYMLINK_MAX_ROWS]

        panel_width = min(self.BOOKMARK_PANEL_WIDTH, max(300, win_w - 2 * self.BOOKMARK_PANEL_MARGIN))
        max_height = min(
            self.BOOKMARK_PANEL_MAX_HEIGHT,
            max(180, win_h - self.BOOKMARK_PANEL_TOP - self.BOOKMARK_PANEL_BOTTOM),
        )
        row_count = max(1, len(display_records))
        rows_height = row_count * self.BOOKMARK_ROW_HEIGHT + max(0, row_count - 1) * self.BOOKMARK_ROW_GAP

        symlink_row_count = len(symlink_records)
        symlink_rows_height = (
            symlink_row_count * self.SYMLINK_ROW_HEIGHT
            + max(0, symlink_row_count - 1) * self.SYMLINK_ROW_GAP
        )
        symlink_body_height = symlink_rows_height if symlink_row_count > 0 else 24

        panel_content_height = (
            self.BOOKMARK_HEADER_HEIGHT
            + rows_height
            + self.BOOKMARK_FOOTER_HEIGHT
            + self.SYMLINK_SECTION_GAP
            + self.SYMLINK_HEADER_HEIGHT
            + symlink_body_height
            + 20
        )
        panel_height = min(max_height, panel_content_height)
        x = win_w - panel_width - self.BOOKMARK_PANEL_MARGIN
        y = self.BOOKMARK_PANEL_TOP

        rows = []
        row_start_y = y + self.BOOKMARK_HEADER_HEIGHT
        for index, record in enumerate(display_records):
            row_top = row_start_y + index * (self.BOOKMARK_ROW_HEIGHT + self.BOOKMARK_ROW_GAP)
            row_rect = pygame.Rect(x + 10, row_top, panel_width - 20, self.BOOKMARK_ROW_HEIGHT)
            rows.append({'record': record, 'rect': row_rect, 'index': index})

        footer_y = y + self.BOOKMARK_HEADER_HEIGHT + rows_height + 4
        prev_rect = pygame.Rect(x + 12, footer_y, 72, 26)
        next_rect = pygame.Rect(x + panel_width - 84, footer_y, 72, 26)
        page_text_rect = pygame.Rect(x + 92, footer_y, panel_width - 184, 26)

        symlink_header_top = footer_y + self.BOOKMARK_FOOTER_HEIGHT + self.SYMLINK_SECTION_GAP
        symlink_header_rect = pygame.Rect(x, symlink_header_top, panel_width, self.SYMLINK_HEADER_HEIGHT)

        symlink_rows = []
        symlink_row_start_y = symlink_header_rect.bottom
        for index, record in enumerate(symlink_records):
            row_top = symlink_row_start_y + index * (self.SYMLINK_ROW_HEIGHT + self.SYMLINK_ROW_GAP)
            row_rect = pygame.Rect(x + 10, row_top, panel_width - 20, self.SYMLINK_ROW_HEIGHT)
            symlink_rows.append({'record': record, 'rect': row_rect, 'index': index})

        symlink_empty_rect = pygame.Rect(x + 16, symlink_row_start_y + 8, panel_width - 32, 24)

        return {
            'panel_rect': pygame.Rect(x, y, panel_width, panel_height),
            'header_rect': pygame.Rect(x, y, panel_width, self.BOOKMARK_HEADER_HEIGHT),
            'rows': rows,
            'page_records': display_records,
            'page_count': page_count,
            'page_index': self.bookmarks_page_index,
            'page_size': page_size,
            'has_prev': self.bookmarks_page_index > 0,
            'has_next': self.bookmarks_page_index < page_count - 1,
            'prev_rect': prev_rect,
            'next_rect': next_rect,
            'page_text_rect': page_text_rect,
            'overflow_count': max(0, len(self.bookmarks) - len(display_records)),
            'symlink_header_rect': symlink_header_rect,
            'symlink_rows': symlink_rows,
            'symlink_records': symlink_records,
            'symlink_empty_rect': symlink_empty_rect,
            'symlink_overflow_count': max(0, len(symlink_records_all) - len(symlink_records)),
        }

    def _bookmark_record_at_pos(self, pos, win_w, win_h):
        layout = self.get_bookmark_panel_layout(win_w, win_h)
        if not layout:
            return None

        if layout['has_prev'] and layout['prev_rect'].collidepoint(pos):
            return {'action': 'prev'}
        if layout['has_next'] and layout['next_rect'].collidepoint(pos):
            return {'action': 'next'}

        for row in layout['rows']:
            if row['rect'].collidepoint(pos):
                return row['record']

        for row in layout.get('symlink_rows', []):
            if row['rect'].collidepoint(pos):
                return row['record']
        return None

    def _bookmark_record_under_mouse(self):
        surface = pygame.display.get_surface()
        if surface is None:
            return None
        return self._bookmark_record_at_pos(pygame.mouse.get_pos(), *surface.get_size())

    # ── per-frame update ─────────────────────────────────────────────────────

    def update(self):
        if not self.cursor_visible:
            newly_selected = self.selector.handle_selection(self.objects)

            if newly_selected is not self._hover_object:
                self._hover_object      = newly_selected
                self._hover_start       = time.time()
                self.show_hover_tooltip = False
                self.hover_preview_children = None
                self._hover_preview_path    = None
                self.hover_preview_name     = None
            elif newly_selected is not None and not self.show_hover_tooltip:
                if time.time() - self._hover_start >= 0.5:
                    self.show_hover_tooltip = True

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

    # ── event handling ───────────────────────────────────────────────────────

    def _print_tree(self, node, prefix=""):
        children = node.get_children()
        for i, child in enumerate(children):
            connector = "└── " if i == len(children) - 1 else "├── "
            print(f"{prefix}{connector}{child.name}")
            if child.is_dir:
                extension = "    " if i == len(children) - 1 else "│   "
                self._print_tree(child, prefix + extension)

    def handle_events(self, events):
        surface = pygame.display.get_surface()
        win_size = surface.get_size() if surface else (0, 0)
        for event in events:
            if event.type == KEYDOWN and event.key == K_ESCAPE:
                self.cursor_visible = not self.cursor_visible
                self.bookmarks_panel_visible = self.cursor_visible
                pygame.mouse.set_visible(True)
                pygame.event.set_grab(not self.cursor_visible)
                if surface:
                    pygame.mouse.set_pos(surface.get_width() // 2, surface.get_height() // 2)
                if self.cursor_visible:
                    self.deselect_object()
                    self.selector.stop_drag()
                else:
                    pygame.mouse.set_visible(False)

            elif event.type == KEYDOWN and InteractionHandler.CtrlPressed() and event.key == K_d:
                self.toggle_bookmark(self.selected_object)

            elif event.type == KEYDOWN and InteractionHandler.CtrlPressed() and event.key == K_b:
                self.toggle_bookmarks_panel()

            elif event.type == KEYDOWN and event.key == K_DELETE and self.bookmarks_panel_visible:
                record = self._bookmark_record_under_mouse()
                if record is None and self.selected_object and self.is_bookmarked(self.selected_object.file_path):
                    record = {
                        'kind': 'bookmark',
                        'name': self.selected_object.file_name,
                        'path': self.selected_object.file_path,
                        'is_dir': self.selected_object.is_dir,
                    }
                if record is not None:
                    if record.get('action') == 'prev':
                        self.previous_bookmark_page()
                    elif record.get('action') == 'next':
                        self.next_bookmark_page(win_size[1])
                    elif record.get('kind') == 'bookmark':
                        self.remove_bookmark(record['path'])

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

            elif event.type == MOUSEBUTTONDOWN and event.button in (1, 3):
                if event.button == 1 and self.cursor_visible:
                    if Renderer._nav_back_rect and Renderer._nav_back_rect.collidepoint(event.pos):
                        path = self.nav_stack.go_back()
                        if path:
                            self.load_directory(path, push_nav=False)
                        continue
                    if Renderer._nav_forward_rect and Renderer._nav_forward_rect.collidepoint(event.pos):
                        path = self.nav_stack.go_forward()
                        if path:
                            self.load_directory(path, push_nav=False)
                        continue

                if self.bookmarks_panel_visible:
                    record = self._bookmark_record_at_pos(event.pos, *win_size)
                    if record is None:
                        continue

                    if isinstance(record, dict) and record.get('action') == 'prev':
                        self.previous_bookmark_page()
                        continue

                    if isinstance(record, dict) and record.get('action') == 'next':
                        self.next_bookmark_page(win_size[1])
                        continue

                    if record.get('kind') == 'symlink':
                        if event.button == 1:
                            self.open_symlink_record(record)
                        continue

                    if event.button == 3:
                        self.remove_bookmark(record['path'])
                    else:
                        self.open_bookmark(record['path'], record['is_dir'])
                    continue

                if self.cursor_visible and event.button == 1:
                    self.cursor_visible = False
                    self.bookmarks_panel_visible = False
                    pygame.mouse.set_visible(False)
                    pygame.event.set_grab(True)
                else:
                    now = time.time() * 1000

                    if (self._last_clicked_object is not None
                            and now - self._last_click_time < self.DOUBLE_CLICK_MS):
                        target = Selector.pick_object(self.objects)
                        if target is self._last_clicked_object:
                            if getattr(target, "is_link", False):
                                self._follow_link_target(target)
                            elif hasattr(target, 'is_dir') and target.is_dir:
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
