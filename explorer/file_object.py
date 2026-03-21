"""
FileExplorer3D - file_object.py
Contains the FileObject class which represents a file or folder in the 3D scene.
"""

import os
from OpenGL.GL import *

EXTENSION_COLORS = {
    ".py":    (0.2, 0.9, 0.3),
    ".js":    (0.9, 0.85, 0.2),
    ".ts":    (0.2, 0.5, 0.9),
    ".html":  (0.9, 0.4, 0.1),
    ".css":   (0.3, 0.6, 1.0),
    ".cpp":   (0.6, 0.3, 0.9),
    ".c":     (0.5, 0.3, 0.8),
    ".h":     (0.7, 0.4, 0.9),
    ".txt":   (0.9, 0.9, 0.9),
    ".md":    (0.8, 0.8, 0.7),
    ".pdf":   (0.9, 0.1, 0.1),
    ".json":  (0.9, 0.7, 0.2),
    ".yaml":  (0.9, 0.7, 0.2),
    ".yml":   (0.9, 0.7, 0.2),
    ".xml":   (0.7, 0.5, 0.2),
    ".png":   (0.9, 0.8, 0.2),
    ".jpg":   (0.9, 0.75, 0.2),
    ".jpeg":  (0.9, 0.75, 0.2),
    ".gif":   (0.9, 0.6, 0.7),
    ".svg":   (0.4, 0.9, 0.8),
    ".zip":   (0.6, 0.4, 0.2),
    ".tar":   (0.6, 0.4, 0.2),
    ".gz":    (0.5, 0.35, 0.15),
}

FOLDER_COLOR    = (0.2, 0.4, 0.9)
DEFAULT_COLOR   = (0.65, 0.65, 0.65)

HIGHLIGHT_COLOR = (1.0, 0.85, 0.2)  # warm yellow tint when selected
HIGHLIGHT_BLEND = 0.5               # 0 = original, 1 = full highlight


def _tint(color, selected: bool):
    """Lerp color toward HIGHLIGHT_COLOR when selected."""
    if not selected:
        return color
    return (
        color[0] + (HIGHLIGHT_COLOR[0] - color[0]) * HIGHLIGHT_BLEND,
        color[1] + (HIGHLIGHT_COLOR[1] - color[1]) * HIGHLIGHT_BLEND,
        color[2] + (HIGHLIGHT_COLOR[2] - color[2]) * HIGHLIGHT_BLEND,
    )


class FileObject:

    FOLDER_SIZE = (1.0, 1.0, 1.0)
    FILE_SIZE   = (0.5, 0.5, 0.5)

    def __init__(self, file_path: str, is_dir: bool):
        self.width, self.height, self.depth = (
            self.FOLDER_SIZE if is_dir else self.FILE_SIZE
        )
        self.x = 0.0
        self.y = 0.0
        self.z = 0.0

        self.file_path = file_path
        self.file_name = os.path.basename(file_path)
        self.is_dir    = is_dir
        self.file_ext  = "" if is_dir else os.path.splitext(self.file_name)[1].lower()
        self.color     = self._get_color()

    def set_position(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z

    def _get_color(self):
        if self.is_dir:
            return FOLDER_COLOR
        return EXTENSION_COLORS.get(self.file_ext, DEFAULT_COLOR)

    def draw(self, selected: bool = False):
        """Draw the prism. Pass selected=True to apply highlight tint and outline."""
        w, h, d = self.width / 2, self.height / 2, self.depth / 2
        r, g, b = _tint(self.color, selected)

        glBegin(GL_QUADS)

        # front / back
        glColor3f(r, g, b)
        glVertex3f(-w, -h,  d); glVertex3f( w, -h,  d)
        glVertex3f( w,  h,  d); glVertex3f(-w,  h,  d)

        glColor3f(r, g, b)
        glVertex3f(-w, -h, -d); glVertex3f(-w,  h, -d)
        glVertex3f( w,  h, -d); glVertex3f( w, -h, -d)

        # left / right — slightly darker
        glColor3f(r * 0.8, g * 0.8, b * 0.8)
        glVertex3f(-w, -h, -d); glVertex3f(-w, -h,  d)
        glVertex3f(-w,  h,  d); glVertex3f(-w,  h, -d)

        glColor3f(r * 0.8, g * 0.8, b * 0.8)
        glVertex3f( w, -h, -d); glVertex3f( w,  h, -d)
        glVertex3f( w,  h,  d); glVertex3f( w, -h,  d)

        # top — brightest
        glColor3f(min(r * 1.3, 1.0), min(g * 1.3, 1.0), min(b * 1.3, 1.0))
        glVertex3f(-w,  h, -d); glVertex3f(-w,  h,  d)
        glVertex3f( w,  h,  d); glVertex3f( w,  h, -d)

        # bottom — darkest
        glColor3f(r * 0.5, g * 0.5, b * 0.5)
        glVertex3f(-w, -h, -d); glVertex3f( w, -h, -d)
        glVertex3f( w, -h,  d); glVertex3f(-w, -h,  d)

        glEnd()

        if selected:
            glDisable(GL_LIGHTING)
            glLineWidth(2.5)
            glColor3f(1.0, 1.0, 1.0)
            for verts in [
                [(-w,-h, d),( w,-h, d),( w, h, d),(-w, h, d)],  # front
                [(-w,-h,-d),(-w, h,-d),( w, h,-d),( w,-h,-d)],  # back
                [(-w,-h,-d),(-w,-h, d),(-w, h, d),(-w, h,-d)],  # left
                [( w,-h,-d),( w, h,-d),( w, h, d),( w,-h, d)],  # right
                [(-w, h,-d),(-w, h, d),( w, h, d),( w, h,-d)],  # top
                [(-w,-h,-d),( w,-h,-d),( w,-h, d),(-w,-h, d)],  # bottom
            ]:
                glBegin(GL_LINE_LOOP)
                for v in verts:
                    glVertex3f(*v)
                glEnd()
            glLineWidth(1.0)
            glEnable(GL_LIGHTING)
