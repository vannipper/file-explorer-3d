import sys
import os
import pygame
import numpy as np
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *

# Existing engine imports
try:
    from config.config import Config
    from ui.menuObj.menu_bar import MenuBar
    from editor.gizmo import Gizmo
    from obj.player import Player
    from obj.rectangular_prism import RectangularPrism
    from obj.world import World
    from utils.file_manager import FileManager
    from initializer import EngineInitializer
    
    # New refactored component imports
    from editor.editor_state import EditorState
    from utils.project_manager import ProjectManager
    from utils.interaction_handler import InteractionHandler
except ImportError as e:
    print(f"Missing engine components: {e}")

class ZenithEngine:
    """Main Application Class."""
    def __init__(self):
        self.config = Config()
        self.state = EditorState()
        self.initializer = EngineInitializer(self.config)
        
        pygame.init()
        info = pygame.display.Info()
        self.win_w, self.win_h = self.initializer.start(
            width=int(info.current_w * 0.9), 
            height=int(info.current_h * 0.85)
        )
        
        self.world = World(self.config)
        self.player = Player(self.config)
        self.menu_bar = MenuBar(self.config, pygame.font.Font(None, 24))
        self.gizmo = Gizmo()
        self.file_manager = FileManager()
        self.project = ProjectManager(self.state, self.world, self.file_manager, self.config)
        
        self.setup_menus()
        self.load_last_project()

    def setup_menus(self):
        self.menu_bar.add_menu("File", [
            ("New Project (Ctrl+N)", "new_project"),
            ("Open (Ctrl+O)", "open_project"),
            ("Save (Ctrl+S)", "save_project"),
            ("Save As (Ctrl+Shift+S)", "save_as_project"),
            ("Exit", "exit")
        ])
        self.menu_bar.add_menu("Edit", [("Delete (Del)", "delete")])
        self.menu_bar.add_menu("Add", [("Primitive", None, [("Cube", "add_cube")])])

    def load_last_project(self):
        last_path = self.config.get("last_project_path")
        if last_path and os.path.exists(last_path):
            self.project.process_action("open_project", auto_path=last_path)
        else:
            self.project.update_title()

    def run(self):
        clock = pygame.time.Clock()
        while self.state.running:
            # dt is the time in seconds since the last frame
            dt = clock.tick(60) / 1000.0 
            self.handle_events()
            self.update(dt)
            self.render()
        pygame.quit()
        sys.exit()

    def handle_events(self):
        events = pygame.event.get()
        m_pos = pygame.mouse.get_pos()
        mods = pygame.key.get_mods()
        ctrl = mods & KMOD_CTRL or mods & KMOD_META
        shift = mods & KMOD_SHIFT

        # Handle discrete player events (Mouse rotation, Fullscreen toggle)
        if not self.state.editor_mode:
            # player.handle_input now returns a boolean
            if self.player.handle_input(events) is False:
                self.state.running = False

        for ev in events:
            if ev.type == QUIT:
                self.project.process_action("exit")
            elif ev.type == VIDEORESIZE:
                pygame.display.set_mode(ev.size, DOUBLEBUF | OPENGL | RESIZABLE)
                self.win_w, self.win_h = ev.size
            elif ev.type == KEYDOWN:
                if ev.key in [K_F1, K_TAB]:
                    self.toggle_editor()
                elif ev.key == K_ESCAPE:
                    self.state.selected_obj = None
                    self.gizmo.stop_drag()
                
                # Shortcuts
                if ctrl:
                    if ev.key == K_s:
                        action = "save_as_project" if shift else "save_project"
                        if self.project.process_action(action): self.state.editor_mode = True
                    elif ev.key == K_o:
                        if self.project.process_action("open_project"): self.state.editor_mode = True
                    elif ev.key == K_n:
                        if self.project.process_action("new_project"): self.state.editor_mode = True
                elif ev.key == K_DELETE and self.state.editor_mode:
                    self.project.process_action("delete")

            if self.state.editor_mode:
                if ev.type == MOUSEBUTTONDOWN and ev.button == 1:
                    if not InteractionHandler.is_mouse_in_ui(self.menu_bar, m_pos):
                        self.handle_selection(m_pos)
                elif ev.type == MOUSEBUTTONUP and ev.button == 1:
                    self.gizmo.stop_drag()

        # Handle UI actions from MenuBar
        if self.state.editor_mode:
            self.menu_bar.update_layout(self.win_w)
            ui_action = self.menu_bar.handle_input(events)
            if ui_action:
                if self.project.process_action(ui_action):
                    self.state.editor_mode = True

    def toggle_editor(self):
        self.state.editor_mode = not self.state.editor_mode
        pygame.event.set_grab(not self.state.editor_mode)
        pygame.mouse.set_visible(self.state.editor_mode)
        self.state.selected_obj = None
        self.gizmo.stop_drag()

    def handle_selection(self, m_pos):
        ray_o, ray_d = InteractionHandler.get_ray(m_pos[0], m_pos[1])
        hit_gizmo = False
        if self.state.selected_obj:
            obj_pos = np.array([self.state.selected_obj.x, self.state.selected_obj.y, self.state.selected_obj.z])
            axis = self.gizmo.check_hover(ray_o, ray_d, obj_pos)
            if axis is not None:
                self.gizmo.start_drag(axis, ray_o, ray_d, obj_pos)
                hit_gizmo = True
        
        if not hit_gizmo:
            best, min_d = None, float('inf')
            for obj in self.world.objects:
                dist = np.linalg.norm(np.cross(ray_d, ray_o - np.array([obj.x, obj.y, obj.z])))
                if dist < 0.3:
                    depth = np.dot(np.array([obj.x, obj.y, obj.z]) - ray_o, ray_d)
                    if 0 < depth < min_d: min_d, best = depth, obj
            self.state.selected_obj = best

    def update(self, dt):
        if self.state.editor_mode:
            if self.gizmo.active_axis is not None and self.state.selected_obj:
                m_pos = pygame.mouse.get_pos()
                ray_o, ray_d = InteractionHandler.get_ray(m_pos[0], m_pos[1])
                new_pos = self.gizmo.update_drag(ray_o, ray_d)
                if new_pos is not None:
                    self.state.selected_obj.set_position(*new_pos)
                    self.state.has_unsaved_changes = True
                    self.project.update_title()
        else:
            # Keyboard state is now polled inside Player.update(dt)
            self.player.update(dt)

    def render(self):
        glViewport(0, 0, self.win_w, self.win_h)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glEnable(GL_DEPTH_TEST)
        
        glEnable(GL_LIGHTING); glEnable(GL_LIGHT0); glEnable(GL_COLOR_MATERIAL)
        glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)
        glLightfv(GL_LIGHT0, GL_POSITION, [5, 10, 5, 1])
        
        glMatrixMode(GL_PROJECTION); glLoadIdentity()
        aspect = self.win_w/self.win_h if self.win_h > 0 else 1
        gluPerspective(self.player.config.get("fov", 70), aspect, 0.1, 100.0)
        glMatrixMode(GL_MODELVIEW); glLoadIdentity()
        self.player.apply_look()

        self.world.draw_floor()
        self.world.draw_axes()
        
        for obj in self.world.objects:
            glPushMatrix()
            glTranslatef(obj.x, obj.y, obj.z)
            if obj == self.state.selected_obj:
                glPushAttrib(GL_LIGHTING_BIT)
                glMaterialfv(GL_FRONT, GL_EMISSION, [0.0, 0.2, 0.0, 1.0])
                glColor3f(0.4, 1.0, 0.4)
                obj.draw()
                glPopAttrib()
            else:
                glColor3f(0.7, 0.7, 0.7)
                obj.draw()
            glPopMatrix()

        if self.state.selected_obj:
            self.gizmo.draw(np.array([self.state.selected_obj.x, self.state.selected_obj.y, self.state.selected_obj.z]))
            
        glDisable(GL_LIGHTING); glDisable(GL_DEPTH_TEST)
        if self.state.editor_mode:
            self.menu_bar.draw(self.win_w, self.win_h)
        pygame.display.flip()

if __name__ == "__main__":
    engine = ZenithEngine()
    engine.run()