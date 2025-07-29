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
        
        # Hide recording overlay
        self.hide_recording_overlay()
        
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
        
        # Show branding image immediately after stopping
        self.show_branding_image_stopped(screenshot_count)
    
    def stop_recording(self):
        """Called when stop button is pressed"""
        if not self.recorder.is_recording:
            return
            
        print("Stopping recording (from button)...")
        
        # Hide recording overlay
        self.hide_recording_overlay()
        
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
        
        # Show branding image immediately after stopping
        self.show_branding_image_stopped(screenshot_count)
    
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
        
        # Show recording overlay
        self.show_recording_overlay()
        
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
    
    def show_recording_overlay(self):
        """Show a red border overlay to indicate recording is active"""
        from app.dialogs import RecordingOverlay
        self.recording_overlay = RecordingOverlay()
        self.recording_overlay.show()
    
    def hide_recording_overlay(self):
        """Hide the recording overlay"""
        if hasattr(self, 'recording_overlay') and self.recording_overlay:
            self.recording_overlay.close()
            self.recording_overlay = None
    
    def show_branding_image(self):
        """Show the branding image immediately when guide is saved"""
        try:
            branding_path = Path("assets/branding.png")
            if branding_path.exists():
                # Create a simple dialog to show the branding image
                from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel
                from PySide6.QtCore import Qt
                
                branding_dialog = QDialog(self)
                branding_dialog.setWindowTitle("GuideShot - Guide Saved")
                branding_dialog.setFixedSize(300, 350)
                branding_dialog.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Window | Qt.WindowType.Tool)
                
                # Center the dialog
                screen = branding_dialog.screen()
                screen_geometry = screen.geometry()
                x = (screen_geometry.width() - branding_dialog.width()) // 2
                y = (screen_geometry.height() - branding_dialog.height()) // 2
                branding_dialog.move(x, y)
                
                layout = QVBoxLayout(branding_dialog)
                layout.setContentsMargins(20, 20, 20, 20)
                
                # Add success message
                success_label = QLabel("✅ Guide Saved Successfully!")
                success_label.setStyleSheet("""
                    QLabel {
                        font-size: 16px;
                        font-weight: bold;
                        color: #27ae60;
                        margin-bottom: 10px;
                    }
                """)
                success_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                layout.addWidget(success_label)
                
                # Add branding image
                branding_label = QLabel()
                pixmap = QPixmap(str(branding_path))
                scaled_pixmap = pixmap.scaled(200, 200, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                branding_label.setPixmap(scaled_pixmap)
                branding_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                branding_label.setFixedSize(200, 200)
                layout.addWidget(branding_label)
                
                # Add instruction text
                instruction_label = QLabel("You can now start taking screenshots!\nPress SPACE to capture.")
                instruction_label.setStyleSheet("""
                    QLabel {
                        font-size: 12px;
                        color: #7f8c8d;
                        margin-top: 10px;
                    }
                """)
                instruction_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                layout.addWidget(instruction_label)
                
                # Auto-close after 3 seconds
                from PySide6.QtCore import QTimer
                QTimer.singleShot(3000, branding_dialog.close)
                
                branding_dialog.show()
                
        except Exception as e:
            print(f"Error showing branding image: {e}")
    
    def show_branding_image_stopped(self, screenshot_count):
        """Show the branding image when recording is stopped, then start processing"""
        try:
            branding_path = Path("assets/branding.png")
            if branding_path.exists():
                # Create a dialog to show the branding image with processing info
                from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton
                from PySide6.QtCore import Qt
                
                branding_dialog = QDialog(self)
                branding_dialog.setWindowTitle("GuideShot - Recording Complete")
                branding_dialog.setFixedSize(350, 250)
                branding_dialog.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Window | Qt.WindowType.Tool)
                
                # Center the dialog
                screen = branding_dialog.screen()
                screen_geometry = screen.geometry()
                x = (screen_geometry.width() - branding_dialog.width()) // 2
                y = (screen_geometry.height() - branding_dialog.height()) // 2
                branding_dialog.move(x, y)
                
                layout = QVBoxLayout(branding_dialog)
                layout.setContentsMargins(20, 20, 20, 20)
                
                # Add completion message
                completion_label = QLabel("✅ Recording Complete!")
                completion_label.setStyleSheet("""
                    QLabel {
                        font-size: 16px;
                        font-weight: bold;
                        color: #27ae60;
                        margin-bottom: 10px;
                    }
                """)
                completion_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                layout.addWidget(completion_label)
                
                # Add screenshot count
                count_label = QLabel(f"📸 {screenshot_count} screenshots captured")
                count_label.setStyleSheet("""
                    QLabel {
                        font-size: 14px;
                        color: #7f8c8d;
                        margin-bottom: 15px;
                    }
                """)
                count_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                layout.addWidget(count_label)
                
                # Add processing message
                processing_label = QLabel("Processing your guide...")
                processing_label.setObjectName("processing_label")  # Set object name for finding
                processing_label.setStyleSheet("""
                    QLabel {
                        font-size: 12px;
                        color: #3498db;
                        margin-top: 10px;
                    }
                """)
                processing_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                layout.addWidget(processing_label)
                
                # Keep this dialog open and start processing in background
                from PySide6.QtCore import QTimer
                def start_processing():
                    # Update the dialog to show processing status
                    processing_label.setText("Creating PDF and video...")
                    processing_label.setStyleSheet("""
                        QLabel {
                            font-size: 12px;
                            color: #3498db;
                            margin-top: 10px;
                        }
                    """)
                    
                    # Start processing in background
                    self.start_background_processing(screenshot_count, branding_dialog)
                
                QTimer.singleShot(2000, start_processing)
                
                branding_dialog.show()
                
        except Exception as e:
            print(f"Error showing branding image: {e}")
            # Fallback to processing dialog
            self.show_processing_dialog(screenshot_count)
    
    def start_background_processing(self, screenshot_count, branding_dialog):
        """Start processing in background and update the branding dialog"""
        try:
            from app.recorder import ScreenshotRecorder
            
            # Create recorder instance for processing
            recorder = ScreenshotRecorder()
            recorder.current_session_folder = self.recorder.current_session_folder
            recorder.settings = self.settings
            recorder.guide_info = self.recorder.guide_info
            
            # Process PDF if enabled
            if self.settings.get('create_pdf', False) and screenshot_count > 0:
                try:
                    branding_dialog.findChild(QLabel, "processing_label").setText("Creating PDF...")
                    pdf_path = recorder.create_pdf_from_guides()
                    branding_dialog.findChild(QLabel, "processing_label").setText("PDF created successfully!")
                except Exception as e:
                    branding_dialog.findChild(QLabel, "processing_label").setText(f"PDF creation failed: {str(e)}")
                    print(f"Error creating PDF: {e}")
            
            # Process video if enabled
            if self.settings.get('create_video', False) and screenshot_count > 0:
                try:
                    branding_dialog.findChild(QLabel, "processing_label").setText("Creating video...")
                    video_path = recorder.create_video_from_guides()
                    branding_dialog.findChild(QLabel, "processing_label").setText("Video created successfully!")
                except Exception as e:
                    branding_dialog.findChild(QLabel, "processing_label").setText(f"Video creation failed: {str(e)}")
                    print(f"Error creating video: {e}")
            
            # Show completion message
            branding_dialog.findChild(QLabel, "processing_label").setText("✅ All processing completed!")
            branding_dialog.findChild(QLabel, "processing_label").setStyleSheet("""
                QLabel {
                    font-size: 12px;
                    color: #27ae60;
                    margin-top: 10px;
                }
            """)
            
            # Close dialog after 2 seconds
            from PySide6.QtCore import QTimer
            QTimer.singleShot(2000, branding_dialog.close)
            
        except Exception as e:
            print(f"Error in background processing: {e}")
            branding_dialog.findChild(QLabel, "processing_label").setText(f"Processing error: {str(e)}")
            # Close dialog after 3 seconds on error
            from PySide6.QtCore import QTimer
            QTimer.singleShot(3000, branding_dialog.close)
    
    def show_processing_dialog(self, screenshot_count):
        """Show processing dialog while creating PDF/video"""
        from app.dialogs import ProcessingDialog
        self.processing_dialog = ProcessingDialog(screenshot_count, self.recorder.current_session_folder, self.settings, self.recorder.guide_info)
        self.processing_dialog.set_processing_finished_callback(self.on_processing_finished)
        self.processing_dialog.show()
    
    def on_processing_finished(self, success, message):
        """Called when processing is finished"""
        if success:
            print(f"Processing completed successfully: {message}")
        else:
            print(f"Processing failed: {message}")
            QMessageBox.warning(None, "Processing Error", f"Error during processing:\n{message}")
    
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
