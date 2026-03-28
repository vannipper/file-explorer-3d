"""
FileExplorer3D - selector.py
Contains the Selector class, which handles raycasting selection of objects.
Gizmo drawing and axis translation have been intentionally removed.
"""

import numpy as np
from utils.interaction_handler import InteractionHandler


class Selector:

    @staticmethod
    def pick_object(objects):
        """Raycast to find the clicked object."""
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

    def handle_selection(self, objects):
        """
        Raycast against all objects and return the one closest to the camera
        that the crosshair is aimed at, or None if nothing was hit.
        """
        mpos = InteractionHandler.GetMousePosition()
        ray_o, ray_d = InteractionHandler.GetRay(mpos[0], mpos[1])

        best, min_d = None, float('inf')
        for obj in objects:
            obj_pos = np.array([obj.x, obj.y, obj.z])
            dist = np.linalg.norm(np.cross(ray_d, ray_o - obj_pos))
            if dist < 0.6:
                depth = np.dot(ray_d, obj_pos - ray_o)
                if 0 < depth < min_d:
                    min_d, best = depth, obj
        return best

    def stop_drag(self):
        """Kept as a no-op so existing world.py calls don't break."""
        pass
