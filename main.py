import sys
import os
import pygame
import numpy as np
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *

from config.config import Config
from ui.menuObj.menu_bar import MenuBar
from editor.gizmo import Gizmo
from obj.player import Player
from obj.rectangular_prism import RectangularPrism
from obj.world import World
from utils.file_manager import FileManager
from initializer import EngineInitializer

# Global state for change tracking
has_unsaved_changes = False

def update_window_title(file_path=None):
    """Updates the window title with project name and unsaved changes indicator."""
    global has_unsaved_changes
    base_title = "Zenith Engine"
    project_name = os.path.basename(file_path) if file_path else "Untitled Project"
    asterisk = "*" if has_unsaved_changes else ""
    pygame.display.set_caption(f"{base_title} - {project_name}{asterisk}")

def mark_changes():
    """Sets the dirty flag and updates the title."""
    global has_unsaved_changes
    if not has_unsaved_changes:
        has_unsaved_changes = True

def get_world_data(world):
    return {
        "objects": [{"type": "cube", "x": o.x, "y": o.y, "z": o.z} for o in world.objects]
    }

def handle_menu_action(action, world, player, current_selection, file_manager):
    global has_unsaved_changes
    if not action or action == "STAY_OPEN": return True
    
    # Handle Exit separately to check for changes
    if action == "exit":
        if has_unsaved_changes:
            pygame.event.set_grab(False)
            pygame.mouse.set_visible(True)
            res = file_manager.ask_save_changes() # returns True (yes), False (no), None (cancel)
            if res is True: # Yes
                # Attempt save
                save_action = "save_project"
                handle_menu_action(save_action, world, player, current_selection, file_manager)
                return False # Exit after saving
            elif res is False: # No
                return False # Exit without saving
            else: # Cancel
                return True # Stay in app
        return False

    is_dialog_action = action in ["new_project", "open_project", "save_project", "save_as_project"]
    if is_dialog_action:
        pygame.event.set_grab(False)
        pygame.mouse.set_visible(True)
        pygame.event.pump()

    if action == "new_project":
        world.objects = []
        file_manager.current_file_path = None
        has_unsaved_changes = False
        update_window_title(None)

    elif action == "open_project":
        path = file_manager.open_file_dialog()
        if path:
            data = file_manager.load_from_path(path)
            if data:
                world.objects = [] 
                for obj_data in data.get("objects", []):
                    cube = RectangularPrism(1, 1, 1)
                    cube.set_position(obj_data['x'], obj_data['y'], obj_data['z'])
                    world.add_object(cube)
                has_unsaved_changes = False
                update_window_title(path)
        
    elif action == "save_project":
        path = file_manager.current_file_path
        if not path:
            path = file_manager.save_file_dialog()
        
        if path:
            if file_manager.save_to_path(path, get_world_data(world)):
                has_unsaved_changes = False
                update_window_title(path)

    elif action == "save_as_project":
        path = file_manager.save_file_dialog("Save As...")
        if path:
            if file_manager.save_to_path(path, get_world_data(world)):
                has_unsaved_changes = False
                update_window_title(path)

    elif action == "add_cube":
        new_cube = RectangularPrism(1.0, 1.0, 1.0)
        new_cube.set_position(0, 0.5, 0)
        world.add_object(new_cube)
        has_unsaved_changes = True
        update_window_title(file_manager.current_file_path)

    elif action == "delete":
        if current_selection and current_selection in world.objects:
            world.objects.remove(current_selection)
            has_unsaved_changes = True
            update_window_title(file_manager.current_file_path)
            return "clear_selection"

    if is_dialog_action:
        pygame.event.clear()
    
    return True

def get_ray_from_mouse(mouse_x, mouse_y, win_w, win_h):
    """Converts 2D screen coordinates to a 3D ray in world space."""
    modelview = glGetDoublev(GL_MODELVIEW_MATRIX)
    projection = glGetDoublev(GL_PROJECTION_MATRIX)
    viewport = glGetIntegerv(GL_VIEWPORT)
    real_y = viewport[3] - mouse_y
    try:
        near_point = gluUnProject(mouse_x, real_y, 0.0, modelview, projection, viewport)
        far_point = gluUnProject(mouse_x, real_y, 1.0, modelview, projection, viewport)
    except:
        return np.array([0,0,0]), np.array([0,0,-1])
    ray_origin = np.array(near_point)
    ray_direction = np.array(far_point) - ray_origin
    norm = np.linalg.norm(ray_direction)
    if norm > 0: ray_direction /= norm
    return ray_origin, ray_direction

def setup_lighting():
    glEnable(GL_LIGHTING)
    glEnable(GL_LIGHT0)
    glEnable(GL_COLOR_MATERIAL)
    glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)
    glLightfv(GL_LIGHT0, GL_POSITION, [5, 10, 5, 1])
    glLightfv(GL_LIGHT0, GL_AMBIENT, [0.2, 0.2, 0.2, 1])
    glLightfv(GL_LIGHT0, GL_DIFFUSE, [0.8, 0.8, 0.8, 1])

def is_mouse_in_ui(menu_bar, mpos):
    """Checks if mouse is over the bar or any open submenus."""
    if mpos[1] <= menu_bar.height:
        return True
    
    def check_recursive(items):
        for item in items:
            if item.is_open:
                if item.children:
                    r = item.children[0].rect
                    submenu_rect = pygame.Rect(r.left, r.top, item.submenu_width, item.submenu_height)
                    if submenu_rect.collidepoint(mpos):
                        return True
                    if check_recursive(item.children):
                        return True
        return False
    return check_recursive(menu_bar.items)

