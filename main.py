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
    from obj.world import World
    from obj.textured_model import TexturedModel
    from utils.file_manager import FileManager
    from initializer import EngineInitializer
    from editor.editor_state import EditorState
    from utils.project_manager import ProjectManager
    from utils.interaction_handler import InteractionHandler
    from utils.model_loader import ModelLoader
except ImportError as e:
    print(f"Missing engine components: {e}")

def setup_menus(menu_bar):
    """Configures the top menu bar items."""
    menu_bar.add_menu("File", [
        ("New Project (Ctrl+N)", "new_project"),
        ("Open (Ctrl+O)", "open_project"),
        ("Save (Ctrl+S)", "save_project"),
        ("Save As (Ctrl+Shift+S)", "save_as_project"),
        ("Exit", "exit")
    ])
    menu_bar.add_menu("Edit", [("Delete (Del)", "delete")])
    menu_bar.add_menu("Add", [
        ("Primitive", None, [("Cube", "add_cube")]),
        ("External", None, [("Import .OBJ", "import_model")])
    ])

def handle_selection(state, world, gizmo, m_pos):
    """Performs raycasting to select objects in the scene."""
    ray_o, ray_d = InteractionHandler.get_ray(m_pos[0], m_pos[1])
    hit_gizmo = False
    
    if state.selected_obj:
        obj_pos = np.array([state.selected_obj.x, state.selected_obj.y, state.selected_obj.z])
        axis = gizmo.check_hover(ray_o, ray_d, obj_pos)
        if axis is not None:
            gizmo.start_drag(axis, ray_o, ray_d, obj_pos)
            hit_gizmo = True
    
    if not hit_gizmo:
        best, min_d = None, float('inf')
        for obj in world.objects:
            dist = np.linalg.norm(np.cross(ray_d, ray_o - np.array([obj.x, obj.y, obj.z])))
            if dist < 0.5:
                depth = np.dot(np.array([obj.x, obj.y, obj.z]) - ray_o, ray_d)
                if 0 < depth < min_d: min_d, best = depth, obj
        state.selected_obj = best

def render_scene(win_w, win_h, state, world, player, gizmo, menu_bar):
    """Main rendering pipeline."""
    glViewport(0, 0, win_w, win_h)
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glEnable(GL_DEPTH_TEST)
    
    glEnable(GL_LIGHTING); glEnable(GL_LIGHT0); glEnable(GL_COLOR_MATERIAL)
    glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)
    glLightfv(GL_LIGHT0, GL_POSITION, [5, 10, 5, 1])
    
    glMatrixMode(GL_PROJECTION); glLoadIdentity()
    aspect = win_w / win_h if win_h > 0 else 1
    gluPerspective(player.config.get("fov", 70), aspect, 0.1, 1000.0)
    glMatrixMode(GL_MODELVIEW); glLoadIdentity()
    player.apply_look()

    world.draw_floor()
    world.draw_axes()
    
    for obj in world.objects:
        glPushMatrix()
        glTranslatef(obj.x, obj.y, obj.z)
        
        if obj == state.selected_obj:
            glPushAttrib(GL_LIGHTING_BIT)
            glMaterialfv(GL_FRONT, GL_EMISSION, [0.0, 0.2, 0.0, 1.0])
            glColor3f(0.4, 1.0, 0.4)
            obj.draw()
            glPopAttrib()
        else:
            glMaterialfv(GL_FRONT, GL_EMISSION, [0.0, 0.0, 0.0, 1.0])
            if isinstance(obj, TexturedModel):
                glColor3f(1.0, 1.0, 1.0)
            else:
                glColor3f(0.7, 0.7, 0.7)
            obj.draw()
        glPopMatrix()

    if state.selected_obj:
        gizmo.draw(np.array([state.selected_obj.x, state.selected_obj.y, state.selected_obj.z]))
        glColor3f(1.0, 1.0, 1.0)
        
    glDisable(GL_LIGHTING); glDisable(GL_DEPTH_TEST)
    if state.editor_mode:
        menu_bar.draw(win_w, win_h)
    pygame.display.flip()

