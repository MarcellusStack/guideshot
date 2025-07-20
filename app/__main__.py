import sys
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QPushButton, QVBoxLayout, 
    QWidget, QMessageBox
)
from PySide6.QtCore import Qt

# Import our custom modules
from .settings import SettingsManager
from .dialogs import KeySettingsDialog
from .recorder import ScreenshotRecorder

class GuideShot(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("GuideShot v0.1")
        self.setGeometry(100, 100, 800, 600)
        
        # Initialize components
        self.settings_manager = SettingsManager()
        self.settings = self.settings_manager.load_settings()
        self.recorder = ScreenshotRecorder()
        
        # Setup UI
        self.setup_ui()
        
        # Connect recorder signals
        self.recorder.screenshot_signal.connect(self.recorder.take_screenshot)
        self.recorder.stop_signal.connect(self.stop_recording_from_hotkey)
    
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
    
    def start_recording(self):
        # Update UI
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.set_key_button.setEnabled(False)
        
        # Start recording
        session_folder = self.recorder.start_recording(self.settings)
        
        # Minimize the window
        self.showMinimized()
        
        # Show start message
        mouse_status = "Enabled" if self.settings.get('mouse_click_enabled', False) else "Disabled"
        QMessageBox.information(None, "Recording Started", 
            f"Recording started!\n\n"
            f"Screenshot Key: {self.settings.get('screenshot_key', 'Space')}\n"
            f"Stop Key: {self.settings.get('stop_key', 'Esc')}\n"
            f"Mouse clicks: {mouse_status}\n\n"
            f"Screenshots will be saved in: {session_folder}\n\n"
            f"The window will be minimized.")
    
    def stop_recording_from_hotkey(self):
        """Called when stop hotkey is pressed"""
        if not self.recorder.is_recording:
            return
            
        print("Stopping recording (from hotkey signal)...")
        
        # Stop recording and get count
        screenshot_count = self.recorder.stop_recording()
        
        # Update UI
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.set_key_button.setEnabled(True)
        self.showNormal()
        self.activateWindow()
        
        # Show summary
        try:
            print(f"Recording stopped via hotkey. Screenshots taken: {screenshot_count}")
            QMessageBox.information(None, "Recording Stopped", 
                f"Recording stopped!\n\n"
                f"Screenshots taken: {screenshot_count}\n"
                f"Saved in: {self.recorder.current_session_folder}")
        except Exception as e:
            print(f"Error showing summary: {e}")
    
    def stop_recording(self):
        """Called when stop button is pressed"""
        if not self.recorder.is_recording:
            return
            
        print("Stopping recording (from button)...")
        
        # Stop recording and get count
        screenshot_count = self.recorder.stop_recording()
        
        # Update UI
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.set_key_button.setEnabled(True)
        self.showNormal()
        self.activateWindow()
        
        # Show summary
        try:
            print(f"Recording stopped via button. Screenshots taken: {screenshot_count}")
            QMessageBox.information(None, "Recording Stopped", 
                f"Recording stopped!\n\n"
                f"Screenshots taken: {screenshot_count}\n"
                f"Saved in: {self.recorder.current_session_folder}")
        except Exception as e:
            print(f"Error showing summary: {str(e)}")
            QMessageBox.warning(None, "Error", "Recording stopped, but there was an error showing the summary.")
    
    def open_key_settings(self):
        dialog = KeySettingsDialog(self)
        if dialog.exec() == QDialog.Accepted:
            # Reload settings after dialog closes
            self.settings = self.settings_manager.load_settings()
    
    def closeEvent(self, event):
        if self.recorder.is_recording:
            self.stop_recording()
        event.accept()

def main():
    app = QApplication(sys.argv)
    window = GuideShot()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
