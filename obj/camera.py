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

        # Forward vector in XZ plane
        fx = math.sin(rad_yaw)
        fz = -math.cos(rad_yaw)

        # Right vector in XZ plane
        rx = math.cos(rad_yaw)
        rz = math.sin(rad_yaw)

        # Apply movement (no additional move_speed multiplier needed)
        self.x += fx * forward + rx * right
        self.z += fz * forward + rz * right

    def apply_look(self):
        # Position the camera using gluLookAt
        dx, dy, dz = self.get_direction()
        eye = (self.x, self.y, self.z)
        center = (self.x + dx, self.y + dy, self.z + dz)
        up = (0.0, 1.0, 0.0)
        gluLookAt(*eye, *center, *up)