def handle_model_import(world, file_manager, state, project):
    """Logic for importing an OBJ model and optional texture."""
    obj_path = file_manager.open_file_dialog(
        title="Import 3D Model", 
        file_types=[("OBJ Files", "*.obj"), ("All Files", "*.*")]
    )
    if not obj_path:
        return False
        
    data = ModelLoader.load_obj(obj_path)
    if data:
        tex_path = file_manager.open_file_dialog(
            title="Select Texture (Optional)", 
            file_types=[("Image Files", "*.png;*.jpg;*.jpeg;*.bmp"), ("All Files", "*.*")]
        )
        tex_id = ModelLoader.load_texture(tex_path) if tex_path else None
        
        v, t, n, f = data
        model = TexturedModel(v, t, n, f, tex_id)
        model.set_position(0, 0, 0)
        
        world.add_object(model)
        state.has_unsaved_changes = True
        project.update_title()
        return True
    return False

if __name__ == "__main__":
    config = Config()
    state = EditorState()
    initializer = EngineInitializer(config)
    
    pygame.init()
    info = pygame.display.Info()
    win_w, win_h = initializer.start(
        width=int(info.current_w * 0.9), 
        height=int(info.current_h * 0.85)
    )
    
    world = World(config)
    player = Player(config)
    menu_bar = MenuBar(config, pygame.font.Font(None, 24))
    gizmo = Gizmo()
    file_manager = FileManager()
    project = ProjectManager(state, world, file_manager, config)
    
    setup_menus(menu_bar)
    
    last_path = config.get("last_project_path")
    if last_path and os.path.exists(last_path):
        project.process_action("open_project", auto_path=last_path)
    else:
        project.update_title()

    clock = pygame.time.Clock()
    
    while state.running:
        dt = clock.tick(60) / 1000.0 
        events = pygame.event.get()
        m_pos = pygame.mouse.get_pos()
        mods = pygame.key.get_mods()
        ctrl = mods & (KMOD_CTRL | KMOD_META)
        shift = mods & KMOD_SHIFT

        if not state.editor_mode:
            if player.handle_input(events) is False:
                state.running = False

        for ev in events:
            if ev.type == QUIT:
                project.process_action("exit")
            elif ev.type == VIDEORESIZE:
                pygame.display.set_mode(ev.size, DOUBLEBUF | OPENGL | RESIZABLE)
                win_w, win_h = ev.size
            elif ev.type == KEYDOWN:
                if ev.key in [K_F1, K_TAB]:
                    state.editor_mode = not state.editor_mode
                    pygame.event.set_grab(not state.editor_mode)
                    pygame.mouse.set_visible(state.editor_mode)
                    state.selected_obj = None
                    gizmo.stop_drag()
                elif ev.key == K_ESCAPE:
                    state.selected_obj = None
                    gizmo.stop_drag()
                
                if ctrl:
                    if ev.key == K_s:
                        action = "save_as_project" if shift else "save_project"
                        if project.process_action(action): state.editor_mode = True
                    elif ev.key == K_o:
                        if project.process_action("open_project"): state.editor_mode = True
                    elif ev.key == K_n:
                        if project.process_action("new_project"): state.editor_mode = True
                elif ev.key == K_DELETE and state.editor_mode:
                    project.process_action("delete")

            if state.editor_mode:
                if ev.type == MOUSEBUTTONDOWN and ev.button == 1:
                    if not InteractionHandler.is_mouse_in_ui(menu_bar, m_pos):
                        handle_selection(state, world, gizmo, m_pos)
                elif ev.type == MOUSEBUTTONUP and ev.button == 1:
                    gizmo.stop_drag()

        if state.editor_mode:
            menu_bar.update_layout(win_w)
            ui_action = menu_bar.handle_input(events)
            
            if ui_action == "import_model":
                handle_model_import(world, file_manager, state, project)
            elif ui_action and project.process_action(ui_action):
                state.editor_mode = True
            
            if gizmo.active_axis is not None and state.selected_obj:
                ray_o, ray_d = InteractionHandler.get_ray(m_pos[0], m_pos[1])
                new_pos = gizmo.update_drag(ray_o, ray_d)
                if new_pos is not None:
                    state.selected_obj.set_position(*new_pos)
                    state.has_unsaved_changes = True
                    project.update_title()
        else:
            player.update(dt)

        render_scene(win_w, win_h, state, world, player, gizmo, menu_bar)

    pygame.quit()