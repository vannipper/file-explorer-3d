"""
FileExplorer3D - main.py
This is the main file which contains all module calls and the main loop.
"""

# imports
import pygame
import numpy as np
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *

try:
    from config.config import Config
    from utils.file_manager import FileManager # TODO: implement loading a parent folder as the first action for this app
    from initializer import EngineInitializer
    from editor.editor_state import EditorState
    from utils.interaction_handler import InteractionHandler
except ImportError as e:
    print(f"Missing engine components: {e}")

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
            if dist < 0.6: 
                depth = np.dot(ray_d, np.array([obj.x, obj.y, obj.z]) - ray_o)
                if 0 < depth < min_d: 
                    min_d, best = depth, obj
        state.selected_obj = best

def render_scene(win_w, win_h, state, world, player, gizmo):
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
    
    # Draw objects
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
            obj.draw()
        glPopMatrix()

    world.draw_axes()

    if state.selected_obj:
        glDisable(GL_DEPTH_TEST)
        gizmo.draw(np.array([state.selected_obj.x, state.selected_obj.y, state.selected_obj.z]))
        glColor3f(1.0, 1.0, 1.0)
        glEnable(GL_DEPTH_TEST)
        
    glDisable(GL_LIGHTING); glDisable(GL_DEPTH_TEST)
    pygame.display.flip()

if __name__ == "__main__":
    config = Config()
    state = EditorState()
    initializer = EngineInitializer(config)
    
    # initialize Pygame
    initializer.initialize_pygame()
    pygame.event.set_grab(not state.editor_mode)
    pygame.mouse.set_visible(state.editor_mode)
    if state.editor_mode:
        pygame.key.start_text_input()
    else:
        pygame.key.stop_text_input()
    clock = pygame.time.Clock()

    # initialize engine components
    world, player, gizmo, file_manager, project = initializer.initialize_engine_components(state)
    
    # initialize OpenGL
    win_w, win_h = initializer.finalize_engine_window()
    
    # main loop
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

        # events TODO: Add event handler module to reduce the length of main
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
                    
                    if state.editor_mode: # avoid system beep on keypress
                        pygame.key.start_text_input()
                    else:
                        pygame.key.stop_text_input()

                    state.selected_obj = None
                    gizmo.stop_drag()
                elif ev.key == K_ESCAPE:
                    state.selected_obj = None
                    gizmo.stop_drag()
                
                if ctrl:
                    if ev.key == K_s:
                        action = "save_as_project" if shift else "save_project"
                        project.process_action(action)
                    elif ev.key == K_o:
                        project.process_action("open_project")
                    elif ev.key == K_n:
                        project.process_action("new_project")
                elif ev.key == K_DELETE and state.editor_mode:
                    project.process_action("delete")

            if state.editor_mode:
                if ev.type == MOUSEBUTTONDOWN and ev.button == 1:
                    handle_selection(state, world, gizmo, m_pos)
                elif ev.type == MOUSEBUTTONUP and ev.button == 1:
                    gizmo.stop_drag()

        if state.editor_mode:
            if gizmo.active_axis is not None and state.selected_obj:
                ray_o, ray_d = InteractionHandler.get_ray(m_pos[0], m_pos[1])
                new_pos = gizmo.update_drag(ray_o, ray_d)
                if new_pos is not None:
                    state.selected_obj.set_position(*new_pos)
                    state.has_unsaved_changes = True
                    project.update_title()
        else:
            player.update(dt)

        render_scene(win_w, win_h, state, world, player, gizmo)

    pygame.quit()