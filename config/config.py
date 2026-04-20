"""
FileExplorer3D - config.py
Contains the Config class, which loads and saves user preferences.
"""

import json
import os

class Config:
    """Handles loading and saving user preferences."""

    CONFIG_FILE = "config.json"

    DEFAULT_SETTINGS = {
        "mouse_sensitivity": 1.0,
        "move_speed": 5.0,
        "last_opened_folder": "~",
        "window_width": 1280,
        "window_height": 720,
        "bookmarks": [],
    }

    def __init__(self):
        self.settings = self.load()

    def load(self):
        """Load settings from config file, or return defaults if not found."""
        if os.path.exists(self.CONFIG_FILE):
            try:
                with open(self.CONFIG_FILE, 'r') as f:
                    loaded = json.load(f)
                    return {**self.DEFAULT_SETTINGS, **loaded}
            except Exception:
                return self.DEFAULT_SETTINGS.copy()
        return self.DEFAULT_SETTINGS.copy()

    def save(self):
        """Save current settings to config file."""
        try:
            with open(self.CONFIG_FILE, 'w') as f:
                json.dump(self.settings, f, indent=2)
        except Exception as e:
            print(f"Failed to save config: {e}")

    def get(self, key, default=None):
        value = self.settings.get(key, default)
        if isinstance(value, str):
            return os.path.expanduser(value)
        return value

    def set(self, key, value):
        if isinstance(value, str):
            home = os.path.expanduser("~")
            if value.startswith(home):
                value = "~" + value[len(home):]
        self.settings[key] = value
