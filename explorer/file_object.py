"""
FileExplorer3D - file_object.py
A 3D prism representing a file or folder in the scene.
"""

import os
from OpenGL.GL import *

EXTENSION_COLORS = {
    ".py":   (0.2, 0.9, 0.3),
    ".js":   (0.9, 0.85, 0.2),
    ".ts":   (0.2, 0.5, 0.9),
    ".html": (0.9, 0.4, 0.1),
    ".css":  (0.3, 0.6, 1.0),
    ".cpp":  (0.6, 0.3, 0.9),
    ".c":    (0.5, 0.3, 0.8),
    ".h":    (0.7, 0.4, 0.9),
    ".txt":  (0.9, 0.9, 0.9),
    ".md":   (0.8, 0.8, 0.7),
    ".pdf":  (0.9, 0.1, 0.1),
    ".json": (0.9, 0.7, 0.2),
    ".yaml": (0.9, 0.7, 0.2),
    ".yml":  (0.9, 0.7, 0.2),
    ".xml":  (0.7, 0.5, 0.2),
    ".png":  (0.9, 0.8, 0.2),
    ".jpg":  (0.9, 0.75, 0.2),
    ".jpeg": (0.9, 0.75, 0.2),
    ".gif":  (0.9, 0.6, 0.7),
    ".svg":  (0.4, 0.9, 0.8),
    ".zip":  (0.6, 0.4, 0.2),
    ".tar":  (0.6, 0.4, 0.2),
    ".gz":   (0.5, 0.35, 0.15),
}

FOLDER_COLOR  = (0.15, 0.3, 0.8)
DEFAULT_COLOR = (0.65, 0.65, 0.65)
ERROR_COLOR   = (0.9, 0.1, 0.1)


class FileObject:
    """A 3D prism representing a file or folder."""

    FOLDER_SIZE = (1.0, 1.0, 1.0)
    FILE_SIZE   = (0.5, 0.5, 0.5)

    def __init__(self, file_path, is_dir):
        self.file_path = file_path
        self.file_name = os.path.basename(file_path)
        self.is_dir    = is_dir
        self.file_ext  = "" if is_dir else os.path.splitext(self.file_name)[1].lower()

        self.width, self.height, self.depth = (
            self.FOLDER_SIZE if is_dir else self.FILE_SIZE
        )
        self.x = 0.0
        self.y = 0.0
        self.z = 0.0

        self.color = self._pick_color()

    def _pick_color(self):
        if self.is_dir:
            return FOLDER_COLOR
        return EXTENSION_COLORS.get(self.file_ext, DEFAULT_COLOR)

    def set_position(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z

    def flash_error(self):
        """Turn the object red to indicate an error (e.g. permission denied)."""
        self.color = ERROR_COLOR

    def draw(self, selected=False):
        w, h, d = self.width / 2, self.height / 2, self.depth / 2
        r, g, b = self.color

        if selected:
            r = r + (1.0 - r) * 0.3
            g = g + (0.85 - g) * 0.3
            b = b + (0.2 - b) * 0.3

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
            for face in [
                [(-w,-h, d),( w,-h, d),( w, h, d),(-w, h, d)],
                [(-w,-h,-d),(-w, h,-d),( w, h,-d),( w,-h,-d)],
                [(-w,-h,-d),(-w,-h, d),(-w, h, d),(-w, h,-d)],
                [( w,-h,-d),( w, h,-d),( w, h, d),( w,-h, d)],
                [(-w, h,-d),(-w, h, d),( w, h, d),( w, h,-d)],
                [(-w,-h,-d),( w,-h,-d),( w,-h, d),(-w,-h, d)],
            ]:
                glBegin(GL_LINE_LOOP)
                for v in face:
                    glVertex3f(*v)
                glEnd()
            glLineWidth(1.0)
            glEnable(GL_LIGHTING)
