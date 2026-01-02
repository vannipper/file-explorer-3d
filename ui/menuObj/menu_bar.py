import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
from .menu_item import MenuItem

class MenuBar:
    """The main container for MenuItems."""
    def __init__(self, config=None, font=None):
        self.config = config
        self.font = font or pygame.font.Font(None, 20)
        self.height = 34
        self.items = []
        self._text_cache = {}
        
        # Colors
        self.BAR_BG = (0.18, 0.18, 0.18, 0.95)
        self.SUB_BG = (0.12, 0.12, 0.12, 0.98)
        self.HOVER_BG = (0.26, 0.26, 0.26, 0.98)
        self.TEXT_COLOR = (235, 235, 235)
        self.HOVER_TEXT = (255, 255, 190)
        self.SEP_COLOR = (0.35, 0.35, 0.35, 1.0)

    def add_menu(self, label, children):
        """Adds a top-level menu."""
        self.items.append(MenuItem(label, children=children, font=self.font))

    def update_layout(self, win_w):
        """Call this whenever the window is resized or items are added."""
        x_offset = 10
        for item in self.items:
            item.calculate_layout(x_offset, 0, True)
            x_offset += item.rect.width + 10

    def handle_input(self, events):
        """Processes a list of events and returns an action ID if a menu item is clicked."""
        mouse_pos = pygame.mouse.get_pos()
        action_triggered = None

        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                res = self._check_click(self.items, mouse_pos)
                if res:
                    action_triggered = res
                else:
                    if mouse_pos[1] > self.height:
                        self._close_all(self.items)

        self._check_hover(self.items, mouse_pos)
        return action_triggered

    def _check_hover(self, items, mpos):
        for item in items:
            item.is_hovered = item.rect.collidepoint(mpos)
            if item.is_open and item.children:
                self._check_hover(item.children, mpos)
            if item.is_hovered and any(i.is_open for i in self.items) and not item.is_open:
                if item.rect.top == 0:
                    self._close_all(self.items)
                    item.is_open = True

    def _check_click(self, items, mpos):
        for item in items:
            if item.is_open and item.children:
                res = self._check_click(item.children, mpos)
                if res: return res
                
        for item in items:
            if item.rect.collidepoint(mpos):
                if item.label == "---": 
                    return None
                if item.children:
                    was_open = item.is_open
                    for sibling in items:
                        sibling.is_open = False
                    item.is_open = not was_open
                    return "STAY_OPEN"
                else:
                    action = item.action
                    self._close_all(self.items)
                    return action
        return None

    def _close_all(self, items):
        for item in items:
            item.is_open = False
            if item.children:
                self._close_all(item.children)

    def draw(self, win_w, win_h):
        # Save current state
        glPushAttrib(GL_ALL_ATTRIB_BITS)
        
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        glOrtho(0, win_w, win_h, 0, -1, 1)
        
        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()
        
        glDisable(GL_DEPTH_TEST)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

        # Draw Background Bar
        glDisable(GL_TEXTURE_2D)
        glColor4f(*self.BAR_BG)
        glRectf(0, 0, win_w, self.height)

        self._draw_items(self.items, True)

        # Restore Matrices and Attributes
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)
        glPopMatrix()
        glPopAttrib()

    def _draw_items(self, items, is_horizontal):
        for item in items:
            if item.is_hovered or item.is_open:
                glDisable(GL_TEXTURE_2D)
                glColor4f(*self.HOVER_BG)
                glRectf(item.rect.left, item.rect.top, item.rect.right, item.rect.bottom)

            if item.label == "---":
                glDisable(GL_TEXTURE_2D)
                glColor4f(*self.SEP_COLOR)
                glBegin(GL_LINES)
                glVertex2f(item.rect.left + 10, item.rect.centery)
                glVertex2f(item.rect.right - 10, item.rect.centery)
                glEnd()
            else:
                glEnable(GL_TEXTURE_2D)
                color = self.HOVER_TEXT if (item.is_hovered or item.is_open) else self.TEXT_COLOR
                tex, tw, th = self._get_text_tex(item.label, color)
                tx = item.rect.left + (12 if not is_horizontal else (item.rect.width - tw)//2)
                ty = item.rect.top + (item.rect.height - th)//2
                self._draw_tex_quad(tx, ty, tw, th, tex)

            if item.is_open and item.children:
                glDisable(GL_TEXTURE_2D)
                glColor4f(*self.SUB_BG)
                r = item.children[0].rect
                glRectf(r.left, r.top, r.left + item.submenu_width, r.top + item.submenu_height)
                
                glColor4f(*self.SEP_COLOR)
                glBegin(GL_LINE_LOOP)
                glVertex2f(r.left, r.top); glVertex2f(r.left + item.submenu_width, r.top)
                glVertex2f(r.left + item.submenu_width, r.top + item.submenu_height); glVertex2f(r.left, r.top + item.submenu_height)
                glEnd()
                
                self._draw_items(item.children, False)

    def _get_text_tex(self, text, color):
        key = (text, color)
        if key not in self._text_cache:
            surf = self.font.render(text, True, color)
            data = pygame.image.tostring(surf, "RGBA", True)
            tid = glGenTextures(1)
            glBindTexture(GL_TEXTURE_2D, tid)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
            glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, surf.get_width(), surf.get_height(), 0, GL_RGBA, GL_UNSIGNED_BYTE, data)
            self._text_cache[key] = (tid, surf.get_width(), surf.get_height())
        return self._text_cache[key]

    def _draw_tex_quad(self, x, y, w, h, tid):
        glColor4f(1, 1, 1, 1)
        glBindTexture(GL_TEXTURE_2D, tid)
        glBegin(GL_QUADS)
        glTexCoord2f(0, 1); glVertex2f(x, y)
        glTexCoord2f(1, 1); glVertex2f(x + w, y)
        glTexCoord2f(1, 0); glVertex2f(x + w, y + h)
        glTexCoord2f(0, 0); glVertex2f(x, y + h)
        glEnd()