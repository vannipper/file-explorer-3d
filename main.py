import sys
import os
import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *

from config.config import Config
from ui.menu import Menu
from ui.menu_bar import MenuBar
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

	# reset cursor/grab to a known state
	pygame.event.set_grab(False)
	pygame.mouse.set_visible(False)
	pygame.event.set_grab(True)

	fs["size"] = (w, h)

	glViewport(0, 0, w, h)
	glMatrixMode(GL_PROJECTION)
	glLoadIdentity()
	gluPerspective(config.get("fov", 70), float(w) / float(h), 0.1, 100.0)
	glMatrixMode(GL_MODELVIEW)
	glEnable(GL_DEPTH_TEST)
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
	menu = Menu(config, on_toggle_fullscreen=toggle_fullscreen_cb)
	menu_bar = MenuBar(config, font=pygame.font.Font(None, 32))
	clock = pygame.time.Clock()

	return world, player, menu, menu_bar, clock


def handle_menu_action(action, config, world, toggle_fullscreen_cb):
	if not action:
		return None
	if action == "settings":
		return ("menu_toggle", None)
	if action == "exit":
		return ("quit", None)
	if action == "show_grid":
		new_val = not config.get("show_grid", False)
		config.set("show_grid", new_val); config.save()
		return None
	if action == "show_axes":
		new_val = not config.get("show_axes", False)
		config.set("show_axes", new_val); config.save()
		return None
	if action == "debug_info":
		new_val = not config.get("debug_info", False)
		config.set("debug_info", new_val); config.save()
		return None
	if action == "fullscreen":
		toggle_fullscreen_cb()
		return None
	if action == "add_cube":
		cube = RectangularPrism(width=1.0, height=1.0, depth=1.0)
		cube.set_position(0, 1, 0)
		world.add_object(cube)
		return None
	# Unknown action: no-op
	return None


def render_frame(world, player, menu, menu_bar, fps):
	surf = pygame.display.get_surface()
	win_w = win_h = None
	if surf:
		win_w, win_h = surf.get_size()

	glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
	glMatrixMode(GL_MODELVIEW)
	glLoadIdentity()
	player.apply_look()

	world.draw_all()

	# modal menu
	menu.draw()

	if surf:
		menu.draw_debug_info(player.position(player.camera), fps, win_w, win_h)
		# only draw the bar in editor mode (collapsed in game mode)
		if editor_mode:
			menu_bar.draw(win_w, win_h)

	pygame.display.flip()


if __name__ == "__main__":
	# Load config & init pygame
	config = Config()
	pygame.init()
	info = pygame.display.Info()
	desktop_w, desktop_h = info.current_w, info.current_h

	# shared mutable fullscreen/state container
	fs = {"on": bool(config.get("start_fullscreen", False)), "size": (desktop_w, desktop_h)}

	# prepare display and callbacks
	create_display(config, desktop_w, desktop_h, fs)
	toggle_fullscreen = make_toggle_fullscreen(config, fs, desktop_w, desktop_h)

	# create scene objects
	world, player, menu, menu_bar, clock = create_scene(config, toggle_fullscreen)

	editor_mode = False
	running = True

	while running:
		dt = clock.tick(60) / 1000.0
		fps = clock.get_fps()

		# Poll events once
		events = pygame.event.get()

		# allow quitting from anywhere
		for ev in events:
			if ev.type == QUIT:
				running = False

		# global toggle: F1 toggle editor/game
		for ev in events:
			if ev.type == KEYDOWN and ev.key == K_F1:
				editor_mode = not editor_mode
				if editor_mode:
					pygame.event.set_grab(False)
					pygame.mouse.set_visible(True)
					pygame.display.set_caption("Minimal 3D Engine - EDITOR MODE (F1 to toggle)")
				else:
					# collapse/hide developer tools when entering game mode
					pygame.event.set_grab(True)
					pygame.mouse.set_visible(False)
					pygame.display.set_caption("Minimal 3D Engine - GAME MODE (F1 to toggle)")
					# Collapse menu/modal and menu bar state
					menu.active = False
					menu.selected_option = 0
					menu.option_rects = []
					# collapse menu bar UI
					menu_bar.active_menu = None
					menu_bar.hovered_item = None
					menu_bar.hovered_subitem = None
					menu_bar.submenu_rects = []

		# layout menu bar for hit-testing before input handling
		surf = pygame.display.get_surface()
		if surf:
			win_w, win_h = surf.get_size()
			menu_bar.update_layout(win_w, win_h)
			# update hover from current mouse position so highlight persists
			menu_bar.update_hover(pygame.mouse.get_pos())

		# click-top-to-enter-editor convenience
		if not editor_mode and not menu.active:
			for ev in events:
				if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
					if ev.pos[1] <= menu_bar.height:
						editor_mode = True
						pygame.event.set_grab(False)
						pygame.mouse.set_visible(True)
						break

		# menu bar input always gets events
		action = menu_bar.handle_input(events)
		if action:
			if not editor_mode:
				editor_mode = True
				pygame.event.set_grab(False)
				pygame.mouse.set_visible(True)
			res = handle_menu_action(action, config, world, toggle_fullscreen)
			if isinstance(res, tuple):
				if res[0] == "menu_toggle":
					menu.toggle()
				elif res[0] == "quit":
					running = False

		# Menu modal handling / editor / game modes
		if menu.active:
			pygame.event.set_grab(False)
			pygame.mouse.set_visible(True)
			if menu.handle_input(events):
				running = False
		elif editor_mode:
			pygame.event.set_grab(False)
			pygame.mouse.set_visible(True)
			for ev in events:
				if ev.type == KEYDOWN and ev.key == K_TAB:
					editor_mode = False
					pygame.event.set_grab(True)
					pygame.mouse.set_visible(False)
		else:
			pygame.event.set_grab(True)
			pygame.mouse.set_visible(False)
			for ev in events:
				if ev.type == KEYDOWN:
					if ev.key == K_ESCAPE:
						menu.toggle()
					elif ev.key == K_TAB:
						editor_mode = True
						pygame.event.set_grab(False)
						pygame.mouse.set_visible(True)

			forward, right = player.handle_input(events, menu)
			if forward is None:
				running = False
			else:
				player.update(forward, right)

		# Render
		render_frame(world, player, menu, menu_bar, fps)

	# Clean up
	pygame.quit()
	sys.exit()