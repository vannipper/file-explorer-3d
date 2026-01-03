import os
import sys
import time
import pygame
import ctypes
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *

class EngineInitializer:
    """Sets up OS-specific requirements, the window, and OpenGL context."""
    
    VERSION = "Pre-Alpha 0.1"
    
    def __init__(self, config):
        self.config = config
        self.width = 0
        self.height = 0
        self.display_info = None
        self.splash_active = False
        self.splash_start_time = None
        self.splash_surface = None
        self.splash_image = None
        self.splash_size = (0, 0)
        self.world = None
        self.player = None
        self.menu_bar = None
        self.gizmo = None
        self.file_manager = None
        self.project_manager = None

    def show_splash(self, image_path):
        """Displays splash screen at native image size without blocking the loading process."""
        if sys.platform == "win32":
            try:
                myappid = 'zenith.engine.alpha.0.1' 
                ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
            except Exception:
                pass

        if not pygame.get_init():
            pygame.init()
            
        self.display_info = pygame.display.Info()

        try:
            if not os.path.exists(image_path):
                return

            self.splash_image = pygame.image.load(image_path)
            img_w, img_h = self.splash_image.get_size()
            self.splash_size = (img_w, img_h)
            
            # Position splash screen in center
            os.environ['SDL_VIDEO_WINDOW_POS'] = f"{(self.display_info.current_w - img_w) // 2},{(self.display_info.current_h - img_h) // 2}"
            
            # NOFRAME is key here for the splash
            self.splash_surface = pygame.display.set_mode((img_w, img_h), NOFRAME)
            
            # Set window caption and icon BEFORE displaying
            pygame.display.set_caption(f"Zenith Engine {self.VERSION} - Loading...")
            self._set_app_icon("zenith_ico_DRAFT.png")
            
            self.splash_surface.blit(self.splash_image, (0, 0))
            pygame.display.flip()
            pygame.event.pump()  # Process events to ensure display updates
            
            # Start timer AFTER image is displayed
            self.splash_active = True
            self.splash_start_time = time.time()
            print(f"Splash: image displayed, timer started at {self.splash_start_time}")
        except Exception as e:
            print(f"Initializer: Splash screen failed: {e}")

    def initialize_pygame(self):
        """Initialize Pygame and display info."""
        self.update_splash_status("Initializing Pygame...")
        pygame.init()
        self.display_info = pygame.display.Info()
        
    def initialize_engine_components(self, state):
        """Initialize all engine components (world, player, etc.)."""
        self.update_splash_status("Setting up world and systems...")
        
        # Import here to avoid circular dependencies
        from obj.world import World
        from obj.player import Player
        from ui.menuObj.menu_bar import MenuBar
        from editor.gizmo import Gizmo
        from utils.file_manager import FileManager
        from utils.project_manager import ProjectManager
        
        self.world = World(self.config)
        self.player = Player(self.config)
        self.menu_bar = MenuBar(self.config, pygame.font.Font(None, 24))
        self.gizmo = Gizmo()
        self.file_manager = FileManager()
        self.project_manager = ProjectManager(state, self.world, self.file_manager, self.config, self.VERSION)
        
        return self.world, self.player, self.menu_bar, self.gizmo, self.file_manager, self.project_manager

    def update_splash_status(self, status_text):
        """Update the splash screen with loading status text at the bottom."""
        if not self.splash_active or self.splash_surface is None:
            return
        
        try:
            # Redraw the original image
            self.splash_surface.blit(self.splash_image, (0, 0))
            
            # Create font for status text (small size)
            font = pygame.font.Font(None, 20)
            
            # Render status text with shadow for better visibility
            text_color = (200, 200, 200)
            shadow_color = (0, 0, 0)
            
            # Render shadow
            shadow_surface = font.render(status_text, True, shadow_color)
            shadow_rect = shadow_surface.get_rect()
            shadow_rect.centerx = self.splash_size[0] // 2 + 1
            shadow_rect.bottom = self.splash_size[1] - 9
            self.splash_surface.blit(shadow_surface, shadow_rect)
            
            # Render main text
            text_surface = font.render(status_text, True, text_color)
            text_rect = text_surface.get_rect()
            text_rect.centerx = self.splash_size[0] // 2
            text_rect.bottom = self.splash_size[1] - 10
            self.splash_surface.blit(text_surface, text_rect)
            
            pygame.display.flip()
            pygame.event.pump()  # Process events to keep window responsive
        except Exception as e:
            print(f"Error updating splash status: {e}")

    def setup_dimensions(self, width=None, height=None):
        """Calculates window size and prepares the environment."""
        if not self.display_info or self.display_info.current_w == -1:
            self.display_info = pygame.display.Info()
            
        # Get the full usable screen size (excludes taskbar on Windows/Linux)
        if sys.platform == "win32":
            # On Windows, get the work area (screen minus taskbar)
            try:
                import ctypes
                user32 = ctypes.windll.user32
                self.width = user32.GetSystemMetrics(0)  # SM_CXSCREEN
                self.height = user32.GetSystemMetrics(1)  # SM_CYSCREEN
            except:
                # Fallback to pygame info
                self.width = self.display_info.current_w
                self.height = self.display_info.current_h
        else:
            # For macOS/Linux, use full screen dimensions
            self.width = self.display_info.current_w
            self.height = self.display_info.current_h
            
        return self.width, self.height

    def finalize_engine_window(self):
        """Creates OpenGL window minimized so splash stays visible."""
        self.update_splash_status("Initializing OpenGL...")
        
        # Get display dimensions
        if not self.display_info or self.display_info.current_w == -1:
            self.display_info = pygame.display.Info()
        
        self.width = self.display_info.current_w
        self.height = self.display_info.current_h
        
        # Position at 0,0
        os.environ['SDL_VIDEO_WINDOW_POS'] = "0,0"
        
        # Create the OpenGL window
        pygame.display.set_mode((self.width, self.height), DOUBLEBUF | OPENGL | RESIZABLE)
        pygame.display.set_caption(f"Zenith Engine {self.VERSION}")
        
        # Immediately minimize it to keep splash visible
        if sys.platform == "win32":
            try:
                import ctypes
                hwnd = pygame.display.get_wm_info()['window']
                # SW_MINIMIZE = 6 (minimize but don't activate splash)
                # SW_HIDE = 0 (completely hide)
                ctypes.windll.user32.ShowWindow(hwnd, 0)  # Hide it completely
            except Exception as e:
                print(f"Could not hide window: {e}")
        
        self._set_app_icon("zenith_ico_DRAFT.png")
        self._setup_opengl()
        
        return self.width, self.height
    
    def create_opengl_window(self):
        """This method is no longer needed - kept for compatibility."""
        pass

    def load_last_project(self):
        """Load the last opened project if it exists."""
        last_path = self.config.get("last_project_path")
        
        if last_path and os.path.exists(last_path):
            # Show which project is loading
            project_name = os.path.basename(last_path)
            self.update_splash_status(f"Loading project: {project_name}...")
            
            # Load the project
            self.project_manager.process_action("open_project", auto_path=last_path)
            
            self.update_splash_status(f"Project loaded: {project_name}")
            return True
        else:
            self.project_manager.update_title()
            self.update_splash_status("Ready")
            return False

    def close_splash(self):
        """Ensure splash has been shown for at least 2 seconds, then show main window."""
        # Wait for minimum display time
        if self.splash_start_time:
            elapsed = time.time() - self.splash_start_time
            min_display_time = 2.0
            if elapsed < min_display_time:
                remaining = min_display_time - elapsed
                print(f"Splash: waiting {remaining:.2f} more seconds...")
                time.sleep(remaining)
            print(f"Splash: displayed for {time.time() - self.splash_start_time:.2f} seconds total")
        
        self.splash_active = False
        
        # Show and maximize the main window
        if sys.platform == "win32":
            try:
                import ctypes
                hwnd = pygame.display.get_wm_info()['window']
                # SW_MAXIMIZE = 3
                ctypes.windll.user32.ShowWindow(hwnd, 3)
                # Bring to front
                ctypes.windll.user32.SetForegroundWindow(hwnd)
            except Exception as e:
                print(f"Could not show/maximize window: {e}")
        else:
            # For non-Windows platforms
            pygame.display.set_mode((self.width, self.height), DOUBLEBUF | OPENGL | RESIZABLE)

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