import json
from pathlib import Path

class SettingsManager:
    def __init__(self):
        self.settings_file = Path("settings.json")
        self.default_settings = {
            'stop_key': 'Esc', 
            'screenshot_key': 'Space', 
            'mouse_click_enabled': False
        }
    
    def load_settings(self):
        """Load settings from JSON file"""
        if self.settings_file.exists():
            try:
                with open(self.settings_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading settings: {e}")
        return self.default_settings.copy()
    
    def save_settings(self, settings):
        """Save settings to JSON file"""
        try:
            with open(self.settings_file, 'w') as f:
                json.dump(settings, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving settings: {e}")
            return False
    
    def get_default_settings(self):
        """Get default settings"""
        return self.default_settings.copy() 