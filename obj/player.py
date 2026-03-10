import pygame
from pygame.locals import *
from obj.camera import Camera

class Player:
    """Manages player camera and input handling with Delta Time support."""

    def __init__(self, config=None, mouse_sensitivity=0.1, move_speed=5.0, fullscreen_toggle=None):
        self.config = config
        self.base_mouse_sensitivity = mouse_sensitivity
        # Speed is units per second
        self.base_move_speed = move_speed 
        self.camera = Camera(move_speed=1.0)  # Set to 1.0, we'll handle scaling in update()
        self.mouse_sensitivity = self.base_mouse_sensitivity
        self.fullscreen_toggle = fullscreen_toggle
        
        # Vertical speed is same as horizontal now
        self.vertical_speed_mult = 1.0

    def position(self):
        return (self.camera.x, self.camera.y, self.camera.z)

    def handle_input(self, events):
        """Processes discrete events (mouse motion, quitting)."""
        if self.config:
            ms_mult = self.config.get("mouse_sensitivity", 1.0)
            mv_mult = self.config.get("move_speed", 1.0)
            self.mouse_sensitivity = self.base_mouse_sensitivity * float(ms_mult)
            self.base_move_speed = 5.0 * float(mv_mult)

        for event in events:
            if event.type == QUIT:
                return False
            
            if event.type == KEYDOWN:
                if event.key == K_F11 and self.fullscreen_toggle:
                    self.fullscreen_toggle()
            
            if event.type == MOUSEMOTION:
                mx, my = event.rel
                self.camera.yaw += mx * self.mouse_sensitivity
                self.camera.pitch -= my * self.mouse_sensitivity
                self.camera.pitch = max(-89.0, min(89.0, self.camera.pitch))
        
        return True

    def update(self, dt):
        """Update player movement scaled by delta time (dt)."""
        keys = pygame.key.get_pressed()
        
        forward = 0
        right = 0
        up = 0

        # Horizontal input
        if keys[K_w]: forward += 1
        if keys[K_s]: forward -= 1
        if keys[K_d]: right += 1
        if keys[K_a]: right -= 1
        
        # Vertical input
        if keys[K_SPACE]: up += 1
        if keys[K_LSHIFT]: up -= 1

        # Calculate distance based on dt and base move speed
        distance = self.base_move_speed * dt
        
        # Apply horizontal movement (camera.move already handles direction)
        if forward != 0 or right != 0:
            self.camera.move(forward * distance, right * distance)
            
        # Apply vertical movement (same speed as horizontal)
        if up != 0:
            self.camera.y += up * distance

    def apply_look(self):
        """Apply camera view to OpenGL."""
        self.camera.apply_look()