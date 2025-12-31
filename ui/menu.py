import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *

from ui.slider import Slider


class Menu:
    """Main menu for game settings and exit."""

    def __init__(self, config, on_toggle_fullscreen=None):
        self.config = config
        self.active = False
        self.selected_option = 0
        # numeric settings removed from options (they are handled by sliders)
        self.options = [
            ("Show Grid", "show_grid"),
            ("Show Axes", "show_axes"),
            ("Debug Info", "debug_info"),
            ("Start Fullscreen", "start_fullscreen"),
            ("Exit", None),
        ]
        # Try to use a system font, fallback to default
        try:
            self.font = pygame.font.Font("C:/Windows/Fonts/segoeui.ttf", 48)
            self.small_font = pygame.font.Font("C:/Windows/Fonts/segoeui.ttf", 36)
        except:
            self.font = pygame.font.Font(None, 48)
            self.small_font = pygame.font.Font(None, 36)

        self.option_rects = []  # Store rects for mouse collision detection
        self.on_toggle_fullscreen = on_toggle_fullscreen

        # Sliders: range 1%..400%, default from config (now defaults to 1.0)
        self.sliders = [
            Slider("Mouse Sensitivity", key="mouse_sensitivity",
                   min_value=0.01, max_value=4.0,
                   value=self.config.get("mouse_sensitivity", 1.0),
                   on_change=lambda v: self._on_slider_change("mouse_sensitivity", v),
                   font=self.small_font,
                   display_percent=True),
            Slider("Move Speed", key="move_speed",
                   min_value=0.01, max_value=4.0,
                   value=self.config.get("move_speed", 1.0),
                   on_change=lambda v: self._on_slider_change("move_speed", v),
                   font=self.small_font,
                   display_percent=True)
        ]

    def _on_slider_change(self, key, value):
        """Callback when a slider changes — update config immediately."""
        self.config.set(key, value)

    def toggle(self):
        """Toggle menu visibility and manage cursor/grab state."""
        self.active = not self.active
        if self.active:
            # show cursor and release grab while in menu
            pygame.mouse.set_visible(True)
            pygame.event.set_grab(False)
        else:
            # hide cursor and re-grab when leaving menu
            pygame.mouse.set_visible(False)
            pygame.event.set_grab(True)
            self.config.save()

    def handle_input(self):
        """
        Handle menu input (keyboard and mouse).
        Returns True if user selected Exit.
        """
        if not self.active:
            return False

        # Forward events to sliders first (they may start/stop dragging)
        for event in pygame.event.get():
            # allow sliders to process events
            for s in self.sliders:
                if s.handle_event(event):
                    # slider handled event that requires no further processing
                    pass

            if event.type == QUIT:
                return True
            if event.type == KEYDOWN:
                if event.key == K_ESCAPE:
                    self.toggle()
                    return False
                elif event.key == K_UP:
                    self.selected_option = (self.selected_option - 1) % len(self.options)
                elif event.key == K_DOWN:
                    self.selected_option = (self.selected_option + 1) % len(self.options)
                elif event.key == K_RETURN:
                    return self.select_option()
            elif event.type == MOUSEMOTION:
                # Update selection highlight from mouse position (use option_rects)
                mouse_x, mouse_y = event.pos
                for i, rect in enumerate(self.option_rects):
                    if rect.collidepoint(mouse_x, mouse_y):
                        self.selected_option = i
                        break
            elif event.type == MOUSEBUTTONDOWN:
                if event.button == 1:  # Left click -> if over an option, select it
                    # check options
                    mouse_x, mouse_y = event.pos
                    for i, rect in enumerate(self.option_rects):
                        if rect.collidepoint(mouse_x, mouse_y):
                            self.selected_option = i
                            return self.select_option()
                    # otherwise clicks on slider handled by slider.handle_event above

        return False

    def select_option(self):
        """Handle selection of current option."""
        name, key = self.options[self.selected_option]

        if key is None:  # Exit option
            self.config.save()
            return True

        # For boolean settings, toggle them
        if isinstance(self.config.get(key), bool):
            new_val = not self.config.get(key)
            self.config.set(key, new_val)

            # If this is the fullscreen setting, apply immediately via callback
            if key == "start_fullscreen" and self.on_toggle_fullscreen:
                self.on_toggle_fullscreen(new_val)

        return False

    def render_text_to_texture(self, text, color, font):
        """Render text to a texture and return texture ID and dimensions."""
        text_surface = font.render(text, True, color)
        text_data = pygame.image.tostring(text_surface, "RGBA", True)

        texture_id = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, texture_id)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, text_surface.get_width(),
                     text_surface.get_height(), 0, GL_RGBA, GL_UNSIGNED_BYTE, text_data)

        return texture_id, text_surface.get_width(), text_surface.get_height()

    def draw_text_quad(self, x, y, width, height, texture_id):
        """Draw a textured quad for text."""
        glBindTexture(GL_TEXTURE_2D, texture_id)
        glBegin(GL_QUADS)
        glTexCoord2f(0, 1); glVertex2f(x, y)
        glTexCoord2f(1, 1); glVertex2f(x + width, y)
        glTexCoord2f(1, 0); glVertex2f(x + width, y + height)
        glTexCoord2f(0, 0); glVertex2f(x, y + height)
        glEnd()

    def draw_debug_info(self, player_pos, fps, win_w, win_h):
        """Draw debug overlay with FPS and player position."""
        if not self.config.get("debug_info", False) or self.active:
            return

        # Switch to 2D projection for debug text
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

        # Prepare debug text
        debug_lines = [
            f"FPS: {fps:.1f}",
            f"Pos: ({player_pos[0]:.2f}, {player_pos[1]:.2f}, {player_pos[2]:.2f})",
        ]

        # Render debug text using texture rendering
        y_pos = 20
        for line in debug_lines:
            tex, w, h = self.render_text_to_texture(line, (100, 200, 255), self.small_font)
            glColor4f(1, 1, 1, 1)
            self.draw_text_quad(10, y_pos, w, h, tex)
            glDeleteTextures([tex])
            y_pos += 30

        glDisable(GL_BLEND)
        glDisable(GL_TEXTURE_2D)
        glEnable(GL_DEPTH_TEST)

        # Restore 3D projection
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)
        glPopMatrix()

    def draw(self):
        """Draw the menu using OpenGL."""
        if not self.active:
            return

        # Get current window size from the display surface
        surf = pygame.display.get_surface()
        if not surf:
            return
        win_w, win_h = surf.get_size()

        # Switch to 2D projection for menu rendering using actual window size
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

        # Draw semi-transparent overlay that fits the window
        glDisable(GL_TEXTURE_2D)
        glColor4f(0, 0, 0, 0.5)
        glBegin(GL_QUADS)
        glVertex2f(0, 0)
        glVertex2f(win_w, 0)
        glVertex2f(win_w, win_h)
        glVertex2f(0, win_h)
        glEnd()

        glEnable(GL_TEXTURE_2D)

        # Render menu title (position relative to window size)
        title_tex, title_w, title_h = self.render_text_to_texture("SETTINGS", (255, 200, 100), self.font)
        glColor4f(1, 1, 1, 1)
        self.draw_text_quad(50, 50, title_w, title_h, title_tex)
        glDeleteTextures([title_tex])

        # Clear option rects for this frame
        self.option_rects = []

        # Calculate starting Y offset as a fraction of the window height for better scaling
        y_offset = int(win_h * 0.2)

        # Render menu options and track their rects (only non-numeric options)
        for i, (name, key) in enumerate(self.options):
            color = (255, 255, 100) if i == self.selected_option else (200, 200, 200)

            # boolean / toggle options show value, Exit shows name
            if key is not None and isinstance(self.config.get(key), bool):
                value = self.config.get(key)
                text = f"{name}: {value}"
            else:
                text = name

            option_tex, option_w, option_h = self.render_text_to_texture(text, color, self.small_font)
            glColor4f(1, 1, 1, 1)

            # position option x relative to window width (left margin of 5% of width)
            x_pos = int(win_w * 0.05)
            self.draw_text_quad(x_pos, y_offset, option_w, option_h, option_tex)

            # Store rect for mouse collision detection (approximate)
            self.option_rects.append(pygame.Rect(x_pos, y_offset, option_w, option_h))

            glDeleteTextures([option_tex])
            y_offset += int(win_h * 0.06)

        # After drawing options, draw sliders on the right side at their own positions
        slider_x = int(win_w * 0.4)
        slider_y = int(win_h * 0.2)
        slider_w = int(win_w * 0.5)
        for s in self.sliders:
            s.draw(slider_x, slider_y, slider_w, self.small_font)
            slider_y += int(win_h * 0.08)

        glDisable(GL_BLEND)
        glDisable(GL_TEXTURE_2D)
        glEnable(GL_DEPTH_TEST)

        # Restore 3D projection
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)
        glPopMatrix()