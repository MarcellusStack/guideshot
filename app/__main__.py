import sys
from pathlib import Path
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QPushButton, QVBoxLayout, 
    QWidget, QMessageBox, QLabel, QInputDialog, QDialog
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap

# Import our custom modules
from app.settings import SettingsManager
from app.dialogs import KeySettingsDialog, GuideInfoDialog
from app.recorder import ScreenshotRecorder

class GuideShot(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("GuideShot v0.2")
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
        version_label = QLabel("v0.2")
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
        self.set_key_button = QPushButton("Settings")
        self.show_guides_button = QPushButton("Show Guides")
        self.close_button = QPushButton("Close")
        
        # Apply styling to buttons
        for button in [self.start_button, self.stop_button, self.set_key_button, self.show_guides_button, self.close_button]:
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
        layout.addWidget(self.show_guides_button, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addSpacing(10)  # Reduced space before close button
        layout.addWidget(self.close_button, alignment=Qt.AlignmentFlag.AlignCenter)
        
        # Connect buttons
        self.close_button.clicked.connect(self.close)
        self.set_key_button.clicked.connect(self.open_key_settings)
        self.show_guides_button.clicked.connect(self.show_guides)
        self.start_button.clicked.connect(self.start_recording)
        self.stop_button.clicked.connect(self.stop_recording)
        
        # Initial button states
        self.stop_button.setEnabled(False)
    
    def start_recording(self):
        # Get guide name and caption from user
        dialog = GuideInfoDialog(self)
        if dialog.exec() != QDialog.Accepted:
            return
        
        guide_info = dialog.get_guide_info()
        
        # Validate input
        if not guide_info['name']:
            QMessageBox.warning(self, "Invalid Input", "Please enter a guide name.")
            return
        
        # Clean the guide name (remove invalid characters for folder names)
        guide_name = self.clean_session_name(guide_info['name'])
        
        # Update UI
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.set_key_button.setEnabled(False)
        
        # Start recording with guide info
        session_folder = self.recorder.start_recording(self.settings, guide_name, guide_info)
        
        # Show countdown screen immediately (don't minimize yet)
        self.show_countdown_screen(guide_info['name'])
    
    def clean_session_name(self, name):
        """Clean session name to make it safe for folder names"""
        import re
        # Replace spaces with underscores and remove invalid characters
        name = re.sub(r'[<>:"/\\|?*]', '', name)  # Remove invalid Windows chars
        name = re.sub(r'\s+', '_', name)  # Replace spaces with underscores
        name = name.lower()  # Convert to lowercase
        # Ensure it's not empty after cleaning
        if not name:
            name = "session"
        return name
    
    def stop_recording_from_hotkey(self):
        """Called when stop hotkey is pressed"""
        if not self.recorder.is_recording:
            return
            
        print("Stopping recording (from hotkey signal)...")
        
        # Reload settings before stopping (in case they were changed)
        self.settings = self.settings_manager.load_settings()
        
        # Stop recording and get count
        screenshot_count = self.recorder.stop_recording(self.settings)
        
        # Update UI
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.set_key_button.setEnabled(True)
        self.showNormal()
        self.activateWindow()
        
        # Show summary
        try:
            print(f"Recording stopped via hotkey. Guides taken: {screenshot_count}")
            
            # Check if PDF was created
            pdf_status = ""
            if self.settings.get('create_pdf', False):
                pdf_file = self.recorder.current_session_folder / f"{self.recorder.current_session_folder.name}.pdf"
                if pdf_file.exists():
                    pdf_status = f"\nPDF created: {pdf_file.name}"
                else:
                    pdf_status = "\nPDF creation failed"
            
            # Check if video was created
            video_status = ""
            if self.settings.get('create_video', False):
                video_file = self.recorder.current_session_folder / f"{self.recorder.current_session_folder.name}.mp4"
                if video_file.exists():
                    video_status = f"\nVideo created: {video_file.name}"
                else:
                    video_status = "\nVideo creation failed"
            
            QMessageBox.information(None, "Recording Stopped", 
                f"Recording stopped!\n\n"
                f"Guides taken: {screenshot_count}\n"
                f"Saved in: {self.recorder.current_session_folder}{pdf_status}{video_status}")
        except Exception as e:
            print(f"Error showing summary: {e}")
    
    def stop_recording(self):
        """Called when stop button is pressed"""
        if not self.recorder.is_recording:
            return
            
        print("Stopping recording (from button)...")
        
        # Reload settings before stopping (in case they were changed)
        self.settings = self.settings_manager.load_settings()
        
        # Stop recording and get count
        screenshot_count = self.recorder.stop_recording(self.settings)
        
        # Update UI
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.set_key_button.setEnabled(True)
        self.showNormal()
        self.activateWindow()
        
        # Show summary
        try:
            print(f"Recording stopped via button. Guides taken: {screenshot_count}")
            
            # Check if PDF was created
            pdf_status = ""
            if self.settings.get('create_pdf', False):
                pdf_file = self.recorder.current_session_folder / f"{self.recorder.current_session_folder.name}.pdf"
                if pdf_file.exists():
                    pdf_status = f"\nPDF created: {pdf_file.name}"
                else:
                    pdf_status = "\nPDF creation failed"
            
            # Check if video was created
            video_status = ""
            if self.settings.get('create_video', False):
                video_file = self.recorder.current_session_folder / f"{self.recorder.current_session_folder.name}.mp4"
                if video_file.exists():
                    video_status = f"\nVideo created: {video_file.name}"
                else:
                    video_status = "\nVideo creation failed"
            
            QMessageBox.information(None, "Recording Stopped", 
                f"Recording stopped!\n\n"
                f"Guides taken: {screenshot_count}\n"
                f"Saved in: {self.recorder.current_session_folder}{pdf_status}{video_status}")
        except Exception as e:
            print(f"Error showing summary: {str(e)}")
            QMessageBox.warning(None, "Error", "Recording stopped, but there was an error showing the summary.")
    
    def open_key_settings(self):
        dialog = KeySettingsDialog(self)
        if dialog.exec() == QDialog.Accepted:
            # Reload settings after dialog closes
            self.settings = self.settings_manager.load_settings()
    
    def show_guides(self):
        """Open the guides window"""
        from app.dialogs import GuidesWindow
        guides_window = GuidesWindow(self)
        guides_window.show()
    
    def show_countdown_screen(self, guide_name):
        """Show countdown screen before recording starts"""
        from app.dialogs import CountdownDialog
        # Create countdown dialog as a separate window (not child of main window)
        self.countdown_dialog = CountdownDialog(guide_name, None)
        self.countdown_dialog.set_countdown_finished_callback(self.on_countdown_finished)
        self.countdown_dialog.set_countdown_canceled_callback(self.on_countdown_canceled)
        self.countdown_dialog.show()
    
    def on_countdown_finished(self):
        """Called when countdown is finished"""
        # Enable screenshot recording
        self.recorder.enable_screenshot_recording()
        
        # Minimize the main window now
        self.showMinimized()
        
        # No additional dialog - just start recording
        print(f"Recording started! Screenshot Key: {self.settings.get('screenshot_key', 'Space')}, Stop Key: {self.settings.get('stop_key', 'Esc')}")
    
    def on_countdown_canceled(self):
        """Called when countdown is canceled"""
        # Reset button states
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.set_key_button.setEnabled(True)
        self.show_guides_button.setEnabled(True)
        
        print("Recording canceled during countdown")
    
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
