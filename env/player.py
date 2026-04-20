"""
FileExplorer3D - player.py
Contains the Player class, which handles interaction events and contains a Camera object.
"""

import pygame
from pygame.locals import *
from env.camera import Camera
from utils.camera_animation_stack import CameraAnimation, CameraAnimationStack

class Player:
    """Manages player camera and input handling."""

    NAVIGATION_DURATION = 0.5   # seconds for folder-enter transitions

    def __init__(self, config, fullscreen_toggle=None):
        self.config = config
        self.camera = Camera()
        self.fullscreen_toggle = fullscreen_toggle
        self.animation_stack = CameraAnimationStack()

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
                if not pygame.mouse.get_visible() and not self.animation_stack.is_animating():
                    sensitivity = self.config.get("mouse_sensitivity", 1.0) * 0.1
                    mx, my = event.rel
                    self.camera.yaw += mx * sensitivity
                    self.camera.pitch -= my * sensitivity
                    self.camera.pitch = max(-89.999, min(89.999, self.camera.pitch))

        return True

    def reset_camera(self, num_objects, cols, spacing):
        """Reset camera to an overview position for the current grid."""
        self.camera.reset_to_overview(num_objects, cols, spacing)

    def start_navigation_animation(self, num_objects, cols, spacing,
                                   duration=NAVIGATION_DURATION):
        """
        Push a smooth camera transition to the overview position for the
        new directory. Clears any in-progress animation first so user intent
        always takes priority. O(1).
        """
        end_pos = Camera.overview_position(num_objects, cols, spacing)
        anim = CameraAnimation(
            start_position=(self.camera.x, self.camera.y, self.camera.z),
            end_position=end_pos,
            start_yaw=self.camera.yaw,
            start_pitch=self.camera.pitch,
            end_yaw=0.0,
            end_pitch=-25.0,
            duration=duration,
        )
        self.animation_stack.clear()
        self.animation_stack.push(anim)

    def update(self, dt):
        # Advance any active animation and apply its state to the camera.
        result = self.animation_stack.update(dt)
        if result is not None:
            pos, yaw, pitch = result
            self.camera.x, self.camera.y, self.camera.z = pos
            self.camera.yaw = yaw
            self.camera.pitch = pitch

        if not pygame.mouse.get_visible():
            cx = pygame.display.get_surface().get_width() // 2
            cy = pygame.display.get_surface().get_height() // 2

            if not self.animation_stack.is_animating():
                keys = pygame.key.get_pressed()
                speed = self.config.get("move_speed", 5.0) * dt
                ctrl_held = pygame.key.get_mods() & (KMOD_CTRL | KMOD_META)

                forward = (keys[K_w] - keys[K_s])
                right = (int(keys[K_d] and not ctrl_held) - keys[K_a])
                up = (keys[K_SPACE] - keys[K_LSHIFT])

                if forward or right:
                    self.camera.move(forward * speed, right * speed)
                if up:
                    self.camera.y += up * speed

            # Keep cursor centred so mouse-look has no jump when control returns.
            pygame.mouse.set_pos(cx, cy)

    def apply_look(self):
        """Apply camera view to OpenGL."""
        self.camera.apply_look()
