import pygame
from pygame.locals import *
from obj.camera import Camera


class Player:
    """Manages player camera and input handling."""

    def __init__(self, config=None, mouse_sensitivity=0.1, move_speed=0.1, fullscreen_toggle=None):
        self.config = config
        self.base_mouse_sensitivity = mouse_sensitivity
        self.base_move_speed = move_speed
        self.camera = Camera(move_speed=self.base_move_speed)
        self.mouse_sensitivity = self.base_mouse_sensitivity
        self.fullscreen_toggle = fullscreen_toggle

    def position(self, camera):
        return (camera.x, camera.y, camera.z)

    def handle_input(self, events, menu=None):
        """
        Process keyboard and mouse input.
        Returns forward and right movement values, or (None, None) if should quit.
        """
        forward = 0
        right = 0

        # use live values from config if provided: treat as multipliers (100% = 1.0)
        if self.config:
            ms_mult = self.config.get("mouse_sensitivity", 1.0)
            mv_mult = self.config.get("move_speed", 1.0)
            # compute effective sensitivity and camera move speed
            self.mouse_sensitivity = self.base_mouse_sensitivity * float(ms_mult)
            self.camera.move_speed = self.base_move_speed * float(mv_mult)

        for event in events:
            if event.type == QUIT:
                return None, None
            if event.type == KEYDOWN:
                if event.key == K_ESCAPE:
                    if menu:
                        menu.toggle()
                    else:
                        return None, None
                if event.key == K_F11:
                    # toggle fullscreen immediately
                    if self.fullscreen_toggle:
                        self.fullscreen_toggle()
            if event.type == MOUSEMOTION:
                # update camera rotation only when menu is not active
                if not (menu and getattr(menu, "active", False)):
                    mx, my = event.rel
                    self.camera.yaw += mx * self.mouse_sensitivity
                    self.camera.pitch -= my * self.mouse_sensitivity
                    # Clamp pitch
                    self.camera.pitch = max(-89.0, min(89.0, self.camera.pitch))

        keys = pygame.key.get_pressed()
        if keys[K_w]:
            forward += 1
        if keys[K_s]:
            forward -= 1
        if keys[K_d]:
            right += 1
        if keys[K_a]:
            right -= 1

        return forward, right

    def update(self, forward, right):
        """Update player camera position based on movement."""
        self.camera.move(forward, right)

    def apply_look(self):
        """Apply camera view to OpenGL."""
        self.camera.apply_look()
