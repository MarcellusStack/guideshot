import json
from pathlib import Path

class SettingsManager:
    def __init__(self):
        self.settings_file = Path("settings.json")
        self.default_settings = {
            'stop_key': 'Esc', 
            'screenshot_key': 'Space', 
            'mouse_click_enabled': False,
            'circle_size': 20,
            'circle_color': '#FF0000',  # Red color in hex
            'create_pdf': False,  # Create PDF from guides
            'create_video': False,  # Create video from guides
            'screenshot_duration': 2.0,  # Duration in seconds each screenshot is shown in video
            'helper_text_enabled': False,  # Enable helper text under circle
            'helper_text': 'Click here',  # Default helper text
            'voice_enabled': False,  # Enable voice recording per screenshot
            'voice_key': 'v',  # Key to hold for voice recording  
            'speech_to_text': True,  # Convert speech to text for PDF captions
            'text_to_speech': True,  # Generate TTS audio for video
            'tts_voice': 'default',  # TTS voice selection (default, google, windows)
            'voice_language': 'de'  # Voice language (de=German, en=English)
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