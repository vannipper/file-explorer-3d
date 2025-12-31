import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *


class MenuBar:
    """Top menu bar for the editor."""

    def __init__(self, config, on_settings=None, font=None):
        self.config = config
        self.on_settings = on_settings
        # more compact default font
        self.font = font or pygame.font.Font(None, 20)
        # compact height
        self.height = 34

        self.menu_items = [
            ("File", [
                ("New", "new"),
                ("Open", "open"),
                ("Save", "save"),
                ("Save As", "save_as"),
                ("---", None),
                ("Exit", "exit")
            ]),
            ("Edit", [
                ("Undo", "undo"),
                ("Redo", "redo"),
                ("---", None),
                ("Delete Selected", "delete"),
                ("Duplicate Selected", "duplicate"),
                ("---", None),
                ("Select All", "select_all"),
                ("Deselect All", "deselect_all")
            ]),
            ("View", [
                ("Settings", "settings"),
                ("---", None),
                ("Show Grid", "show_grid"),
                ("Show Axes", "show_axes"),
                ("Debug Info", "debug_info"),
                ("---", None),
                ("Reset Camera", "reset_camera"),
                ("Fullscreen", "fullscreen")
            ]),
            ("Add", [
                ("Cube", "add_cube"),
                ("Sphere", "add_sphere"),
                ("Cylinder", "add_cylinder"),
                ("Plane", "add_plane")
            ]),
        ]

        # interactive state
        self.menu_rects = []
        self.active_menu = None
        self.submenu_rects = []
        self.hovered_item = None
        self.hovered_subitem = None

        # layout params
        self.item_positions = []  # list of (x, w, h)
        self.left_margin = 10
        self.item_spacing = 18
        self.submenu_w = 180

        # simple text texture cache: (text,color) -> (texid,w,h)
        self._text_cache = {}

        # colors (more contrast)
        self.TEXT_COLOR = (235, 235, 235)
        self.HOVER_TEXT = (255, 255, 220)
        self.SUB_HOVER_TEXT = (255, 255, 190)
        self.BAR_BG = (0.18, 0.18, 0.18, 0.95)
        self.ITEM_HOVER_BG = (0.26, 0.26, 0.26, 0.98)
        self.SUB_BG = (0.12, 0.12, 0.12, 0.98)

    def render_text_to_texture(self, text, color):
        """Render text to a texture and return texture ID and dimensions. Uses cache."""
        key = (text, color)
        if key in self._text_cache:
            return self._text_cache[key]
        text_surface = self.font.render(text, True, color)
        text_data = pygame.image.tostring(text_surface, "RGBA", True)

        texture_id = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, texture_id)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, text_surface.get_width(),
                     text_surface.get_height(), 0, GL_RGBA, GL_UNSIGNED_BYTE, text_data)
        # Make sure texture output replaces the current color (avoid modulation artifacts)
        glTexEnvf(GL_TEXTURE_ENV, GL_TEXTURE_ENV_MODE, GL_REPLACE)

        self._text_cache[key] = (texture_id, text_surface.get_width(), text_surface.get_height())
        return self._text_cache[key]

    def draw_text_quad(self, x, y, width, height, texture_id):
        """Draw a textured quad for text."""
        # Ensure white modulation so texture colors appear exactly as in the texture
        glColor4f(1.0, 1.0, 1.0, 1.0)
        glEnable(GL_TEXTURE_2D)
        glBindTexture(GL_TEXTURE_2D, texture_id)
        glBegin(GL_QUADS)
        glTexCoord2f(0, 1); glVertex2f(x, y)
        glTexCoord2f(1, 1); glVertex2f(x + width, y)
        glTexCoord2f(1, 0); glVertex2f(x + width, y + height)
        glTexCoord2f(0, 0); glVertex2f(x, y + height)
        glEnd()
        # leave texture enabled/disabled state to caller as before

    def update_layout(self, win_w, win_h):
        """Compute menu item rects (no GL drawing) so input can be handled before render."""
        x_pos = self.left_margin
        self.menu_rects = []
        self.item_positions = []
        for item_name, submenu in self.menu_items:
            tex, w, h = self.render_text_to_texture(item_name, (200, 200, 200))
            self.menu_rects.append(pygame.Rect(x_pos, 6, w, self.height - 8))
            self.item_positions.append((x_pos, w, h))
            x_pos += w + self.item_spacing

    def update_hover(self, mouse_pos):
        """Update hovered top item & hovered submenu item based on a given mouse position."""
        mx, my = mouse_pos
        # top item hover
        self.hovered_item = None
        for i, rect in enumerate(self.menu_rects):
            if rect.collidepoint(mx, my):
                self.hovered_item = i
                break

        # submenu hover if open
        self.hovered_subitem = None
        if self.active_menu is not None and 0 <= self.active_menu < len(self.menu_items):
            submenu_items = self.menu_items[self.active_menu][1]
            submenu_x = self.left_margin
            for i in range(self.active_menu):
                submenu_x += self.item_positions[i][1] + self.item_spacing
            submenu_y = self.height
            item_y = submenu_y
            for idx, (item_name, _) in enumerate(submenu_items):
                if item_name == "---":
                    item_y += 8
                    continue
                r = pygame.Rect(submenu_x, item_y, self.submenu_w, 28)
                if r.collidepoint(mx, my):
                    self.hovered_subitem = idx
                    break
                item_y += 28

    def handle_input(self, events):
        """Handle menu bar input. Returns action string or None."""
        # process events for clicks only; hover state is handled by update_hover()
        click_occurred = False
        hit = False
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                click_occurred = True
                mouse_x, mouse_y = event.pos

                # toggle open/close top menu (click on top item)
                for i, rect in enumerate(self.menu_rects):
                    if rect.collidepoint(mouse_x, mouse_y):
                        hit = True
                        if self.active_menu == i:
                            self.active_menu = None
                        else:
                            self.active_menu = i
                        self.hovered_subitem = None
                        return None

                # check submenu clicks (if open). IMPORTANT: do NOT close the menu when a submenu item is clicked.
                if self.active_menu is not None and 0 <= self.active_menu < len(self.menu_items):
                    submenu_items = self.menu_items[self.active_menu][1]
                    submenu_x = self.left_margin
                    for i in range(self.active_menu):
                        submenu_x += self.item_positions[i][1] + self.item_spacing
                    submenu_y = self.height
                    item_y = submenu_y
                    for idx, (item_name, action) in enumerate(submenu_items):
                        if item_name == "---":
                            item_y += 8
                            continue
                        r = pygame.Rect(submenu_x, item_y, self.submenu_w, 28)
                        if r.collidepoint(mouse_x, mouse_y):
                            hit = True
                            # RETURN action but do NOT close the active menu here
                            return action
                        item_y += 28

        # If there was a click and it didn't hit any menu area, close any open menu
        if click_occurred and not hit and self.active_menu is not None:
            self.active_menu = None
            self.hovered_subitem = None

        return None

    def draw(self, win_w, win_h):
        """Draw the menu bar at the top of the window."""
        # Switch to 2D projection
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        glOrtho(0, win_w, win_h, 0, -1, 1)
        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()

        glDisable(GL_DEPTH_TEST)
        glEnable(GL_TEXTURE_2D)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

        # bar background
        glDisable(GL_TEXTURE_2D)
        glColor4f(*self.BAR_BG)
        glBegin(GL_QUADS)
        glVertex2f(0, 0)
        glVertex2f(win_w, 0)
        glVertex2f(win_w, self.height)
        glVertex2f(0, self.height)
        glEnd()
        glEnable(GL_TEXTURE_2D)

        # draw items with hover background
        x_pos = self.left_margin
        self.menu_rects = []
        for i, (item_name, _) in enumerate(self.menu_items):
            is_hover = (i == self.hovered_item)
            # hover background
            if is_hover:
                tex_temp, w_temp, _ = self.render_text_to_texture(item_name, self.TEXT_COLOR)
                glDisable(GL_TEXTURE_2D)
                glColor4f(*self.ITEM_HOVER_BG)
                glBegin(GL_QUADS)
                glVertex2f(x_pos - 6, 4)
                glVertex2f(x_pos - 6 + w_temp + 12, 4)
                glVertex2f(x_pos - 6 + w_temp + 12, self.height - 6)
                glVertex2f(x_pos - 6, self.height - 6)
                glEnd()
                glEnable(GL_TEXTURE_2D)

            color = self.HOVER_TEXT if is_hover else self.TEXT_COLOR
            tex, w, h = self.render_text_to_texture(item_name, color)
            self.draw_text_quad(x_pos, (self.height - h) // 2, w, h, tex)
            self.menu_rects.append(pygame.Rect(x_pos, 6, w, self.height - 8))
            x_pos += w + self.item_spacing

        # draw submenu if active
        self.submenu_rects = []
        if self.active_menu is not None and self.active_menu < len(self.menu_items):
            submenu_items = self.menu_items[self.active_menu][1]
            submenu_x = self.left_margin
            for i in range(self.active_menu):
                submenu_x += self.item_positions[i][1] + self.item_spacing

            submenu_y = self.height
            # compute total submenu height
            total_h = 0
            for name, _ in submenu_items:
                total_h += (8 if name == "---" else 28)

            # background and border
            glDisable(GL_TEXTURE_2D)
            glColor4f(*self.SUB_BG)
            glBegin(GL_QUADS)
            glVertex2f(submenu_x, submenu_y)
            glVertex2f(submenu_x + self.submenu_w, submenu_y)
            glVertex2f(submenu_x + self.submenu_w, submenu_y + total_h)
            glVertex2f(submenu_x, submenu_y + total_h)
            glEnd()
            glColor4f(0.35, 0.35, 0.35, 1.0)
            glBegin(GL_LINE_LOOP)
            glVertex2f(submenu_x, submenu_y)
            glVertex2f(submenu_x + self.submenu_w, submenu_y)
            glVertex2f(submenu_x + self.submenu_w, submenu_y + total_h)
            glVertex2f(submenu_x, submenu_y + total_h)
            glEnd()
            glEnable(GL_TEXTURE_2D)

            # items
            item_y = submenu_y
            for idx, (item_name, action) in enumerate(submenu_items):
                if item_name == "---":
                    item_y += 8
                    continue
                is_sub_hover = (idx == self.hovered_subitem)
                if is_sub_hover:
                    glDisable(GL_TEXTURE_2D)
                    glColor4f(0.22, 0.22, 0.22, 0.98)
                    glBegin(GL_QUADS)
                    glVertex2f(submenu_x, item_y)
                    glVertex2f(submenu_x + self.submenu_w, item_y)
                    glVertex2f(submenu_x + self.submenu_w, item_y + 28)
                    glVertex2f(submenu_x, item_y + 28)
                    glEnd()
                    glEnable(GL_TEXTURE_2D)

                color = self.SUB_HOVER_TEXT if is_sub_hover else (210, 210, 210)
                tex, w, h = self.render_text_to_texture(item_name, color)
                self.draw_text_quad(submenu_x + 8, item_y + (28 - h) // 2, w, h, tex)
                self.submenu_rects.append((pygame.Rect(submenu_x, item_y, self.submenu_w, 28), action))
                item_y += 28

        glDisable(GL_BLEND)
        glDisable(GL_TEXTURE_2D)
        glEnable(GL_DEPTH_TEST)

        # Restore 3D projection
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)
        glPopMatrix()
