import json
import os


class Config:
    """Handles loading and saving user preferences."""
    
    CONFIG_FILE = "config.json"
    
    DEFAULT_SETTINGS = {
        "mouse_sensitivity": 1.0,
        "move_speed": 1.0,
        "show_grid": True,
        "show_axes": True,
        "fov": 70,
        "start_fullscreen": False,
    }
    
    def __init__(self):
        self.settings = self.load()
    
    def load(self):
        """Load settings from config file, or return defaults if not found."""
        if os.path.exists(self.CONFIG_FILE):
            try:
                with open(self.CONFIG_FILE, 'r') as f:
                    return json.load(f)
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
        """Get a setting value."""
        return self.settings.get(key, default)
    
    def set(self, key, value):
        """Set a setting value."""
        self.settings[key] = value
