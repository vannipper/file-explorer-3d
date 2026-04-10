"""
FileExplorer3D - renderer.py
Contains the Renderer class, which handles the rendering of objects.
"""

import numpy as np
import pygame
from pygame.locals import *
from utils.interaction_handler import InteractionHandler
from OpenGL.GL import *
from OpenGL.GLU import *


class Renderer:

    _font = None
    _label_texture_id = None
    _label_text = None
    _label_size = (0, 0)

    @staticmethod
    def _get_font():
        if Renderer._font is None:
            pygame.font.init()
            Renderer._font = pygame.font.SysFont("Arial", 22, bold=True)
        return Renderer._font

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

        glEnable(GL_LIGHTING); glEnable(GL_LIGHT0); glEnable(GL_COLOR_MATERIAL)
        glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)
        glLightfv(GL_LIGHT0, GL_POSITION, [5, 10, 5, 1])

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
    def DrawObject(obj, selected_object):
        glPushMatrix()
        glTranslatef(obj.x, obj.y, obj.z)
        glMaterialfv(GL_FRONT, GL_EMISSION, [0.0, 0.0, 0.0, 1.0])
        obj.draw(selected=(obj is selected_object))
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
