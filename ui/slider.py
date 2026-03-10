import pygame
from OpenGL.GL import *


class Slider:
    """Simple horizontal slider rendered with OpenGL textures for labels."""

    def __init__(self, label, key=None, min_value=0.0, max_value=1.0, value=0.0, on_change=None, font=None, display_percent=False, min_percent=1, max_percent=400):
        self.label = label
        self.key = key
        self.min = min_value
        self.max = max_value
        self.value = float(value)
        self.on_change = on_change
        self.font = font or pygame.font.Font(None, 24)
        self.dragging = False
        self.rect = pygame.Rect(0, 0, 0, 0)  # will be set in draw
        self.display_percent = display_percent
        self.min_percent = min_percent
        self.max_percent = max_percent
        self._text_cache = {}
        self.label_width = 400

    def _value_to_pos(self, x, width):
        """Convert current value to knob x position."""
        t = (self.value - self.min) / (self.max - self.min) if self.max != self.min else 0.0
        return int(x + t * width)

    def _pos_to_value(self, px, x, width):
        """Convert mouse x to value in range."""
        t = (px - x) / float(width)
        t = max(0.0, min(1.0, t))
        return self.min + t * (self.max - self.min)

    def handle_event(self, event):
        """Handle pygame events for dragging. Returns True if handled."""
        label_width = self.label_width
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos
            if self.rect.collidepoint(mx, my):
                self.dragging = True
                # update immediately
                new_val = self._pos_to_value(mx, self.rect.x + label_width, self.rect.width - label_width - 80)
                self.set_value(new_val)
                return True
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if self.dragging:
                self.dragging = False
                return True
        elif event.type == pygame.MOUSEMOTION:
            if self.dragging:
                mx, my = event.pos
                new_val = self._pos_to_value(mx, self.rect.x + label_width, self.rect.width - label_width - 80)
                self.set_value(new_val)
                return True
        return False

    def set_value(self, v):
        """Set value and call callback if changed."""
        v = max(self.min, min(self.max, float(v)))
        if abs(v - self.value) > 1e-6:
            self.value = v
            if self.on_change:
                self.on_change(self.value)

    def render_text_to_texture(self, text, color, font):
        """Render text to a texture and return texture ID and dimensions. Uses cache."""
        key = (text, color, getattr(font, 'name', None), getattr(font, 'size', None))
        if key in self._text_cache:
            return self._text_cache[key]
        text_surface = font.render(text, True, color)
        text_data = pygame.image.tostring(text_surface, "RGBA", True)

        texture_id = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, texture_id)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, text_surface.get_width(),
                     text_surface.get_height(), 0, GL_RGBA, GL_UNSIGNED_BYTE, text_data)

        self._text_cache[key] = (texture_id, text_surface.get_width(), text_surface.get_height())
        return self._text_cache[key]

    def draw(self, x, y, width, font):
        """Draw slider at given position. x,y are top-left, width is full slider width."""
        # Fixed label width of 400 pixels
        label_width = self.label_width
        
        # store rect for interaction (includes label and slider area)
        self.rect = pygame.Rect(x, y, width, 32)

        # draw label text on left (fixed 400 pixel width)
        label_tex, lw, lh = self.render_text_to_texture(self.label, (220, 220, 220), font)
        glColor4f(1, 1, 1, 1)
        self._draw_textured_quad(x, y, lw, lh, label_tex)
        # do not delete cached texture

        # slider bar starts after the label
        bar_x = x + label_width
        bar_y = y + 16
        bar_w = width - label_width - 80  # leave space for value on right
        bar_h = 6

        # background bar
        glColor4f(0.3, 0.3, 0.3, 1.0)
        glBegin(GL_QUADS)
        glVertex2f(bar_x, bar_y - bar_h/2)
        glVertex2f(bar_x + bar_w, bar_y - bar_h/2)
        glVertex2f(bar_x + bar_w, bar_y + bar_h/2)
        glVertex2f(bar_x, bar_y + bar_h/2)
        glEnd()

        # filled portion
        t = (self.value - self.min) / (self.max - self.min) if self.max != self.min else 0.0
        fill_w = int(bar_w * t)
        glColor4f(0.8, 0.6, 0.1, 1.0)
        glBegin(GL_QUADS)
        glVertex2f(bar_x, bar_y - bar_h/2)
        glVertex2f(bar_x + fill_w, bar_y - bar_h/2)
        glVertex2f(bar_x + fill_w, bar_y + bar_h/2)
        glVertex2f(bar_x, bar_y + bar_h/2)
        glEnd()

        # knob
        knob_x = bar_x + int(bar_w * t)
        knob_r = 8
        glColor4f(0.9, 0.9, 0.9, 1.0)
        glBegin(GL_TRIANGLE_FAN)
        glVertex2f(knob_x, bar_y)
        for a in range(0, 361, 30):
            ang = a * 3.14159 / 180.0
            glVertex2f(knob_x + knob_r * __import__('math').cos(ang), bar_y + knob_r * __import__('math').sin(ang))
        glEnd()

        # draw value text on right (display as percentage if requested)
        if self.display_percent:
            display_val = int(max(self.min_percent, min(self.max_percent, round(self.value * 100))))
            val_text = f"{display_val}%"
        else:
            val_text = f"{self.value:.2f}"

        val_tex, vw, vh = self.render_text_to_texture(val_text, (255, 255, 150), font)
        # position with margin after slider bar, vertically centered with bar
        val_x = bar_x + bar_w + 10  # 10 pixel margin
        val_y = bar_y - vh / 2  # vertically center with bar
        self._draw_textured_quad(val_x, val_y, vw, vh, val_tex)
        # do not delete cached texture

    def _draw_textured_quad(self, x, y, w, h, texture_id):
        glEnable(GL_TEXTURE_2D)
        glBindTexture(GL_TEXTURE_2D, texture_id)
        glBegin(GL_QUADS)
        glTexCoord2f(0, 1); glVertex2f(x, y)
        glTexCoord2f(1, 1); glVertex2f(x + w, y)
        glTexCoord2f(1, 0); glVertex2f(x + w, y + h)
        glTexCoord2f(0, 0); glVertex2f(x, y + h)
        glEnd()
        glDisable(GL_TEXTURE_2D)
