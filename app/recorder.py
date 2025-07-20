import keyboard
from datetime import datetime
from pathlib import Path
import pyautogui
from PIL import Image, ImageDraw
from PySide6.QtCore import QObject, Signal, QTimer

class ScreenshotRecorder(QObject):
    """Handles screenshot recording functionality"""
    
    # Qt signals for thread-safe communication
    screenshot_signal = Signal()
    stop_signal = Signal()
    
    def __init__(self):
        super().__init__()
        self.is_recording = False
        self.screenshots_folder = Path("screenshots")
        self.screenshots_folder.mkdir(exist_ok=True)
        self.current_session_folder = None
        
        # Screenshot timing
        self.last_screenshot_time = 0
        self.screenshot_cooldown = 0.5  # seconds
        
        # Mouse detection
        self.last_mouse_state = False
        self.mouse_timer = None
        self.mouse_listener = None
    
    def create_session_folder(self):
        """Create a new session folder for screenshots"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.current_session_folder = self.screenshots_folder / f"session_{timestamp}"
        self.current_session_folder.mkdir(exist_ok=True)
        return self.current_session_folder
    
    def setup_hotkeys(self, settings):
        """Setup keyboard hotkeys for recording"""
        keyboard.unhook_all()
        
        try:
            screenshot_key = settings.get('screenshot_key', 'space').lower()
            stop_key = settings.get('stop_key', 'esc').lower()
            mouse_enabled = settings.get('mouse_click_enabled', False)
            
            print(f"Setting up hotkeys: Screenshot='{screenshot_key}', Stop='{stop_key}', Mouse={mouse_enabled}")
            
            # Create wrapper functions that emit signals (thread-safe)
            def screenshot_wrapper():
                if self.is_recording:
                    print(f"Screenshot hotkey '{screenshot_key}' pressed - emitting signal...")
                    self.screenshot_signal.emit()
                else:
                    print("Screenshot key pressed but not recording")
            
            def stop_wrapper():
                if self.is_recording:
                    print(f"Stop hotkey '{stop_key}' pressed - emitting signal...")
                    self.stop_signal.emit()
                else:
                    print("Stop key pressed but not recording")
            
            # Always set up keyboard hotkeys first (they take priority)
            try:
                keyboard.add_hotkey(screenshot_key, screenshot_wrapper, suppress=False)
                print(f"Screenshot hotkey '{screenshot_key}' registered")
            except Exception as e:
                print(f"Failed to register screenshot hotkey: {e}")
            
            try:
                keyboard.add_hotkey(stop_key, stop_wrapper, suppress=False)
                print(f"Stop hotkey '{stop_key}' registered")
            except Exception as e:
                print(f"Failed to register stop hotkey: {e}")
                
        except Exception as e:
            print(f"Error setting up hotkeys: {e}")
        
        # Setup mouse detection AFTER keyboard hotkeys (so they don't conflict)
        if mouse_enabled:
            self.setup_mouse_detection()
        else:
            print("Mouse click detection disabled in settings.")
    
    def setup_mouse_detection(self):
        """Setup mouse click detection"""
        try:
            # Try to use pynput for mouse detection if available
            try:
                from pynput import mouse
                
                def on_click(x, y, button, pressed):
                    if self.is_recording and pressed and button == mouse.Button.left:
                        current_time = datetime.now().timestamp()
                        # Add debounce to prevent multiple screenshots
                        if not hasattr(self, 'last_click_time') or (current_time - self.last_click_time) > 0.5:
                            print("Mouse click detected - emitting signal...")
                            self.screenshot_signal.emit()
                            self.last_click_time = current_time
                
                # Start mouse listener
                self.mouse_listener = mouse.Listener(on_click=on_click)
                self.mouse_listener.start()
                print("Mouse click detection enabled (using pynput).")
                return
                
            except ImportError:
                print("pynput not available, trying alternative method...")
                
            # Fallback: Use a simple timer-based approach with minimal interference
            self.last_mouse_state = False
            self.mouse_timer = QTimer(self)
            self.mouse_timer.timeout.connect(self.check_mouse_simple)
            self.mouse_timer.start(200)  # Check every 200ms (less frequent)
            print("Mouse click detection enabled (fallback method).")
            
        except Exception as e:
            print(f"Failed to setup mouse detection: {e}")
    
    def check_mouse_simple(self):
        """Simple mouse check with minimal interference"""
        if not self.is_recording:
            return
        
        try:
            # Very simple check - just detect button state changes
            current_mouse_state = pyautogui.mouseDown(button='left')
            
            # Only trigger on new press (not hold)
            if current_mouse_state and not self.last_mouse_state:
                current_time = datetime.now().timestamp()
                if not hasattr(self, 'last_click_time') or (current_time - self.last_click_time) > 0.5:
                    print("Mouse click detected - emitting signal...")
                    self.screenshot_signal.emit()
                    self.last_click_time = current_time
            
            self.last_mouse_state = current_mouse_state
            
        except Exception as e:
            # Silently ignore errors to avoid spam
            pass
    
    def take_screenshot(self):
        """Take a screenshot with mouse position indicator"""
        if not self.is_recording:
            print("Not recording, ignoring screenshot request")
            return
            
        current_time = datetime.now().timestamp()
        if current_time - self.last_screenshot_time < self.screenshot_cooldown:
            print("Screenshot cooldown active, ignoring request")
            return
            
        try:
            print("Executing screenshot...")
            # Get current mouse position
            mouse_x, mouse_y = pyautogui.position()
            
            # Take screenshot
            screenshot = pyautogui.screenshot()
            
            # Convert to PIL Image if it's not already
            if not isinstance(screenshot, Image.Image):
                screenshot = Image.frombytes('RGB', screenshot.size, screenshot.rgb)
            
            # Draw circle at mouse position using settings
            draw = ImageDraw.Draw(screenshot)
            circle_radius = self.settings.get('circle_size', 20)
            
            # Convert hex color to RGB tuple
            circle_color_hex = self.settings.get('circle_color', '#FF0000')
            circle_color = self.hex_to_rgb(circle_color_hex)
            
            draw.ellipse([
                mouse_x - circle_radius, mouse_y - circle_radius,
                mouse_x + circle_radius, mouse_y + circle_radius
            ], outline=circle_color, width=3)
            
            # Save screenshot
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            screenshot_path = self.current_session_folder / f"screenshot_{timestamp}.png"
            screenshot.save(str(screenshot_path))
            
            self.last_screenshot_time = datetime.now().timestamp()
            print(f"Screenshot saved successfully: {screenshot_path}")
            
        except Exception as e:
            print(f"Screenshot error: {str(e)}")
            import traceback
            traceback.print_exc()
    
    def hex_to_rgb(self, hex_color):
        """Convert hex color to RGB tuple"""
        try:
            # Remove # if present
            hex_color = hex_color.lstrip('#')
            # Convert to RGB
            return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        except:
            # Default to red if conversion fails
            return (255, 0, 0)
    
    def start_recording(self, settings):
        """Start recording session"""
        self.is_recording = True
        self.settings = settings  # Store settings for screenshot function
        self.create_session_folder()
        self.setup_hotkeys(settings)
        return self.current_session_folder
    
    def stop_recording(self):
        """Stop recording and cleanup"""
        if not self.is_recording:
            return 0
            
        self.is_recording = False
        
        # Cleanup keyboard hooks
        try:
            keyboard.unhook_all()
            print("Keyboard hooks cleaned up")
        except Exception as e:
            print(f"Error cleaning up hotkeys: {e}")
        
        # Cleanup mouse detection
        self.cleanup_mouse_detection()
        
        # Count screenshots
        screenshot_count = len(list(self.current_session_folder.glob("*.png"))) if self.current_session_folder else 0
        return screenshot_count
    
    def cleanup_mouse_detection(self):
        """Clean up mouse detection resources"""
        try:
            # Stop pynput mouse listener if it exists
            if hasattr(self, 'mouse_listener') and self.mouse_listener:
                self.mouse_listener.stop()
                print("Mouse listener stopped")
        except Exception as e:
            print(f"Error stopping mouse listener: {e}")
        
        try:
            # Stop mouse timer if it exists
            if hasattr(self, 'mouse_timer') and self.mouse_timer:
                self.mouse_timer.stop()
                print("Mouse timer stopped")
        except Exception as e:
            print(f"Error stopping mouse timer: {e}")
    
    def get_screenshot_count(self):
        """Get current screenshot count"""
        if self.current_session_folder and self.current_session_folder.exists():
            return len(list(self.current_session_folder.glob("*.png")))
        return 0 