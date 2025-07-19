import sys
import json
from pathlib import Path
from datetime import datetime
import pyautogui
import keyboard
from PIL import Image, ImageDraw
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QPushButton, QVBoxLayout, 
    QWidget, QDialog, QLabel, QMessageBox
)
from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QShortcut, QKeySequence

class KeyCaptureDialog(QDialog):
    def __init__(self, key_type, parent=None):
        super().__init__(parent)
        self.key_type = key_type
        self.setWindowTitle("Set Key")
        self.setFixedSize(300, 100)
        
        layout = QVBoxLayout(self)
        self.label = QLabel(f"Press any key to set as {key_type.replace('_', ' ')}...")
        layout.addWidget(self.label)
        
        self.selected_key = None
        
    def keyPressEvent(self, event):
        # Get the key that was pressed
        key = event.key()
        
        # Handle special keys
        if key == Qt.Key.Key_Space:
            self.selected_key = "space"
        elif key == Qt.Key.Key.Key_Escape:
            self.selected_key = "esc"
        elif key == Qt.Key.Key_Return or key == Qt.Key.Key_Enter:
            self.selected_key = "enter"
        else:
            # For regular keys, use the text
            text = event.text()
            if text:
                self.selected_key = text.lower()
        
        if self.selected_key:
            self.accept()

class KeySettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Key Settings")
        self.setFixedSize(400, 300)
        
        # Load current settings
        self.settings = self.load_settings()
        
        # Setup UI
        layout = QVBoxLayout(self)
        
        # Add labels to show current keys
        self.stop_key_label = QLabel(f"Current Stop Key: {self.settings.get('stop_key', 'Esc')}")
        self.screenshot_key_label = QLabel(f"Current Screenshot Key: {self.settings.get('screenshot_key', 'Space')}")
        layout.addWidget(self.stop_key_label)
        layout.addWidget(self.screenshot_key_label)
        
        # Add buttons
        self.set_stop_key_btn = QPushButton("Set Stop Recording Key")
        self.set_screenshot_key_btn = QPushButton("Set Screenshot Key")
        layout.addWidget(self.set_stop_key_btn)
        layout.addWidget(self.set_screenshot_key_btn)
        
        # Add close button
        self.close_btn = QPushButton("Close")
        layout.addWidget(self.close_btn)
        
        # Add stretches for better layout
        layout.insertStretch(0, 1)
        layout.addStretch(1)
        
        # Connect buttons
        self.set_stop_key_btn.clicked.connect(lambda: self.set_key('stop_key'))
        self.set_screenshot_key_btn.clicked.connect(lambda: self.set_key('screenshot_key'))
        self.close_btn.clicked.connect(self.accept)
        
    def set_key(self, key_type):
        dialog = KeyCaptureDialog(key_type, self)
        if dialog.exec() == QDialog.Accepted and dialog.selected_key:
            # Update settings
            self.settings[key_type] = dialog.selected_key
            self.save_settings()
            
            # Update label
            if key_type == 'stop_key':
                self.stop_key_label.setText(f"Current Stop Key: {dialog.selected_key}")
            else:
                self.screenshot_key_label.setText(f"Current Screenshot Key: {dialog.selected_key}")
    
    def load_settings(self):
        settings_file = Path("settings.json")
        if settings_file.exists():
            try:
                with open(settings_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        return {'stop_key': 'Esc', 'screenshot_key': 'Space'}
    
    def save_settings(self):
        with open("settings.json", 'w') as f:
            json.dump(self.settings, f)

class GuideShot(QMainWindow):
    # Define Qt signals for thread-safe communication
    screenshot_signal = Signal()
    stop_signal = Signal()
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("GuideShot v0.1")
        self.setGeometry(100, 100, 800, 600)
        
        # Load settings
        self.settings = self.load_settings()
        
        # Initialize recording state
        self.is_recording = False
        self.screenshots_folder = Path("screenshots")
        self.screenshots_folder.mkdir(exist_ok=True)
        
        # Setup UI
        self.setup_ui()
        
        # Setup screenshot timer (to prevent multiple screenshots at once)
        self.last_screenshot_time = 0
        self.screenshot_cooldown = 0.5  # seconds
        self.last_mouse_state = False
        
        # Connect signals to slots for thread-safe operation
        self.screenshot_signal.connect(self.take_screenshot)
        self.stop_signal.connect(self.stop_recording_from_hotkey)
    
    def setup_ui(self):
        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Create buttons
        self.start_button = QPushButton("Start Capturing")
        self.stop_button = QPushButton("Stop Capturing")
        self.set_key_button = QPushButton("Set Keys")
        self.close_button = QPushButton("Close")
        
        # Add buttons to layout
        layout.addWidget(self.start_button)
        layout.addWidget(self.stop_button)
        layout.addWidget(self.set_key_button)
        layout.addWidget(self.close_button)
        
        # Add some spacing to push buttons to the center
        layout.addStretch(1)
        layout.insertStretch(0, 1)
        
        # Connect buttons
        self.close_button.clicked.connect(self.close)
        self.set_key_button.clicked.connect(self.open_key_settings)
        self.start_button.clicked.connect(self.start_recording)
        self.stop_button.clicked.connect(self.stop_recording)
        
        # Initial button states
        self.stop_button.setEnabled(False)

    def check_mouse(self):
        if not self.is_recording:
            return
        
        try:
            # Use PyAutoGUI's native mouseDown function to check if left button is pressed
            # This is cross-platform and works on Windows, macOS, and Linux
            current_mouse_state = False
            try:
                # Check if we can detect a mouse press by trying to get button state
                # We'll use a simple approach: check if mouse position changed recently
                current_pos = pyautogui.position()
                
                # For now, let's disable automatic mouse click detection
                # and only rely on keyboard shortcuts to avoid focus issues
                # Users can still use the screenshot key instead
                pass
                
            except Exception:
                pass
            
        except Exception as e:
            print(f"Mouse check error: {e}")
    
    def setup_global_hotkeys(self):
        keyboard.unhook_all()
        
        # Use a simple approach with direct key bindings
        try:
            screenshot_key = self.settings.get('screenshot_key', 'space').lower()
            stop_key = self.settings.get('stop_key', 'esc').lower()
            
            print(f"Setting up hotkeys: Screenshot='{screenshot_key}', Stop='{stop_key}'")
            
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
            
            # Add hotkeys with error handling
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
        
        # Disable mouse detection for now to avoid conflicts
        print("Mouse click detection disabled to avoid conflicts.")
        print("Use keyboard shortcuts for all actions.")
    
    def stop_recording_from_hotkey(self):
        """Thread-safe stop for hotkey - called via Qt signal"""
        if not self.is_recording:
            print("Already stopped, ignoring stop request")
            return
            
        print("Stopping recording (from hotkey signal)...")
        self.is_recording = False
        
        # Cleanup hotkeys first
        try:
            keyboard.unhook_all()
            print("Hotkeys cleaned up")
        except Exception as e:
            print(f"Error cleaning up hotkeys: {e}")
        
        # Update UI (now safe because we're in the main thread)
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.set_key_button.setEnabled(True)
        self.showNormal()
        self.activateWindow()
        
        # Count screenshots and show summary
        try:
            screenshot_count = len(list(self.current_session_folder.glob("*.png")))
            print(f"Recording stopped via hotkey. Screenshots taken: {screenshot_count}")
            
            QMessageBox.information(None, "Recording Stopped", 
                f"Recording stopped!\n\n"
                f"Screenshots taken: {screenshot_count}\n"
                f"Saved in: {self.current_session_folder}")
        except Exception as e:
            print(f"Error showing summary: {e}")
    
    def take_screenshot(self):
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
            
            # Draw circle at mouse position
            draw = ImageDraw.Draw(screenshot)
            circle_radius = 20
            circle_color = (255, 0, 0)  # Red
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
    
    def start_recording(self):
        self.is_recording = True
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.set_key_button.setEnabled(False)
        
        # Create a new folder for this recording session
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.current_session_folder = self.screenshots_folder / f"session_{timestamp}"
        self.current_session_folder.mkdir(exist_ok=True)
        
        print(f"Starting recording with keys: Screenshot='{self.settings.get('screenshot_key', 'space')}', Stop='{self.settings.get('stop_key', 'esc')}'")
        
        # Setup global hotkeys
        self.setup_global_hotkeys()
        
        # Minimize the window
        self.showMinimized()
        
        QMessageBox.information(None, "Recording Started", 
            f"Recording started!\n\n"
            f"Screenshot Key: {self.settings.get('screenshot_key', 'Space')}\n"
            f"Stop Key: {self.settings.get('stop_key', 'Esc')}\n"
            f"Mouse clicks: Currently disabled\n\n"
            f"Screenshots will be saved in: {self.current_session_folder}\n\n"
            f"The window will be minimized.")
    
    def stop_recording(self):
        """Regular stop_recording for button clicks"""
        if not self.is_recording:
            print("Already stopped, ignoring stop request")
            return
            
        print("Stopping recording (from button)...")
        self.is_recording = False
        
        # Cleanup hotkeys
        try:
            keyboard.unhook_all()
            print("Hotkeys cleaned up")
        except Exception as e:
            print(f"Error cleaning up hotkeys: {e}")
        
        # Update UI immediately (safe for button clicks)
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.set_key_button.setEnabled(True)
        
        # Restore window
        self.showNormal()
        self.activateWindow()
        
        # Show summary
        try:
            screenshot_count = len(list(self.current_session_folder.glob("*.png")))
            print(f"Recording stopped via button. Screenshots taken: {screenshot_count}")
            QMessageBox.information(None, "Recording Stopped", 
                f"Recording stopped!\n\n"
                f"Screenshots taken: {screenshot_count}\n"
                f"Saved in: {self.current_session_folder}")
        except Exception as e:
            print(f"Error showing summary: {str(e)}")
            QMessageBox.warning(None, "Error", "Recording stopped, but there was an error showing the summary.")
    
    def load_settings(self):
        settings_file = Path("settings.json")
        if settings_file.exists():
            try:
                with open(settings_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        return {'stop_key': 'Esc', 'screenshot_key': 'Space'}
    
    def open_key_settings(self):
        dialog = KeySettingsDialog(self)
        if dialog.exec() == QDialog.Accepted:
            self.settings = self.load_settings()

    def closeEvent(self, event):
        if self.is_recording:
            self.stop_recording()
        keyboard.unhook_all()
        if hasattr(self, 'mouse_timer') and self.mouse_timer is not None:
            self.mouse_timer.stop()
        event.accept()

def main():
    app = QApplication(sys.argv)
    window = GuideShot()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