def render_frame(world, player, menu_bar, gizmo, editor_mode, selected_obj):
    surf = pygame.display.get_surface()
    if not surf: return
    win_w, win_h = surf.get_size()
    
    glViewport(0, 0, win_w, win_h)
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    
    glEnable(GL_DEPTH_TEST)
    setup_lighting()
    
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    aspect_ratio = win_w / win_h if win_h > 0 else 1
    gluPerspective(player.config.get("fov", 70), aspect_ratio, 0.1, 100.0)
    
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    player.apply_look()
    
    world.draw_floor()
    world.draw_axes()
    
    for obj in world.objects:
        glPushMatrix()
        glTranslatef(obj.x, obj.y, obj.z)
        if obj == selected_obj:
            glPushAttrib(GL_LIGHTING_BIT)
            glMaterialfv(GL_FRONT, GL_EMISSION, [0.0, 0.2, 0.0, 1.0])
            glColor3f(0.4, 1.0, 0.4) 
            obj.draw()
            glPopAttrib()
        else:
            glColor3f(0.7, 0.7, 0.7)
            obj.draw()
        glPopMatrix()

    if selected_obj:
        gizmo.draw(np.array([selected_obj.x, selected_obj.y, selected_obj.z]))

    glDisable(GL_LIGHTING)
    glDisable(GL_DEPTH_TEST)
    
    if editor_mode:
        menu_bar.draw(win_w, win_h)

    pygame.display.flip()

if __name__ == "__main__":
    config = Config()
    initializer = EngineInitializer(config)
    win_w, win_h = initializer.start()
    world = World(config)
    player = Player(config)
    menu_bar = MenuBar(config, pygame.font.Font(None, 24))
    gizmo = Gizmo()
    file_manager = FileManager()
    
    update_window_title(None)
    
    menu_bar.add_menu("File", [
        ("New Project", "new_project"),
        ("Open", "open_project"),
        ("Save", "save_project"),
        ("Save As", "save_as_project"),
        ("Exit", "exit")
    ])
    menu_bar.add_menu("Edit", [("Delete", "delete")])
    menu_bar.add_menu("Add", [("Primitive", None, [("Cube", "add_cube")])])

    editor_mode = False
    pygame.event.set_grab(True)
    pygame.mouse.set_visible(False)
    running = True
    selected_obj = None
    clock = pygame.time.Clock()

    while running:
        clock.tick(60)
        events = pygame.event.get()
        mouse_pos = pygame.mouse.get_pos()
        surface = pygame.display.get_surface()
        win_w, win_h = surface.get_size() if surface else (win_w, win_h)

        for ev in events:
            if ev.type == QUIT:
                if handle_menu_action("exit", world, player, selected_obj, file_manager) is False:
                    running = False
                continue

            if ev.type == VIDEORESIZE:
                win_w, win_h = ev.size
                pygame.display.set_mode((win_w, win_h), DOUBLEBUF | OPENGL | RESIZABLE)
                try:
                    icon = pygame.image.load("zenith_ico_DRAFT.png")
                    pygame.display.set_icon(icon)
                except: pass
            
            if ev.type == KEYDOWN:
                if ev.key == K_F1 or ev.key == K_TAB:
                    editor_mode = not editor_mode
                    pygame.event.set_grab(not editor_mode)
                    pygame.mouse.set_visible(editor_mode)
                    if not editor_mode: 
                        selected_obj = None 
                        gizmo.stop_drag()

            if editor_mode:
                if ev.type == MOUSEBUTTONDOWN and ev.button == 1:
                    if not is_mouse_in_ui(menu_bar, mouse_pos):
                        ray_o, ray_d = get_ray_from_mouse(mouse_pos[0], mouse_pos[1], win_w, win_h)
                        hit_gizmo = False
                        if selected_obj:
                            axis_hit = gizmo.check_hover(ray_o, ray_d, np.array([selected_obj.x, selected_obj.y, selected_obj.z]))
                            if axis_hit is not None:
                                gizmo.start_drag(axis_hit, ray_o, ray_d, np.array([selected_obj.x, selected_obj.y, selected_obj.z]))
                                hit_gizmo = True
                        
                        if not hit_gizmo:
                            best_obj, min_dist = None, float('inf')
                            for obj in world.objects:
                                obj_center = np.array([obj.x, obj.y, obj.z])
                                dist_to_ray = np.linalg.norm(np.cross(ray_d, ray_o - obj_center))
                                if dist_to_ray < 0.3: 
                                    depth = np.dot(obj_center - ray_o, ray_d)
                                    if 0 < depth < min_dist:
                                        min_dist = depth
                                        best_obj = obj
                            selected_obj = best_obj

                if ev.type == MOUSEBUTTONUP and ev.button == 1:
                    gizmo.stop_drag()

        if editor_mode:
            menu_bar.update_layout(win_w)
            action = menu_bar.handle_input(events)
            if action:
                result = handle_menu_action(action, world, player, selected_obj, file_manager)
                if result is False: running = False
                elif result == "clear_selection": selected_obj = None
            
            if gizmo.active_axis is not None and selected_obj:
                ray_o, ray_d = get_ray_from_mouse(mouse_pos[0], mouse_pos[1], win_w, win_h)
                new_pos = gizmo.update_drag(ray_o, ray_d)
                if new_pos is not None:
                    selected_obj.set_position(*new_pos)
                    if not has_unsaved_changes:
                        has_unsaved_changes = True
                        update_window_title(file_manager.current_file_path)
        else:
            res = player.handle_input(events)
            if res and all(v is not None for v in res): player.update(*res)

        render_frame(world, player, menu_bar, gizmo, editor_mode, selected_obj)

    pygame.quit()
    sys.exit()