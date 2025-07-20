import sys
from pathlib import Path
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QPushButton, QVBoxLayout, 
    QWidget, QMessageBox, QLabel
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap

# Import our custom modules
from .settings import SettingsManager
from .dialogs import KeySettingsDialog
from .recorder import ScreenshotRecorder

class GuideShot(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("GuideShot v0.1")
        # Set window size to 800x600 as requested
        self.setGeometry(100, 100, 800, 600)
        self.setMinimumSize(600, 450)  # Prevent window from being too small
        
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
        layout.setSpacing(12)  # Reduced spacing for 600px height
        layout.setContentsMargins(30, 20, 30, 20)  # Reduced margins
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)  # Center all content
        
        # Add app title
        title_label = QLabel("GuideShot")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("""
            QLabel {
                font-size: 28px;
                font-weight: bold;
                color: #2c3e50;
                margin-bottom: 2px;
            }
        """)
        layout.addWidget(title_label)
        
        # Add version number directly under title
        version_label = QLabel("v0.1")
        version_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        version_label.setStyleSheet("""
            QLabel {
                font-size: 16px;
                color: #7f8c8d;
                margin-bottom: 10px;
            }
        """)
        layout.addWidget(version_label)
        
        # Add branding image with fixed size
        try:
            branding_path = Path("assets/branding.png")
            if branding_path.exists():
                branding_label = QLabel()
                pixmap = QPixmap(str(branding_path))
                # Smaller fixed size for better proportion (220x220)
                scaled_pixmap = pixmap.scaled(220, 220, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                branding_label.setPixmap(scaled_pixmap)
                branding_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                branding_label.setFixedSize(220, 220)  # Fixed size container
                branding_label.setContentsMargins(0, 5, 0, 5)  # Reduced margin around the image
                layout.addWidget(branding_label)
            else:
                print("Branding image not found at assets/branding.png")
        except Exception as e:
            print(f"Error loading branding image: {e}")
        
       
        
        
        # Create buttons with better styling
        button_style = """
            QPushButton {
                font-size: 14px;
                padding: 8px 24px;
                border: 2px solid #3498db;
                border-radius: 6px;
                background-color: #3498db;
                color: white;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
                border-color: #2980b9;
            }
            QPushButton:pressed {
                background-color: #21618c;
            }
            QPushButton:disabled {
                background-color: #bdc3c7;
                border-color: #bdc3c7;
                color: #7f8c8d;
            }
        """
        
        self.start_button = QPushButton("Start Capturing")
        self.stop_button = QPushButton("Stop Capturing")
        self.set_key_button = QPushButton("Set Keys")
        self.close_button = QPushButton("Close")
        
        # Apply styling to buttons
        for button in [self.start_button, self.stop_button, self.set_key_button, self.close_button]:
            button.setStyleSheet(button_style)
            button.setMinimumHeight(35)  # Made buttons shorter
            button.setMaximumHeight(35)  # Ensure consistent height
            button.setFixedWidth(200)  # Fixed width so buttons don't span full screen
        
        # Different style for close button
        self.close_button.setStyleSheet("""
            QPushButton {
                font-size: 14px;
                padding: 8px 24px;
                border: 2px solid #e74c3c;
                border-radius: 6px;
                background-color: #e74c3c;
                color: white;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #c0392b;
                border-color: #c0392b;
            }
            QPushButton:pressed {
                background-color: #a93226;
            }
        """)
        
        # Add buttons to layout with spacing and center alignment
        layout.addWidget(self.start_button, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.stop_button, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.set_key_button, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addSpacing(10)  # Reduced space before close button
        layout.addWidget(self.close_button, alignment=Qt.AlignmentFlag.AlignCenter)
        
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
