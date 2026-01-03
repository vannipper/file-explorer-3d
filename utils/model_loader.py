import os
import pygame
from OpenGL.GL import *

class ModelLoader:
    """Parses .obj files and manages texture loading."""
    
    @staticmethod
    def load_obj(filepath):
        """
        Basic OBJ parser. 
        Returns vertices, texcoords, normals, and face indices.
        """
        vertices = []
        texcoords = []
        normals = []
        faces = []

        try:
            with open(filepath, 'r') as f:
                for line in f:
                    if line.startswith('#') or not line.strip():
                        continue
                    values = line.split()
                    if not values:
                        continue
                    
                    if values[0] == 'v':
                        vertices.append([float(v) for v in values[1:4]])
                    elif values[0] == 'vt':
                        texcoords.append([float(v) for v in values[1:3]])
                    elif values[0] == 'vn':
                        normals.append([float(v) for v in values[1:4]])
                    elif values[0] == 'f':
                        face = []
                        for v in values[1:]:
                            w = v.split('/')
                            # OBJ indices are 1-based
                            vert_index = int(w[0]) - 1
                            tex_index = int(w[1]) - 1 if len(w) > 1 and w[1] else -1
                            norm_index = int(w[2]) - 1 if len(w) > 2 and w[2] else -1
                            face.append((vert_index, tex_index, norm_index))
                        faces.append(face)
            return vertices, texcoords, normals, faces
        except Exception as e:
            print(f"Error loading OBJ {filepath}: {e}")
            return None

    @staticmethod
    def load_texture(texture_path):
        """Loads an image file into an OpenGL texture ID."""
        if not os.path.exists(texture_path):
            return None
        
        try:
            texture_surface = pygame.image.load(texture_path)
            texture_data = pygame.image.tostring(texture_surface, "RGBA", True)
            width = texture_surface.get_width()
            height = texture_surface.get_height()

            tex_id = glGenTextures(1)
            glBindTexture(GL_TEXTURE_2D, tex_id)
            glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, width, height, 0, GL_RGBA, GL_UNSIGNED_BYTE, texture_data)

            glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
            glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
            
            return tex_id
        except Exception as e:
            print(f"Error loading texture {texture_path}: {e}")
            return None
