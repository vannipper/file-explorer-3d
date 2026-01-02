import sys
import os
import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *

from config.config import Config
from ui.menuObj.menu_bar import MenuBar
from objects.player import Player
from objects.rectangular_prism import RectangularPrism
from objects.world import World


def create_display(config, desktop_w, desktop_h, fs):
    """Create the pygame display and reinitialize OpenGL projection/viewport."""
    if fs["on"]:
        w, h = desktop_w, desktop_h
    else:
        w = max(640, int(desktop_w * 0.9))
        h = max(480, int(desktop_h * 0.9) - 40)
        pos_x = (desktop_w - w) // 2
        pos_y = (desktop_h - h) // 2
        os.environ['SDL_VIDEO_WINDOW_POS'] = f"{pos_x},{pos_y}"

    if fs["on"]:
        flags = FULLSCREEN | DOUBLEBUF | OPENGL
    else:
        flags = DOUBLEBUF | OPENGL

    pygame.display.set_mode((w, h), flags)
    pygame.display.set_caption("Minimal 3D Engine - WASD + Mouse Look (ESC for menu)")

    pygame.event.set_grab(False)
    pygame.mouse.set_visible(True) 

    fs["size"] = (w, h)

    glViewport(0, 0, w, h)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(config.get("fov", 70), float(w) / float(h), 0.1, 100.0)
    glMatrixMode(GL_MODELVIEW)
    glEnable(GL_DEPTH_TEST)
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glClearColor(0.1, 0.1, 0.15, 1.0)


def make_toggle_fullscreen(config, fs, desktop_w, desktop_h):
    def toggle_fullscreen(new_state=None):
        if new_state is None:
            fs["on"] = not fs["on"]
        else:
            fs["on"] = bool(new_state)
        config.set("start_fullscreen", fs["on"])
        config.save()
        create_display(config, desktop_w, desktop_h, fs)
        pygame.event.clear()
    return toggle_fullscreen


def create_scene(config, toggle_fullscreen_cb):
    world = World(config)
    prism = RectangularPrism(width=2.0, height=2.0, depth=2.0)
    prism.set_position(0, 1, 0)
    world.add_object(prism)

    player = Player(
        config=config,
        mouse_sensitivity=0.1,
        move_speed=0.1,
        fullscreen_toggle=toggle_fullscreen_cb
    )
    menu_bar = MenuBar(config=config, font=pygame.font.Font(None, 24))
    
    menu_bar.add_menu("File", [
        ("New", "new"), ("Open", "open"), ("Save", "save"), 
        ("Save As", "save_as"), ("---", None), ("Exit", "exit")
    ])
    menu_bar.add_menu("Edit", [
        ("Undo", "undo"), ("Redo", "redo"), ("---", None),
        ("Delete Selected", "delete"), ("Duplicate Selected", "duplicate")
    ])
    menu_bar.add_menu("View", [
        ("---", None), ("Show Grid", "show_grid"),
        ("Show Axes", "show_axes"),
        ("---", None), ("Reset Camera", "reset_camera"), ("Fullscreen", "fullscreen")
    ])
    menu_bar.add_menu("Add", [
        ("Primitive", None, [
            ("Cube", "add_cube"), ("Sphere", "add_sphere")
        ]),
        ("Light", "add_light")
    ])

    clock = pygame.time.Clock()
    return world, player, menu_bar, clock


def handle_menu_action(action, config, world, toggle_fullscreen_cb):
    if not action: return None
    if action == "exit": return ("quit", None)
    if action == "show_grid":
        config.set("show_grid", not config.get("show_grid", False))
        config.save(); return None
    if action == "show_axes":
        config.set("show_axes", not config.get("show_axes", False))
        config.save(); return None
    if action == "fullscreen":
        toggle_fullscreen_cb(); return None
    
    if action == "add_cube":
        cube = RectangularPrism(1, 1, 1); cube.set_position(0, 1, 0)
        world.add_object(cube); return None
        
    return None


def render_frame(world, player, menu_bar, fps, editor_mode):
    surf = pygame.display.get_surface()
    if not surf: return
    win_w, win_h = surf.get_size()

    # --- 1. START 3D PASS ---
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glEnable(GL_DEPTH_TEST)
    
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(player.config.get("fov", 70), float(win_w) / float(win_h), 0.1, 100.0)
    
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    
    # Always apply camera orientation (even in editor mode)
    player.apply_look()
    
    # Draw the actual 3D objects
    world.draw_all()
    glFlush() # Ensure 3D is sent to GPU before switching to 2D

    # --- 2. START 2D PASS ---
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    glOrtho(0, win_w, win_h, 0, -1, 1)
    
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    
    glDisable(GL_DEPTH_TEST) # Disable depth for UI
    
    if editor_mode:
        menu_bar.draw(win_w, win_h)

    # Clean up matrices
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)
    glPopMatrix()
    
    pygame.display.flip()


if __name__ == "__main__":
    config = Config()
    pygame.init()
    info = pygame.display.Info()
    desktop_w, desktop_h = info.current_w, info.current_h
    fs = {"on": bool(config.get("start_fullscreen", False)), "size": (desktop_w, desktop_h)}

    create_display(config, desktop_w, desktop_h, fs)
    toggle_fullscreen = make_toggle_fullscreen(config, fs, desktop_w, desktop_h)
    world, player, menu_bar, clock = create_scene(config, toggle_fullscreen)

    editor_mode = False
    running = True

    pygame.event.set_grab(True)
    pygame.mouse.set_visible(False)

    while running:
        dt = clock.tick(60) / 1000.0
        fps = clock.get_fps()
        events = pygame.event.get()

        surf = pygame.display.get_surface()
        if surf:
            win_w, _ = surf.get_size()
            menu_bar.update_layout(win_w)

        # 1. Handle Global Input
        for ev in events:
            if ev.type == QUIT:
                running = False
            if ev.type == KEYDOWN:
                if ev.key == K_F1 or ev.key == K_TAB:
                    editor_mode = not editor_mode
                    if editor_mode:
                        pygame.event.set_grab(False)
                        pygame.mouse.set_visible(True)
                    else:
                        pygame.event.set_grab(True)
                        pygame.mouse.set_visible(False)
                        menu_bar._close_all(menu_bar.items)

        # 2. Process Input based on Mode
        if editor_mode:
            # INTERACTION: Menu Bar (F1 Screen)
            action = menu_bar.handle_input(events)
            if action:
                res = handle_menu_action(action, config, world, toggle_fullscreen)
                if res and res[0] == "quit": running = False
            
            # CRITICAL: We DO NOT call player.handle_input here.
            # Calling it when the mouse isn't grabbed resets the camera's relative motion,
            # which caused the "disappearing world" effect in previous versions.
        else:
            # INTERACTION: Gameplay
            forward, right = player.handle_input(events)
            if forward is None: 
                running = False
            else: 
                player.update(forward, right)

        # 3. Always render the frame
        render_frame(world, player, menu_bar, fps, editor_mode)

    pygame.quit()
    sys.exit()