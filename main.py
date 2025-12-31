import sys
import os
import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *

from config.config import Config
from ui.menu import Menu
from objects.player import Player
from objects.rectangular_prism import RectangularPrism
from objects.world import World

if __name__ == "__main__":
	# Load configuration
	config = Config()

	pygame.init()

	# Query desktop/main monitor size and decide flags
	info = pygame.display.Info()
	desktop_w, desktop_h = info.current_w, info.current_h

	# use a mutable container so nested callback can modify state and store current size
	fs = {"on": bool(config.get("start_fullscreen", False)), "size": (desktop_w, desktop_h)}

	def set_display(fullscreen):
		"""Create the pygame display and reinitialize OpenGL projection/viewport."""
		# choose window size: slightly smaller than desktop when windowed so title bar is visible
		if fullscreen:
			w, h = desktop_w, desktop_h
		else:
			# use 90% of desktop and subtract a bit of height for title bar
			w = max(640, int(desktop_w * 0.9))
			h = max(480, int(desktop_h * 0.9) - 40)

			# center the window on the main monitor
			pos_x = (desktop_w - w) // 2
			pos_y = (desktop_h - h) // 2
			# set SDL env for window position before creating window
			os.environ['SDL_VIDEO_WINDOW_POS'] = f"{pos_x},{pos_y}"

		if fullscreen:
			flags = FULLSCREEN | DOUBLEBUF | OPENGL
		else:
			flags = DOUBLEBUF | OPENGL

		# create display
		pygame.display.set_mode((w, h), flags)
		pygame.display.set_caption("Minimal 3D Engine - WASD + Mouse Look (ESC for menu)")

		# completely reset cursor state: ungrab, hide, then regrab
		pygame.event.set_grab(False)
		pygame.mouse.set_visible(False)
		pygame.event.set_grab(True)

		# remember current size for rendering and menu
		fs["size"] = (w, h)

		# OpenGL viewport / projection update
		glViewport(0, 0, w, h)
		glMatrixMode(GL_PROJECTION)
		glLoadIdentity()
		gluPerspective(config.get("fov", 70), float(w) / float(h), 0.1, 100.0)
		glMatrixMode(GL_MODELVIEW)
		# re-enable standard GL state (depth test / clear color)
		glEnable(GL_DEPTH_TEST)
		glClearColor(0.1, 0.1, 0.15, 1.0)

	def toggle_fullscreen(new_state=None):
		"""Toggle or set fullscreen, update config and apply display change immediately."""
		if new_state is None:
			fs["on"] = not fs["on"]
		else:
			fs["on"] = bool(new_state)
		config.set("start_fullscreen", fs["on"])
		config.save()
		set_display(fs["on"])
		pygame.event.clear()

	# Apply initial display mode (windowed by default unless config requests fullscreen)
	set_display(fs["on"])

	# Create world and add objects
	world = World(config)
	prism = RectangularPrism(width=2.0, height=2.0, depth=2.0)
	prism.set_position(0, 1, 0)
	world.add_object(prism)

	# pass toggle_fullscreen into Player and Menu so they can switch modes at runtime
	# base mouse sensitivity and move speed set to previous defaults to preserve feel
	player = Player(
		config=config,
		mouse_sensitivity=0.1,   # base sensitivity (actual used = base * slider)
		move_speed=0.1,          # base move speed (actual used = base * slider)
		fullscreen_toggle=toggle_fullscreen
	)
	menu = Menu(config, on_toggle_fullscreen=toggle_fullscreen)
	clock = pygame.time.Clock()

	running = True
	while running:
		dt = clock.tick(60) / 1000.0

		if menu.active:
			pygame.event.set_grab(False)
			pygame.mouse.set_visible(True)
			running = not menu.handle_input()
		else:
			pygame.event.set_grab(True)
			pygame.mouse.set_visible(False)
			forward, right = player.handle_input(menu)
			
			if forward is None:
				running = False
				continue

			player.update(forward, right)

		# Render
		glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

		glMatrixMode(GL_MODELVIEW)
		glLoadIdentity()
		player.apply_look()

		world.draw_all()
		
		# draw menu (menu will query the actual display size itself)
		menu.draw()

		pygame.display.flip()

	pygame.quit()
	sys.exit()
