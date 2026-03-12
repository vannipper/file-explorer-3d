"""
FileExplorer3D - main.py
This is the main file which contains all module calls and the main loop.
"""

# pip imports
import pygame
import numpy as np
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
from config.config import Config
from utils.file_manager import FileManager # TODO: implement loading a parent folder as the first action for this app
from utils.initializer import EngineInitializer
from utils.interaction_handler import InteractionHandler
from utils.renderer import Renderer

# TODO: Move this to either gizmo, world, or player
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

if __name__ == "__main__":
    config = Config()
    config.load()
    
    # initialize Pygame
    EngineInitializer.InitializePygame()
    clock = pygame.time.Clock()

    # initialize engine components
    EngineInitializer.load_last_project(config)
    world, player, selector, file_manager = EngineInitializer.InitializeEngineComponents(config)
    
    # video variables
    win_w, win_h = EngineInitializer.InitializeOpenGLWindow()
    mpos = InteractionHandler.GetMousePosition()
    
    # main loop
    run = True
    while run:
        dt = clock.tick(60) / 1000.0

        # Handle Pygame events
        events = pygame.event.get()
        run = player.handle_events(events)
        world.handle_events(events)
        Renderer.handle_events(events)
        
        # update player
        player.update(dt)

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
            
            if obj == world.selected_obj:
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

        if world.selected_obj:
            glDisable(GL_DEPTH_TEST)
            selector.draw(np.array([world.selected_obj.x, world.selected_obj.y, world.selected_obj.z]))
            glColor3f(1.0, 1.0, 1.0)
            glEnable(GL_DEPTH_TEST)
            
        glDisable(GL_LIGHTING); glDisable(GL_DEPTH_TEST)
        pygame.display.flip()
    pygame.quit()
