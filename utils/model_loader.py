import os
import pygame
from OpenGL.GL import *
import numpy as np

class ModelLoader:
    """Parses .obj files and manages texture loading."""
    
    @staticmethod
    def load_obj(filepath):
        """
        Robust OBJ parser with proper face triangulation and negative index handling.
        Returns vertices, texcoords, normals, and face indices.
        """
        vertices = []
        texcoords = []
        normals = []
        faces = []

        try:
            with open(filepath, 'r') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if line.startswith('#') or not line:
                        continue
                    
                    # Handle line continuations (backslash at end)
                    while line.endswith('\\'):
                        line = line[:-1] + next(f).strip()
                    
                    values = line.split()
                    if not values:
                        continue
                    
                    try:
                        if values[0] == 'v':
                            # Vertex position (x, y, z, [w])
                            vertices.append([float(v) for v in values[1:4]])
                        
                        elif values[0] == 'vt':
                            # Texture coordinate (u, v, [w])
                            texcoords.append([float(v) for v in values[1:3]])
                        
                        elif values[0] == 'vn':
                            # Vertex normal (x, y, z)
                            normals.append([float(v) for v in values[1:4]])
                        
                        elif values[0] == 'f':
                            # Face definition
                            face_verts = []
                            
                            for v in values[1:]:
                                # Split by '/' to get vertex/texture/normal indices
                                parts = v.split('/')
                                
                                # Parse vertex index (required)
                                if parts[0]:
                                    v_idx = int(parts[0])
                                    # Handle negative indices (relative to end of list)
                                    if v_idx < 0:
                                        v_idx = len(vertices) + v_idx
                                    else:
                                        v_idx = v_idx - 1  # Convert from 1-based to 0-based
                                else:
                                    continue  # Skip invalid vertex
                                
                                # Parse texture coordinate index (optional)
                                t_idx = -1
                                if len(parts) > 1 and parts[1]:
                                    t_idx = int(parts[1])
                                    if t_idx < 0:
                                        t_idx = len(texcoords) + t_idx
                                    else:
                                        t_idx = t_idx - 1
                                
                                # Parse normal index (optional)
                                n_idx = -1
                                if len(parts) > 2 and parts[2]:
                                    n_idx = int(parts[2])
                                    if n_idx < 0:
                                        n_idx = len(normals) + n_idx
                                    else:
                                        n_idx = n_idx - 1
                                
                                face_verts.append((v_idx, t_idx, n_idx))
                            
                            # Triangulate face using fan triangulation
                            if len(face_verts) >= 3:
                                for i in range(1, len(face_verts) - 1):
                                    faces.append([
                                        face_verts[0],
                                        face_verts[i],
                                        face_verts[i + 1]
                                    ])
                            elif len(face_verts) > 0:
                                print(f"Warning: Face on line {line_num} has only {len(face_verts)} vertices")
                    
                    except (ValueError, IndexError) as e:
                        print(f"Error parsing line {line_num}: {line}")
                        print(f"  Error: {e}")
                        continue
            
            print(f"Loaded OBJ: {len(vertices)} vertices, {len(texcoords)} texcoords, {len(normals)} normals, {len(faces)} triangles")
            return vertices, texcoords, normals, faces
            
        except Exception as e:
            print(f"Error loading OBJ {filepath}: {e}")
            import traceback
            traceback.print_exc()
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

class TexturedModel:
    """An object representing an imported 3D model with a texture."""
    
    def __init__(self, vertices, texcoords, normals, faces, texture_id=None):
        self.vertices = vertices
        self.texcoords = texcoords
        self.normals = normals
        self.faces = faces
        self.texture_id = texture_id
        
        # Position/Rotation/Scale
        self.x, self.y, self.z = 0, 0, 0
        self.rx, self.ry, self.rz = 0, 0, 0
        self.sx, self.sy, self.sz = 1, 1, 1
        
        # Create a Display List for performance
        self.display_list = glGenLists(1)
        self._compile()

    def set_position(self, x, y, z):
        self.x, self.y, self.z = x, y, z

    def _compile(self):
        glNewList(self.display_list, GL_COMPILE)
        if self.texture_id:
            glEnable(GL_TEXTURE_2D)
            glBindTexture(GL_TEXTURE_2D, self.texture_id)
        
        glBegin(GL_TRIANGLES)
        for face in self.faces:
            for vertex_data in face:
                v_idx, t_idx, n_idx = vertex_data
                
                # Apply normal if available
                if n_idx != -1 and n_idx < len(self.normals):
                    glNormal3fv(self.normals[n_idx])
                
                # Apply texture coordinate if available
                if t_idx != -1 and t_idx < len(self.texcoords):
                    glTexCoord2fv(self.texcoords[t_idx])
                
                # Apply vertex position
                if v_idx < len(self.vertices):
                    glVertex3fv(self.vertices[v_idx])
        glEnd()
        
        if self.texture_id:
            glDisable(GL_TEXTURE_2D)
        glEndList()

    def draw(self):
        glCallList(self.display_list)