"""
FileExplorer3D - renderer.py
Contains the Renderer class, which handles the rendering of objects.
"""

import numpy as np
import pygame
from pygame.locals import *
from utils.interaction_handler import InteractionHandler
from utils.metadata_cache import format_size
from OpenGL.GL import *
from OpenGL.GLU import *


class Renderer:

    _font = None
    _small_font = None

    _label_texture_id = None
    _label_text = None

    # Pygame-coordinate rects for the nav arrow hit areas (updated each frame)
    _nav_back_rect = None
    _nav_forward_rect = None
    _label_size = (0, 0)

    _info_panel_texture_id = None
    _info_panel_text = None
    _info_panel_size = (0, 0)

    _bookmark_panel_texture_id = None
    _bookmark_panel_cache_key = None
    _bookmark_panel_size = (0, 0)

    _hover_tooltip_texture_id = None
    _hover_tooltip_text = None
    _hover_tooltip_size = (0, 0)

    # ── directory preview palette (mirrors file_object.py) ─────────────────
    _EXT_COLORS = {
        ".py":   (0.2, 0.9, 0.3),  ".js":   (0.9, 0.85, 0.2),
        ".ts":   (0.2, 0.5, 0.9),  ".html": (0.9, 0.4, 0.1),
        ".css":  (0.3, 0.6, 1.0),  ".cpp":  (0.6, 0.3, 0.9),
        ".c":    (0.5, 0.3, 0.8),  ".h":    (0.7, 0.4, 0.9),
        ".txt":  (0.9, 0.9, 0.9),  ".md":   (0.8, 0.8, 0.7),
        ".pdf":  (0.9, 0.1, 0.1),  ".json": (0.9, 0.7, 0.2),
        ".yaml": (0.9, 0.7, 0.2),  ".yml":  (0.9, 0.7, 0.2),
        ".xml":  (0.7, 0.5, 0.2),  ".png":  (0.9, 0.8, 0.2),
        ".jpg":  (0.9, 0.75, 0.2), ".jpeg": (0.9, 0.75, 0.2),
        ".gif":  (0.9, 0.6, 0.7),  ".svg":  (0.4, 0.9, 0.8),
        ".zip":  (0.6, 0.4, 0.2),  ".tar":  (0.6, 0.4, 0.2),
        ".gz":   (0.5, 0.35, 0.15),
    }
    _FOLDER_COLOR  = (0.15, 0.3, 0.8)
    _DEFAULT_COLOR = (0.65, 0.65, 0.65)

    @staticmethod
    def _get_font():
        if Renderer._font is None:
            pygame.font.init()
            Renderer._font = pygame.font.SysFont("Arial", 22, bold=True)
        return Renderer._font

    @staticmethod
    def _get_small_font():
        if Renderer._small_font is None:
            pygame.font.init()
            Renderer._small_font = pygame.font.SysFont("Arial", 14)
        return Renderer._small_font

    @staticmethod
    def handle_events(events):
        for event in events:
            if event.type == VIDEORESIZE:
                InteractionHandler.ResizeWindow(*event.size)
                glViewport(0, 0, event.size[0], event.size[1])
                viewport = glGetIntegerv(GL_VIEWPORT)
                return int(viewport[2]), int(viewport[3])
        return None

    @staticmethod
    def SetupFrame(win_w, win_h, config):
        glViewport(0, 0, win_w, win_h)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glEnable(GL_DEPTH_TEST)

        glEnable(GL_LIGHTING); glEnable(GL_COLOR_MATERIAL)
        glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)
        
        # Set ambient light to maximum for uniform illumination everywhere
        glLightModelfv(GL_LIGHT_MODEL_AMBIENT, [1.0, 1.0, 1.0, 1.0])

        glMatrixMode(GL_PROJECTION); glLoadIdentity()
        aspect = win_w / win_h if win_h > 0 else 1
        gluPerspective(config.get("fov", 70), aspect, 0.1, 1000.0)

        glMatrixMode(GL_MODELVIEW); glLoadIdentity()

    @staticmethod
    def DrawGrid(size=20, step=1):
        glDisable(GL_LIGHTING)
        glColor3f(0.3, 0.3, 0.3)
        glBegin(GL_LINES)
        for i in range(-size, size + 1, step):
            glVertex3f(-size, 0, i); glVertex3f(size, 0, i)
            glVertex3f(i, 0, -size); glVertex3f(i, 0, size)
        glEnd()
        glEnable(GL_LIGHTING)

    @staticmethod
    def DrawObject(obj, selected_object, bookmarked=False):
        glPushMatrix()
        glTranslatef(obj.x, obj.y, obj.z)
        glMaterialfv(GL_FRONT, GL_EMISSION, [0.0, 0.0, 0.0, 1.0])
        obj.draw(selected=(obj is selected_object), bookmarked=bookmarked)

        # Draw a compact warning glyph above nodes participating in link cycles.
        if getattr(obj, "in_cycle", False):
            top_y = obj.height / 2.0 + 0.18
            glDisable(GL_LIGHTING)
            glColor3f(1.0, 0.55, 0.1)
            glLineWidth(2.0)
            glBegin(GL_LINES)
            glVertex3f(0.0, top_y + 0.14, 0.0)
            glVertex3f(0.0, top_y - 0.08, 0.0)
            glEnd()
            glPointSize(4.0)
            glBegin(GL_POINTS)
            glVertex3f(0.0, top_y - 0.13, 0.0)
            glEnd()
            glLineWidth(1.0)
            glEnable(GL_LIGHTING)

        glPopMatrix()

    @staticmethod
    def DrawAxes():
        glDisable(GL_DEPTH_TEST)
        glDisable(GL_LIGHTING)
        glLineWidth(2.0)
        glBegin(GL_LINES)
        glColor3f(1, 0, 0); glVertex3f(0,0,0); glVertex3f(5,0,0)
        glColor3f(0, 1, 0); glVertex3f(0,0,0); glVertex3f(0,5,0)
        glColor3f(0, 0, 1); glVertex3f(0,0,0); glVertex3f(0,0,5)
        glEnd()
        glLineWidth(1.0)
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_LIGHTING)

    @staticmethod
    def HighlightSelectedObject(selected_object, selector):
        glDisable(GL_DEPTH_TEST)
        selector.draw(np.array([selected_object.x, selected_object.y, selected_object.z]))
        glColor3f(1.0, 1.0, 1.0)
        glEnable(GL_DEPTH_TEST)
        glDisable(GL_LIGHTING); glDisable(GL_DEPTH_TEST)

    @staticmethod
    def DrawCrosshair(win_w, win_h):
        """Draw a small crosshair at the centre of the screen."""
        cx, cy   = win_w // 2, win_h // 2
        arm      = 10
        gap      = 3

        glMatrixMode(GL_PROJECTION); glPushMatrix(); glLoadIdentity()
        glOrtho(0, win_w, 0, win_h, -1, 1)
        glMatrixMode(GL_MODELVIEW); glPushMatrix(); glLoadIdentity()

        glDisable(GL_DEPTH_TEST)
        glDisable(GL_LIGHTING)
        glLineWidth(1.5)

        glColor4f(0.0, 0.0, 0.0, 0.6)
        glBegin(GL_LINES)
        glVertex2f(cx - arm - 1, cy);       glVertex2f(cx - gap - 1, cy)
        glVertex2f(cx + gap + 1, cy);       glVertex2f(cx + arm + 1, cy)
        glVertex2f(cx, cy - arm - 1);       glVertex2f(cx, cy - gap - 1)
        glVertex2f(cx, cy + gap + 1);       glVertex2f(cx, cy + arm + 1)
        glEnd()

        glColor4f(1.0, 1.0, 1.0, 1.0)
        glBegin(GL_LINES)
        glVertex2f(cx - arm, cy);           glVertex2f(cx - gap, cy)
        glVertex2f(cx + gap, cy);           glVertex2f(cx + arm, cy)
        glVertex2f(cx, cy - arm);           glVertex2f(cx, cy - gap)
        glVertex2f(cx, cy + gap);           glVertex2f(cx, cy + arm)
        glEnd()

        glLineWidth(1.0)
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_LIGHTING)

        glMatrixMode(GL_PROJECTION); glPopMatrix()
        glMatrixMode(GL_MODELVIEW);  glPopMatrix()

    @staticmethod
    def DrawNavArrows(nav_stack, win_w, win_h):
        """Render back (◄) and forward (►) arrows in the top-left HUD.

        Active arrows are drawn white; unavailable ones are drawn dark grey.
        Uses the same font/texture pipeline as DrawSelectedLabel.
        """
        back_color    = (255, 255, 255) if nav_stack.can_go_back()    else (60, 60, 60)
        forward_color = (255, 255, 255) if nav_stack.can_go_forward()  else (60, 60, 60)

        font = Renderer._get_font()
        pad  = 8
        margin = 12
        gap    = 6   # horizontal gap between the two arrows

        back_surf    = font.render("◄", True, back_color)
        forward_surf = font.render("►", True, forward_color)

        bw, bh = back_surf.get_size()
        fw, fh = forward_surf.get_size()
        h      = max(bh, fh)

        # composite onto one surface: [pad] ◄ [gap] ► [pad]
        total_w = pad + bw + gap + fw + pad
        total_h = h + pad * 2

        bg = pygame.Surface((total_w, total_h), pygame.SRCALPHA)
        bg.fill((0, 0, 0, 140))
        bg.blit(back_surf,    (pad,              pad + (h - bh) // 2))
        bg.blit(forward_surf, (pad + bw + gap,   pad + (h - fh) // 2))
        bg = pygame.transform.flip(bg, False, True)
        raw = pygame.image.tostring(bg, "RGBA", False)

        tex_id = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, tex_id)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA,
                     total_w, total_h, 0, GL_RGBA, GL_UNSIGNED_BYTE, raw)

        # position: top-left corner (OpenGL y=0 is bottom, so flip)
        x0 = margin
        y0 = win_h - margin - total_h
        x1, y1 = x0 + total_w, y0 + total_h

        # Store pygame-coordinate hit rects for click detection (y=0 at top)
        split_x = x0 + pad + bw + gap // 2
        Renderer._nav_back_rect    = pygame.Rect(x0, margin, split_x - x0, total_h)
        Renderer._nav_forward_rect = pygame.Rect(split_x, margin, x1 - split_x, total_h)

        glMatrixMode(GL_PROJECTION); glPushMatrix(); glLoadIdentity()
        glOrtho(0, win_w, 0, win_h, -1, 1)
        glMatrixMode(GL_MODELVIEW); glPushMatrix(); glLoadIdentity()

        glDisable(GL_DEPTH_TEST)
        glDisable(GL_LIGHTING)
        glEnable(GL_TEXTURE_2D)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

        glBindTexture(GL_TEXTURE_2D, tex_id)
        glColor4f(1, 1, 1, 1)
        glBegin(GL_QUADS)
        glTexCoord2f(0, 0); glVertex2f(x0, y0)
        glTexCoord2f(1, 0); glVertex2f(x1, y0)
        glTexCoord2f(1, 1); glVertex2f(x1, y1)
        glTexCoord2f(0, 1); glVertex2f(x0, y1)
        glEnd()

        glBindTexture(GL_TEXTURE_2D, 0)
        glDeleteTextures([tex_id])   # free GPU texture each frame (small, changes often)
        glDisable(GL_TEXTURE_2D)
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_LIGHTING)

        glMatrixMode(GL_PROJECTION); glPopMatrix()
        glMatrixMode(GL_MODELVIEW);  glPopMatrix()

    @staticmethod
    def DrawSelectedLabel(selected_object, win_w, win_h):
        """Render the selected object's file name as a 2D HUD label."""
        if selected_object is None:
            return

        label_text = selected_object.file_name

        if label_text != Renderer._label_text:
            Renderer._label_text = label_text
            Renderer._label_texture_id = Renderer._upload_label_texture(label_text)

        if Renderer._label_texture_id is None:
            return

        Renderer._draw_label_quad(Renderer._label_texture_id, win_w, win_h)

    @staticmethod
    def DrawBookmarksPanel(world, win_w, win_h):
        """Render a bookmarks panel and return layout data for interaction."""
        layout = world.get_bookmark_panel_layout(win_w, win_h)
        if not layout:
            return None

        records = layout['page_records']
        symlink_records = layout.get('symlink_records', [])
        panel_rect = layout['panel_rect']

        panel_surface = pygame.Surface((panel_rect.width, panel_rect.height), pygame.SRCALPHA)
        panel_surface.fill((10, 14, 24, 210))

        title_font = Renderer._get_font()
        body_font = Renderer._get_small_font()

        pygame.draw.rect(panel_surface, (255, 255, 255, 32), panel_surface.get_rect(), 1, border_radius=12)

        title = title_font.render("Bookmarks", True, (255, 255, 255))
        panel_surface.blit(title, (16, 10))

        row_top = layout['header_rect'].height
        if not records:
            empty_text = body_font.render("No bookmarks yet", True, (190, 200, 220))
            panel_surface.blit(empty_text, (16, row_top + 12))
        for index, record in enumerate(records):
            row_y = row_top + index * (world.BOOKMARK_ROW_HEIGHT + world.BOOKMARK_ROW_GAP)
            row_rect = pygame.Rect(10, row_y, panel_rect.width - 20, world.BOOKMARK_ROW_HEIGHT)
            pygame.draw.rect(panel_surface, (255, 255, 255, 18), row_rect, border_radius=10)

            badge_color = (230, 190, 70) if record['is_dir'] else (90, 180, 230)
            badge_rect = pygame.Rect(row_rect.x + 10, row_rect.y + 12, world.BOOKMARK_ICON_SIZE + 6, world.BOOKMARK_ICON_SIZE + 6)
            pygame.draw.rect(panel_surface, badge_color, badge_rect, border_radius=6)
            badge_label = body_font.render("D" if record['is_dir'] else "F", True, (20, 24, 32))
            panel_surface.blit(
                badge_label,
                (
                    badge_rect.x + (badge_rect.width - badge_label.get_width()) // 2,
                    badge_rect.y + (badge_rect.height - badge_label.get_height()) // 2,
                ),
            )

            status_text = None
            status_color = (190, 200, 220)
            if not record.get('exists', True):
                status_text = '[MISSING]'
                status_color = (230, 140, 140)
            elif record.get('is_protected', False):
                status_text = '[PROTECTED]'
                status_color = (240, 190, 110)

            status_width = 0
            if status_text:
                status_surf = body_font.render(status_text, True, status_color)
                status_width = status_surf.get_width() + 12
                panel_surface.blit(
                    status_surf,
                    (row_rect.right - status_surf.get_width() - 10, row_rect.y + 8),
                )

            name_x = badge_rect.right + 10
            name_max_width = panel_rect.width - name_x - 14 - status_width
            name_text = Renderer._fit_text(record['name'], title_font, name_max_width)
            name_surf = title_font.render(name_text, True, (255, 255, 255))
            panel_surface.blit(name_surf, (name_x, row_rect.y + 6))

            path_text = Renderer._fit_text(record['path'], body_font, name_max_width)
            path_surf = body_font.render(path_text, True, (190, 200, 220))
            panel_surface.blit(path_surf, (name_x, row_rect.y + 28))

        footer_y = panel_rect.height - world.BOOKMARK_FOOTER_HEIGHT + 6
        if layout['page_count'] > 1:
            prev_color = (255, 255, 255) if layout['has_prev'] else (90, 96, 110)
            next_color = (255, 255, 255) if layout['has_next'] else (90, 96, 110)

            prev_rect = layout['prev_rect'].move(-panel_rect.x, -panel_rect.y)
            next_rect = layout['next_rect'].move(-panel_rect.x, -panel_rect.y)
            page_text_rect = layout['page_text_rect'].move(-panel_rect.x, -panel_rect.y)

            pygame.draw.rect(panel_surface, (255, 255, 255, 24), prev_rect, border_radius=8)
            pygame.draw.rect(panel_surface, (255, 255, 255, 24), next_rect, border_radius=8)
            prev_surf = body_font.render("Prev", True, prev_color)
            next_surf = body_font.render("Next", True, next_color)
            panel_surface.blit(prev_surf, (prev_rect.x + (prev_rect.width - prev_surf.get_width()) // 2, prev_rect.y + 6))
            panel_surface.blit(next_surf, (next_rect.x + (next_rect.width - next_surf.get_width()) // 2, next_rect.y + 6))

            page_text = body_font.render(f"{layout['page_index'] + 1} / {layout['page_count']}", True, (190, 200, 220))
            panel_surface.blit(page_text, (page_text_rect.x + (page_text_rect.width - page_text.get_width()) // 2, footer_y + 6))
        elif layout['overflow_count'] > 0:
            overflow_text = body_font.render(f"+ {layout['overflow_count']} more bookmarks", True, (190, 200, 220))
            panel_surface.blit(overflow_text, (16, footer_y + 6))

        symlink_header_rect = layout.get('symlink_header_rect')
        if symlink_header_rect is not None:
            symlink_header_rel = symlink_header_rect.move(-panel_rect.x, -panel_rect.y)
            symlink_title = title_font.render("Symlinks In View", True, (180, 240, 245))
            panel_surface.blit(symlink_title, (16, symlink_header_rel.y + 2))

            symlink_rows = layout.get('symlink_rows', [])
            for row in symlink_rows:
                record = row['record']
                row_rect = row['rect'].move(-panel_rect.x, -panel_rect.y)
                pygame.draw.rect(panel_surface, (255, 255, 255, 18), row_rect, border_radius=10)

                badge_rect = pygame.Rect(row_rect.x + 10, row_rect.y + 12, world.BOOKMARK_ICON_SIZE + 6, world.BOOKMARK_ICON_SIZE + 6)
                pygame.draw.rect(panel_surface, (90, 220, 230), badge_rect, border_radius=6)
                badge_label = body_font.render("L", True, (20, 24, 32))
                panel_surface.blit(
                    badge_label,
                    (
                        badge_rect.x + (badge_rect.width - badge_label.get_width()) // 2,
                        badge_rect.y + (badge_rect.height - badge_label.get_height()) // 2,
                    ),
                )

                status_text = None
                status_color = (190, 200, 220)
                if record.get('link_broken', False):
                    status_text = '[BROKEN]'
                    status_color = (230, 140, 140)
                elif record.get('is_protected', False):
                    status_text = '[PROTECTED]'
                    status_color = (240, 190, 110)

                status_width = 0
                if status_text:
                    status_surf = body_font.render(status_text, True, status_color)
                    status_width = status_surf.get_width() + 12
                    panel_surface.blit(
                        status_surf,
                        (row_rect.right - status_surf.get_width() - 10, row_rect.y + 8),
                    )

                name_x = badge_rect.right + 10
                name_max_width = panel_rect.width - name_x - 14 - status_width
                name_text = Renderer._fit_text(record.get('name', ''), title_font, name_max_width)
                name_surf = title_font.render(name_text, True, (255, 255, 255))
                panel_surface.blit(name_surf, (name_x, row_rect.y + 6))

                target_text = Renderer._fit_text(record.get('target_path', ''), body_font, name_max_width)
                target_surf = body_font.render(target_text, True, (190, 200, 220))
                panel_surface.blit(target_surf, (name_x, row_rect.y + 28))

            if not symlink_records:
                empty_rect = layout.get('symlink_empty_rect')
                if empty_rect is not None:
                    empty_rel = empty_rect.move(-panel_rect.x, -panel_rect.y)
                    empty_surf = body_font.render("No symlinks in view", True, (190, 200, 220))
                    panel_surface.blit(empty_surf, (empty_rel.x, empty_rel.y))

            symlink_overflow = layout.get('symlink_overflow_count', 0)
            if symlink_overflow > 0:
                overflow_surf = body_font.render(f"+ {symlink_overflow} more symlinks", True, (190, 200, 220))
                overflow_y = symlink_header_rel.bottom + len(symlink_rows) * (world.SYMLINK_ROW_HEIGHT + world.SYMLINK_ROW_GAP) + 4
                panel_surface.blit(overflow_surf, (16, overflow_y))

        cache_key = (
            "|".join(r['path'] for r in records),
            "|".join(r['path'] for r in symlink_records),
            panel_rect.width, panel_rect.height,
            layout['page_index'], layout['page_count'],
        )

        if cache_key != Renderer._bookmark_panel_cache_key or Renderer._bookmark_panel_texture_id is None:
            if Renderer._bookmark_panel_texture_id is not None:
                glDeleteTextures([Renderer._bookmark_panel_texture_id])

            panel_surface = pygame.transform.flip(panel_surface, False, True)
            raw = pygame.image.tostring(panel_surface, "RGBA", False)
            tex_id = glGenTextures(1)
            glBindTexture(GL_TEXTURE_2D, tex_id)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
            glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, panel_rect.width, panel_rect.height, 0, GL_RGBA, GL_UNSIGNED_BYTE, raw)

            Renderer._bookmark_panel_texture_id = tex_id
            Renderer._bookmark_panel_cache_key = cache_key
            Renderer._bookmark_panel_size = (panel_rect.width, panel_rect.height)

        draw_y = win_h - panel_rect.y - panel_rect.height
        Renderer._draw_textured_quad(Renderer._bookmark_panel_texture_id, panel_rect.x, draw_y, panel_rect.width, panel_rect.height, win_w, win_h)
        return layout

    @staticmethod
    def _upload_label_texture(text: str):
        font = Renderer._get_font()
        text_surf = font.render(text, True, (255, 255, 255))
        pad = 10
        w = text_surf.get_width()  + pad * 2
        h = text_surf.get_height() + pad * 2

        bg = pygame.Surface((w, h), pygame.SRCALPHA)
        bg.fill((0, 0, 0, 160))
        bg.blit(text_surf, (pad, pad))
        bg = pygame.transform.flip(bg, False, True)
        raw = pygame.image.tostring(bg, "RGBA", False)

        tex_id = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, tex_id)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, w, h, 0, GL_RGBA, GL_UNSIGNED_BYTE, raw)
        glBindTexture(GL_TEXTURE_2D, 0)

        Renderer._label_size = (w, h)
        return tex_id

    @staticmethod
    def _draw_label_quad(tex_id, win_w, win_h):
        lw, lh  = Renderer._label_size
        margin  = 20
        x0, y0  = margin, margin
        x1, y1  = x0 + lw, y0 + lh

        glMatrixMode(GL_PROJECTION); glPushMatrix(); glLoadIdentity()
        glOrtho(0, win_w, 0, win_h, -1, 1)
        glMatrixMode(GL_MODELVIEW);  glPushMatrix(); glLoadIdentity()

        glDisable(GL_DEPTH_TEST)
        glDisable(GL_LIGHTING)
        glEnable(GL_TEXTURE_2D)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

        glBindTexture(GL_TEXTURE_2D, tex_id)
        glColor4f(1, 1, 1, 1)
        glBegin(GL_QUADS)
        glTexCoord2f(0, 0); glVertex2f(x0, y0)
        glTexCoord2f(1, 0); glVertex2f(x1, y0)
        glTexCoord2f(1, 1); glVertex2f(x1, y1)
        glTexCoord2f(0, 1); glVertex2f(x0, y1)
        glEnd()

        glBindTexture(GL_TEXTURE_2D, 0)
        glDisable(GL_TEXTURE_2D)
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_LIGHTING)

        glMatrixMode(GL_PROJECTION); glPopMatrix()
        glMatrixMode(GL_MODELVIEW);  glPopMatrix()

    @staticmethod
    def DrawInfoPanel(obj, meta, win_w, win_h):
        """
        Render a metadata HUD panel in the bottom-right corner when a
        file or folder is aimed at. Shows name, type, size, modified date,
        and permissions. Symlinks additionally show their target path.
        """
        if obj is None or meta is None:
            return

        lines = [obj.file_name]
        lines.append(f"Type: {meta.file_type}")
        lines.append(f"Size: {format_size(meta.size_bytes)}")
        lines.append(f"Modified: {meta.modified_date.strftime('%Y-%m-%d  %H:%M')}")
        lines.append(f"Perms: {meta.permissions}")
        if meta.is_symlink and meta.symlink_target:
            lines.append(f"\u2192 {meta.symlink_target}")
        if getattr(obj, "is_link", False):
            link_kind = "shortcut" if getattr(obj, "is_shortcut", False) else "symlink"
            lines.append(f"Link: {link_kind}")
            if getattr(obj, "link_target_path", None):
                lines.append(f"Target: {obj.link_target_path}")
            if getattr(obj, "link_broken", False):
                lines.append("[BROKEN LINK]")
            if getattr(obj, "in_cycle", False):
                lines.append("[CYCLE WARNING]")
            if getattr(obj, "link_target_path", None) and not getattr(obj, "link_target_in_view", True):
                lines.append("Target not visible in this directory view")

        panel_max_w = min(420, max(200, win_w // 3))

        cache_key = "|".join(lines) + f"|maxw={panel_max_w}"
        if cache_key != Renderer._info_panel_text:
            Renderer._info_panel_text = cache_key
            size_buf = [0, 0]
            Renderer._info_panel_texture_id = Renderer._upload_panel_texture(
                lines, size_buf, max_w=panel_max_w
            )
            Renderer._info_panel_size = tuple(size_buf)

        if Renderer._info_panel_texture_id is None:
            return

        lw, lh = Renderer._info_panel_size
        margin = 20
        x0 = win_w - lw - margin
        y0 = margin
        Renderer._draw_textured_quad(Renderer._info_panel_texture_id, x0, y0, lw, lh, win_w, win_h)

    @staticmethod
    def DrawHoverTooltip(obj, meta, win_w, win_h):
        """
        Render a compact one-line tooltip above the crosshair after the
        user has aimed at the same object for >500 ms.
        Format: "filename  ·  type  ·  size"
        """
        if obj is None or meta is None:
            return

        text = f"{obj.file_name}  \u00b7  {meta.file_type}  \u00b7  {format_size(meta.size_bytes)}"

        if text != Renderer._hover_tooltip_text:
            Renderer._hover_tooltip_text = text
            size_buf = [0, 0]
            Renderer._hover_tooltip_texture_id = Renderer._upload_single_line_texture(text, size_buf)
            Renderer._hover_tooltip_size = tuple(size_buf)

        if Renderer._hover_tooltip_texture_id is None:
            return

        lw, lh = Renderer._hover_tooltip_size
        cx = win_w // 2
        cy = win_h // 2
        x0 = cx - lw // 2
        y0 = cy + 30           # 30 px above centre in GL ortho coords (y-up)
        Renderer._draw_textured_quad(Renderer._hover_tooltip_texture_id, x0, y0, lw, lh, win_w, win_h)

    @staticmethod
    def DrawDirectoryPreview(obj, children, win_w, win_h, hovered_name=None):
        """
        Render a floating mini-grid of coloured cubes above a hovered directory.
        Up to MAX_ITEMS entries shown in a COLS-wide grid. If the crosshair
        is over a cube, its name is shown in a label above the grid.
        An overflow count is shown if the directory has more than MAX_ITEMS entries.
        """
        if obj is None:
            return

        MAX_ITEMS = 30
        COLS      = 6
        CUBE_SIZE = 0.18
        CUBE_GAP  = 0.46
        LIFT      = 0.55

        base_y  = obj.y + obj.height / 2 + LIFT + CUBE_SIZE
        grid_w  = COLS * CUBE_GAP
        start_x = obj.x - grid_w / 2 + CUBE_GAP / 2
        start_z = obj.z

        shown = children[:MAX_ITEMS]
        rows  = max(1, -(-len(shown) // COLS))  # ceiling division

        glDisable(GL_LIGHTING)
        glEnable(GL_DEPTH_TEST)

        if not shown:
            label = "(empty)"
            size_buf = [0, 0]
            tex = Renderer._upload_single_line_texture(label, size_buf)
            if tex:
                lw, lh = size_buf
                px, py = Renderer._world_to_screen(obj.x, base_y, obj.z, win_w, win_h)
                if px is not None:
                    Renderer._draw_textured_quad(tex, int(px - lw/2), int(py - lh/2), lw, lh, win_w, win_h)
                glDeleteTextures([tex])
            glEnable(GL_LIGHTING)
            return

        for i, entry in enumerate(shown):
            col = i % COLS
            row = i // COLS
            cx  = start_x + col * CUBE_GAP
            cy  = base_y  + row * CUBE_GAP
            r, g, b = Renderer._preview_color(entry)
            Renderer._draw_mini_cube(cx, cy, start_z, CUBE_SIZE, r, g, b)

        glEnable(GL_LIGHTING)

        # Hovered mini-cube name label — shown above the grid
        if hovered_name:
            size_buf = [0, 0]
            tex = Renderer._upload_single_line_texture(hovered_name, size_buf)
            if tex:
                lw, lh = size_buf
                px, py = Renderer._world_to_screen(
                    obj.x, base_y + rows * CUBE_GAP + 0.35, obj.z, win_w, win_h)
                if px is not None:
                    Renderer._draw_textured_quad(tex, int(px - lw/2), int(py - lh/2), lw, lh, win_w, win_h)
                glDeleteTextures([tex])

        # Overflow label — shown below the grid so it never collides with the name label
        overflow = len(children) - MAX_ITEMS
        if overflow > 0:
            label = f"+ {overflow} more"
            size_buf = [0, 0]
            tex = Renderer._upload_single_line_texture(label, size_buf)
            if tex:
                lw, lh = size_buf
                px, py = Renderer._world_to_screen(
                    obj.x, base_y - 0.3, obj.z, win_w, win_h)
                if px is not None:
                    Renderer._draw_textured_quad(tex, int(px - lw/2), int(py - lh/2), lw, lh, win_w, win_h)
                glDeleteTextures([tex])

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _upload_panel_texture(lines: list, size_buf: list, max_w: int = 0) -> int | None:
        """
        Render multiple text lines onto a single RGBA surface, upload it
        as an OpenGL texture, and write (w, h) into size_buf[0..1].
        First line uses the bold font; remaining lines use the small font.
        If max_w > 0, the panel is capped at that pixel width and any line
        that overflows is clipped with an ellipsis.
        Returns the texture ID, or None on failure.
        """
        try:
            pygame.font.init()
            title_font = Renderer._get_font()
            body_font  = Renderer._get_small_font()

            pad      = 10
            line_gap = 4

            raw_surfs = []
            for i, line in enumerate(lines):
                font = title_font if i == 0 else body_font
                raw_surfs.append((font.render(line, True, (255, 255, 255)), font))

            content_w = max(s.get_width() for s, _ in raw_surfs)
            if max_w > 0:
                content_w = min(content_w, max_w - pad * 2)

            surfaces = []
            for surf, font in raw_surfs:
                if surf.get_width() > content_w:
                    ellipsis_w = font.size("...")[0]
                    text_budget = content_w - ellipsis_w
                    if text_budget <= 0:
                        surf = font.render("...", True, (255, 255, 255))
                    else:
                        clipped = surf.subsurface((0, 0, text_budget, surf.get_height()))
                        ell_surf = font.render("...", True, (255, 255, 255))
                        combined = pygame.Surface((text_budget + ellipsis_w, surf.get_height()), pygame.SRCALPHA)
                        combined.blit(clipped, (0, 0))
                        combined.blit(ell_surf, (text_budget, 0))
                        surf = combined
                surfaces.append(surf)

            w = content_w + pad * 2
            h = sum(s.get_height() for s in surfaces) + line_gap * (len(surfaces) - 1) + pad * 2

            bg = pygame.Surface((w, h), pygame.SRCALPHA)
            bg.fill((0, 0, 0, 160))

            y = pad
            for surf in surfaces:
                bg.blit(surf, (pad, y))
                y += surf.get_height() + line_gap

            bg  = pygame.transform.flip(bg, False, True)
            raw = pygame.image.tostring(bg, "RGBA", False)

            tex_id = glGenTextures(1)
            glBindTexture(GL_TEXTURE_2D, tex_id)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
            glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, w, h, 0, GL_RGBA, GL_UNSIGNED_BYTE, raw)
            glBindTexture(GL_TEXTURE_2D, 0)

            size_buf[0], size_buf[1] = w, h
            return tex_id
        except Exception:
            return None

    @staticmethod
    def _upload_single_line_texture(text: str, size_buf: list) -> int | None:
        """
        Render a single line of text, upload as a texture, write (w, h)
        into size_buf[0..1].  Returns the texture ID, or None on failure.
        """
        try:
            pygame.font.init()
            font = Renderer._get_small_font()

            pad       = 6
            text_surf = font.render(text, True, (255, 255, 255))
            w = text_surf.get_width()  + pad * 2
            h = text_surf.get_height() + pad * 2

            bg = pygame.Surface((w, h), pygame.SRCALPHA)
            bg.fill((0, 0, 0, 160))
            bg.blit(text_surf, (pad, pad))
            bg  = pygame.transform.flip(bg, False, True)
            raw = pygame.image.tostring(bg, "RGBA", False)

            tex_id = glGenTextures(1)
            glBindTexture(GL_TEXTURE_2D, tex_id)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
            glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, w, h, 0, GL_RGBA, GL_UNSIGNED_BYTE, raw)
            glBindTexture(GL_TEXTURE_2D, 0)

            size_buf[0], size_buf[1] = w, h
            return tex_id
        except Exception:
            return None

    @staticmethod
    def _fit_text(text: str, font, max_width: int) -> str:
        if font.size(text)[0] <= max_width:
            return text
        ellipsis = "..."
        if font.size(ellipsis)[0] > max_width:
            return ""

        left = 0
        right = len(text)
        best = ellipsis
        while left <= right:
            mid = (left + right) // 2
            candidate = text[:mid].rstrip() + ellipsis
            if font.size(candidate)[0] <= max_width:
                best = candidate
                left = mid + 1
            else:
                right = mid - 1
        return best

    @staticmethod
    def _draw_textured_quad(tex_id, x0, y0, lw, lh, win_w, win_h):
        """Draw a texture-mapped quad in screen-space (OpenGL ortho HUD)."""
        x1, y1 = x0 + lw, y0 + lh

        glMatrixMode(GL_PROJECTION); glPushMatrix(); glLoadIdentity()
        glOrtho(0, win_w, 0, win_h, -1, 1)
        glMatrixMode(GL_MODELVIEW); glPushMatrix(); glLoadIdentity()

        glDisable(GL_DEPTH_TEST)
        glDisable(GL_LIGHTING)
        glEnable(GL_TEXTURE_2D)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

        glBindTexture(GL_TEXTURE_2D, tex_id)
        glColor4f(1, 1, 1, 1)
        glBegin(GL_QUADS)
        glTexCoord2f(0, 0); glVertex2f(x0, y0)
        glTexCoord2f(1, 0); glVertex2f(x1, y0)
        glTexCoord2f(1, 1); glVertex2f(x1, y1)
        glTexCoord2f(0, 1); glVertex2f(x0, y1)
        glEnd()

        glBindTexture(GL_TEXTURE_2D, 0)
        glDisable(GL_TEXTURE_2D)
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_LIGHTING)

        glMatrixMode(GL_PROJECTION); glPopMatrix()
        glMatrixMode(GL_MODELVIEW);  glPopMatrix()

    @staticmethod
    def _preview_color(entry):
        """Return RGB color for a DirEntry (file or directory)."""
        if entry.is_dir(follow_symlinks=False):
            return Renderer._FOLDER_COLOR

        name = entry.name.lower()
        for ext, color in Renderer._EXT_COLORS.items():
            if name.endswith(ext):
                return color
        return Renderer._DEFAULT_COLOR

    @staticmethod
    def _draw_mini_cube(x, y, z, size, r, g, b):
        """Draw a small cube at world position (x, y, z)."""
        glPushMatrix()
        glTranslatef(x, y, z)
        glColor3f(r, g, b)

        glBegin(GL_TRIANGLES)
        # Front face
        glVertex3f(-size, -size,  size)
        glVertex3f( size, -size,  size)
        glVertex3f( size,  size,  size)
        glVertex3f(-size, -size,  size)
        glVertex3f( size,  size,  size)
        glVertex3f(-size,  size,  size)
        # Back face
        glVertex3f(-size, -size, -size)
        glVertex3f(-size,  size, -size)
        glVertex3f( size,  size, -size)
        glVertex3f(-size, -size, -size)
        glVertex3f( size,  size, -size)
        glVertex3f( size, -size, -size)
        # Top face
        glVertex3f(-size,  size, -size)
        glVertex3f(-size,  size,  size)
        glVertex3f( size,  size,  size)
        glVertex3f(-size,  size, -size)
        glVertex3f( size,  size,  size)
        glVertex3f( size,  size, -size)
        # Bottom face
        glVertex3f(-size, -size, -size)
        glVertex3f( size, -size, -size)
        glVertex3f( size, -size,  size)
        glVertex3f(-size, -size, -size)
        glVertex3f( size, -size,  size)
        glVertex3f(-size, -size,  size)
        # Right face
        glVertex3f( size, -size, -size)
        glVertex3f( size,  size, -size)
        glVertex3f( size,  size,  size)
        glVertex3f( size, -size, -size)
        glVertex3f( size,  size,  size)
        glVertex3f( size, -size,  size)
        # Left face
        glVertex3f(-size, -size, -size)
        glVertex3f(-size, -size,  size)
        glVertex3f(-size,  size,  size)
        glVertex3f(-size, -size, -size)
        glVertex3f(-size,  size,  size)
        glVertex3f(-size,  size, -size)
        glEnd()

        glPopMatrix()

    @staticmethod
    def _world_to_screen(wx, wy, wz, win_w, win_h):
        """
        Convert world coordinates to screen coordinates using the current
        projection and modelview matrices. Returns (screen_x, screen_y) or
        None if the point is behind the camera or projection fails.
        """
        modelview = glGetDoublev(GL_MODELVIEW_MATRIX)
        projection = glGetDoublev(GL_PROJECTION_MATRIX)
        viewport = glGetIntegerv(GL_VIEWPORT)

        result = gluProject(wx, wy, wz, modelview, projection, viewport)
        if result is None:
            return None

        sx, sy, sz = result
        sy = win_h - sy
        return (sx, sy)
