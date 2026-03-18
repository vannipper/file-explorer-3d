"""
FileExplorer3D - player.py
Contains the Player class, which handles interaction events and contains a Camera object.
"""

import pygame
from pygame.locals import *
from env.camera import Camera

class Player:
    """Manages player camera and input handling."""

    def __init__(self, config, fullscreen_toggle=None):
        self.config = config
        self.camera = Camera()
        self.fullscreen_toggle = fullscreen_toggle

    def position(self):
        return (self.camera.x, self.camera.y, self.camera.z)

    def handle_events(self, events):
        """Processes discrete events. Returns False if the app should quit."""
        if not events: return True

        for event in events:
            if event.type == QUIT:
                return False
            if event.type == KEYDOWN:
                if event.key == K_F11 and self.fullscreen_toggle:
                    self.fullscreen_toggle()
            if event.type == MOUSEMOTION:
                if not pygame.mouse.get_visible():
                    sensitivity = self.config.get("mouse_sensitivity", 1.0) * 0.1
                    mx, my = event.rel
                    self.camera.yaw += mx * sensitivity
                    self.camera.pitch -= my * sensitivity
                    self.camera.pitch = max(-89.999, min(89.999, self.camera.pitch))

        return True

    def update(self, dt):
        if not pygame.mouse.get_visible():
            keys = pygame.key.get_pressed()
            speed = self.config.get("move_speed", 5.0) * dt

            forward = (keys[K_w] - keys[K_s])
            right = (keys[K_d] - keys[K_a])
            up = (keys[K_SPACE] - keys[K_LSHIFT])

            if forward or right:
                self.camera.move(forward * speed, right * speed)
            if up:
                self.camera.y += up * speed

            cx = pygame.display.get_surface().get_width() // 2
            cy = pygame.display.get_surface().get_height() // 2
            pygame.mouse.set_pos(cx, cy)

    def apply_look(self):
        """Apply camera view to OpenGL."""
        self.camera.apply_look()
