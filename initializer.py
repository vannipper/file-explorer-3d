import os
import sys
import time
import pygame
import ctypes
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *

class EngineInitializer:
    def __init__(self, config):
        self.config = config
        self.width = 0
        self.height = 0
        self.display_info = None

    def start(self, width=None, height=None):
        """Main entry point for engine initialization."""
        # Fix for Windows Taskbar Icon (AppUserModelID)
        if sys.platform == "win32":
            try:
                myappid = 'zenith.engine.alpha.0.1' 
                ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
            except Exception:
                pass

        if not pygame.get_init():
            pygame.init()
            
        self.display_info = pygame.display.Info()
        
        # 1. Run Splash Screen
        self._show_splash_screen("zenith_DRAFT.jpg")
        
        # 2. Setup Main Window Dimensions
        # Priority: Passed Arguments -> Config -> Calculation (80% of screen)
        if width and height:
            self.width = width
            self.height = height
        else:
            self.width = max(640, int(self.display_info.current_w * 0.8))
            self.height = max(480, int(self.display_info.current_h * 0.8))
        
        # Center the main window
        os.environ['SDL_VIDEO_WINDOW_POS'] = f"{(self.display_info.current_w - self.width) // 2},{(self.display_info.current_h - self.height) // 2}"
        
        # 3. Create Main Display (With borders and resizable)
        pygame.display.set_mode((self.width, self.height), DOUBLEBUF | OPENGL | RESIZABLE)
        pygame.display.set_caption("Zenith Engine")
        
        # 4. Set App Icon
        self._set_app_icon("zenith_ico_DRAFT.png")
        
        # 5. Setup OpenGL Defaults
        self._setup_opengl()
        
        return self.width, self.height

    def _show_splash_screen(self, image_path):
        """Displays splash screen at native image size and then cleans up."""
        try:
            logo = pygame.image.load(image_path)
            img_w, img_h = logo.get_size()
            
            # Position splash screen in center
            os.environ['SDL_VIDEO_WINDOW_POS'] = f"{(self.display_info.current_w - img_w) // 2},{(self.display_info.current_h - img_h) // 2}"
            
            splash_surf = pygame.display.set_mode((img_w, img_h), NOFRAME)
            splash_surf.blit(logo, (0, 0))
            pygame.display.flip()
            
            time.sleep(2.0)
            
            # Reset video for the main window transition
            pygame.display.quit()
            pygame.display.init()
        except Exception as e:
            print(f"Initializer: Splash screen failed: {e}")
            if not pygame.get_init():
                pygame.display.init()

    def _set_app_icon(self, icon_path):
        """Sets the window icon after the display mode is established."""
        try:
            if os.path.exists(icon_path):
                icon_surface = pygame.image.load(icon_path)
                pygame.display.set_icon(icon_surface)
        except Exception as e:
            print(f"Initializer: Icon load failed: {e}")

    def _setup_opengl(self):
        """Sets up the initial OpenGL state."""
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glEnable(GL_DEPTH_TEST)
        glClearColor(0.1, 0.1, 0.15, 1.0)