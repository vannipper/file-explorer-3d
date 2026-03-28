"""
FileExplorer3D - selector.py (NAME WIP)
Contains the Selector class, which handles the selection of on-screen objects.
"""

# imports
import numpy as np
from OpenGL.GL import *

from utils.interaction_handler import InteractionHandler

class Selector:
    """A 3D transformation gizmo for translating objects."""
    def __init__(self):
        self.axis_length = 0.75
        self.threshold = 0.3 # distance threshold
        self.active_axis = None # 0:X, 1:Y, 2:Z
        self.drag_start_pos = None
        self.drag_start_obj_pos = None
        self.axes_vectors = [
            np.array([1, 0, 0]),
            np.array([0, 1, 0]),
            np.array([0, 0, 1])
        ]
        self.colors = [
            (1, 0, 0), # X: Red
            (0, 1, 0), # Y: Green
            (0, 0, 1)  # Z: Blue
        ]

    def draw(self, obj_pos):
        """Draws the gizmo at the object's position."""
        glDisable(GL_LIGHTING)
        glLineWidth(3.0)
        glBegin(GL_LINES)
        for i in range(3):
            color = self.colors[i]
            if self.active_axis == i:
                glColor3f(1.0, 1.0, 0.0) # highlight
            else:
                glColor3f(*color)
            
            glVertex3f(*obj_pos)
            glVertex3f(*(obj_pos + self.axes_vectors[i] * self.axis_length))
        glEnd()
        glLineWidth(1.0)
        glEnable(GL_LIGHTING)

    @staticmethod
    def pick_object(objects):
        """Raycast to find the clicked object, ignoring gizmo axes."""
        mpos = InteractionHandler.GetMousePosition()
        ray_o, ray_d = InteractionHandler.GetRay(mpos[0], mpos[1])
        best, min_d = None, float('inf')
        for obj in objects:
            dist = np.linalg.norm(np.cross(ray_d, ray_o - np.array([obj.x, obj.y, obj.z])))
            if dist < 0.6:
                depth = np.dot(ray_d, np.array([obj.x, obj.y, obj.z]) - ray_o)
                if 0 < depth < min_d:
                    min_d, best = depth, obj
        return best

    def handle_selection(self, objects, selected_object):
        """Performs raycasting to select objects in the scene."""
        mpos = InteractionHandler.GetMousePosition()
        ray_o, ray_d = InteractionHandler.GetRay(mpos[0], mpos[1])
        hit_selector = False
        
        if selected_object:
            obj_pos = np.array([selected_object.x, selected_object.y, selected_object.z])
            axis = self.check_hover(ray_o, ray_d, obj_pos)
            if axis is not None:
                self.start_drag(axis, ray_o, ray_d, obj_pos)
                hit_selector = True
        
        if not hit_selector:
            best, min_d = None, float('inf')
            for obj in objects:
                dist = np.linalg.norm(np.cross(ray_d, ray_o - np.array([obj.x, obj.y, obj.z])))
                if dist < 0.6: 
                    depth = np.dot(ray_d, np.array([obj.x, obj.y, obj.z]) - ray_o)
                    if 0 < depth < min_d: 
                        min_d, best = depth, obj
            selected_object = best

        return selected_object

    def check_hover(self, ray_o, ray_d, obj_pos):
        """Returns the axis index if the ray is near a gizmo handle, else None."""
        best_axis = None
        min_dist = self.threshold
        
        for i in range(3):
            u = self.axes_vectors[i]  # Axis direction
            v = ray_d                 # Ray direction
            w = obj_pos - ray_o       # Vector from ray origin to axis origin
            
            a = np.dot(u, u)
            b = np.dot(u, v)
            c = np.dot(v, v)
            d = np.dot(u, w)
            e = np.dot(v, w)
            
            denom = a * c - b * b
            
            # parallel lines
            if abs(denom) < 1e-7:
                continue
            
            t = (b * e - c * d) / denom
            s = (a * e - b * d) / denom
            
            if s > 0 and 0 <= t <= self.axis_length:
                closest_on_axis = obj_pos + u * t
                closest_on_ray = ray_o + v * s
                dist = np.linalg.norm(closest_on_axis - closest_on_ray)
                
                if dist < min_dist:
                    min_dist = dist
                    best_axis = i
                    
        return best_axis

    def start_drag(self, axis_idx, ray_o, ray_d, obj_pos):
        self.active_axis = axis_idx
        self.drag_start_obj_pos = np.copy(obj_pos)
        
        u = self.axes_vectors[axis_idx]
        v = ray_d
        w = obj_pos - ray_o
        
        a = np.dot(u, u)
        b = np.dot(u, v)
        c = np.dot(v, v)
        d = np.dot(u, w)
        e = np.dot(v, w)
        
        denom = a * c - b * b
        if abs(denom) > 1e-7:
            self.drag_start_pos = (b * e - c * d) / denom
        else:
            self.drag_start_pos = 0

    def update_drag(self, ray_o, ray_d):
        if self.active_axis is None: return None
        
        u = self.axes_vectors[self.active_axis]
        v = ray_d
        obj_pos = self.drag_start_obj_pos
        w = obj_pos - ray_o
        
        a = np.dot(u, u)
        b = np.dot(u, v)
        c = np.dot(v, v)
        d = np.dot(u, w)
        e = np.dot(v, w)
        
        denom = a * c - b * b
        if abs(denom) < 1e-7: return None
        
        current_t = (b * e - c * d) / denom
        delta = current_t - self.drag_start_pos
        
        return self.drag_start_obj_pos + u * delta

    def stop_drag(self):
        self.active_axis = None
        self.drag_start_pos = None
        self.drag_start_obj_pos = None
