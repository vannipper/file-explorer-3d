from OpenGL.GL import *

class TexturedModel:
    """An object representing an imported 3D model with a texture."""
    def __init__(self, vertices, texcoords, normals, faces, texture_id=None):
        self.vertices = vertices
        self.texcoords = texcoords
        self.normals = normals
        self.faces = faces
        self.texture_id = texture_id
        
        # Paths relative to project root (Crucial for serialization)
        self.rel_obj_path = None
        self.rel_tex_path = None
        
        self.x, self.y, self.z = 0, 0, 0
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
                if n_idx != -1: glNormal3fv(self.normals[n_idx])
                if t_idx != -1: glTexCoord2fv(self.texcoords[t_idx])
                glVertex3fv(self.vertices[v_idx])
        glEnd()
        
        if self.texture_id: glDisable(GL_TEXTURE_2D)
        glEndList()

    def draw(self):
        glCallList(self.display_list)