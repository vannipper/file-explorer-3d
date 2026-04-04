"""
FileExplorer3D - camera.py
Contains the Camera class, which helps the OpenGL render determine what gets drawn to the screen.
"""

# imports
import math
from OpenGL.GLU import gluLookAt

class Camera:
    def __init__(self, x=0.0, y=1.0, z=5.0, yaw=0.0, pitch=0.0, move_speed=1.0):
        self.x = x
        self.y = y
        self.z = z
        self.yaw = yaw      # left-right
        self.pitch = pitch  # up-down
        self.move_speed = move_speed

    def get_direction(self):
        # Convert yaw/pitch to a forward direction vector
        rad_yaw = math.radians(self.yaw)
        rad_pitch = math.radians(self.pitch)

        dx = math.cos(rad_pitch) * math.sin(rad_yaw)
        dy = math.sin(rad_pitch)
        dz = -math.cos(rad_pitch) * math.cos(rad_yaw)

        return dx, dy, dz

    def move(self, forward, right):
        """
        Move the camera based on forward/right distances (already scaled by dt).
        forward, right are distances to move, not just direction.
        """
        rad_yaw = math.radians(self.yaw)

        fx = math.sin(rad_yaw)
        fz = -math.cos(rad_yaw)

        rx = math.cos(rad_yaw)
        rz = math.sin(rad_yaw)

        self.x += fx * forward + rx * right
        self.z += fz * forward + rz * right

    def reset_to_overview(self, num_objects, cols, spacing):
        """Position camera to see the full grid of objects."""
        rows = max(1, math.ceil(num_objects / cols)) if num_objects > 0 else 1
        center_x = (min(num_objects, cols) - 1) * spacing / 2
        center_z = (rows - 1) * spacing / 2

        self.x = center_x
        self.y = max(3.0, rows * spacing * 0.5)
        self.z = center_z + max(5.0, rows * spacing)
        self.yaw = 0.0
        self.pitch = -25.0

    def apply_look(self):
        dx, dy, dz = self.get_direction()
        eye = (self.x, self.y, self.z)
        center = (self.x + dx, self.y + dy, self.z + dz)
        up = (0.0, 1.0, 0.0)
        gluLookAt(*eye, *center, *up)
