from PySide6.QtWidgets import (
    QDialog, QLabel, QPushButton, QVBoxLayout, QCheckBox, 
    QHBoxLayout, QSpinBox, QColorDialog, QLineEdit, QTextEdit, QDoubleSpinBox,
    QListWidget, QListWidgetItem, QScrollArea, QWidget, QFrame
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor
from pathlib import Path
from app.settings import SettingsManager

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
        elif key == Qt.Key.Key_Escape:
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
        self.setWindowTitle("Settings")
        self.setFixedSize(450, 520)  # Made taller for video settings
        
        # Initialize settings manager
        self.settings_manager = SettingsManager()
        self.settings = self.settings_manager.load_settings()
        
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
        
        # Add mouse click checkbox
        self.mouse_click_checkbox = QCheckBox("Enable mouse click for guides")
        self.mouse_click_checkbox.setChecked(self.settings.get('mouse_click_enabled', False))
        layout.addWidget(self.mouse_click_checkbox)
        
        # Add circle size setting
        circle_size_layout = QHBoxLayout()
        circle_size_label = QLabel("Circle Size:")
        self.circle_size_spinbox = QSpinBox()
        self.circle_size_spinbox.setRange(5, 50)  # Min 5px, Max 50px
        self.circle_size_spinbox.setValue(self.settings.get('circle_size', 20))
        self.circle_size_spinbox.setSuffix(" px")
        circle_size_layout.addWidget(circle_size_label)
        circle_size_layout.addWidget(self.circle_size_spinbox)
        circle_size_layout.addStretch()
        layout.addLayout(circle_size_layout)
        
        # Add circle color setting
        circle_color_layout = QHBoxLayout()
        circle_color_label = QLabel("Circle Color:")
        self.circle_color_button = QPushButton()
        self.circle_color_button.setFixedSize(50, 30)
        self.update_color_button()
        circle_color_layout.addWidget(circle_color_label)
        circle_color_layout.addWidget(self.circle_color_button)
        circle_color_layout.addStretch()
        layout.addLayout(circle_color_layout)
        
        # Add PDF creation checkbox
        self.pdf_checkbox = QCheckBox("Create PDF from guides after session")
        self.pdf_checkbox.setChecked(self.settings.get('create_pdf', False))
        layout.addWidget(self.pdf_checkbox)
        
        # Add video creation checkbox
        self.video_checkbox = QCheckBox("Create video from guides after session")
        self.video_checkbox.setChecked(self.settings.get('create_video', False))
        layout.addWidget(self.video_checkbox)
        
        # Add screenshot duration setting
        duration_layout = QHBoxLayout()
        duration_label = QLabel("Screenshot Duration:")
        self.duration_spinbox = QDoubleSpinBox()
        self.duration_spinbox.setRange(0.5, 10.0)  # Min 0.5s, Max 10s
        self.duration_spinbox.setValue(self.settings.get('screenshot_duration', 2.0))
        self.duration_spinbox.setSuffix(" seconds")
        self.duration_spinbox.setDecimals(1)
        self.duration_spinbox.setSingleStep(0.5)
        duration_layout.addWidget(duration_label)
        duration_layout.addWidget(self.duration_spinbox)
        duration_layout.addStretch()
        layout.addLayout(duration_layout)
        
        # Add helper text checkbox
        self.helper_text_checkbox = QCheckBox("Enable helper text under circle")
        self.helper_text_checkbox.setChecked(self.settings.get('helper_text_enabled', False))
        layout.addWidget(self.helper_text_checkbox)
        
        # Add helper text input
        helper_text_layout = QHBoxLayout()
        helper_text_label = QLabel("Helper Text:")
        self.helper_text_input = QLineEdit()
        self.helper_text_input.setText(self.settings.get('helper_text', 'Click here'))
        self.helper_text_input.setPlaceholderText("Enter helper text to display under circle")
        self.helper_text_input.setEnabled(self.settings.get('helper_text_enabled', False))
        helper_text_layout.addWidget(helper_text_label)
        helper_text_layout.addWidget(self.helper_text_input)
        layout.addLayout(helper_text_layout)
        
        # Connect checkbox to enable/disable text input
        self.helper_text_checkbox.toggled.connect(self.helper_text_input.setEnabled)
        
        # Add close button
        self.close_btn = QPushButton("Close")
        layout.addWidget(self.close_btn)
        
        # Add stretches for better layout
        layout.insertStretch(0, 1)
        layout.addStretch(1)
        
        # Connect buttons
        self.set_stop_key_btn.clicked.connect(lambda: self.set_key('stop_key'))
        self.set_screenshot_key_btn.clicked.connect(lambda: self.set_key('screenshot_key'))
        self.mouse_click_checkbox.toggled.connect(self.toggle_mouse_click)
        self.circle_size_spinbox.valueChanged.connect(self.update_circle_size)
        self.circle_color_button.clicked.connect(self.choose_circle_color)
        self.pdf_checkbox.toggled.connect(self.toggle_pdf_creation)
        self.video_checkbox.toggled.connect(self.toggle_video_creation)
        self.duration_spinbox.valueChanged.connect(self.update_screenshot_duration)
        self.helper_text_checkbox.toggled.connect(self.toggle_helper_text)
        self.helper_text_input.textChanged.connect(self.update_helper_text)
        self.close_btn.clicked.connect(self.accept)
        
    def toggle_mouse_click(self, checked):
        self.settings['mouse_click_enabled'] = checked
        self.settings_manager.save_settings(self.settings)
        print(f"Mouse click detection {'enabled' if checked else 'disabled'}")
        
    def update_color_button(self):
        """Update the color button to show current color"""
        color = self.settings.get('circle_color', '#FF0000')
        self.circle_color_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {color};
                border: 2px solid #333;
                border-radius: 4px;
            }}
        """)
    
    def update_circle_size(self, value):
        """Update circle size setting"""
        self.settings['circle_size'] = value
        self.settings_manager.save_settings(self.settings)
        print(f"Circle size updated to: {value}px")
    
    def choose_circle_color(self):
        """Open color picker for circle color"""
        current_color = QColor(self.settings.get('circle_color', '#FF0000'))
        color = QColorDialog.getColor(current_color, self, "Choose Circle Color")
        
        if color.isValid():
            color_hex = color.name()  # Get hex representation
            self.settings['circle_color'] = color_hex
            self.settings_manager.save_settings(self.settings)
            self.update_color_button()
            print(f"Circle color updated to: {color_hex}")
    
    def toggle_pdf_creation(self, checked):
        """Toggle PDF creation setting"""
        self.settings['create_pdf'] = checked
        self.settings_manager.save_settings(self.settings)
        print(f"PDF creation {'enabled' if checked else 'disabled'}")
    
    def toggle_video_creation(self, checked):
        """Toggle video creation setting"""
        self.settings['create_video'] = checked
        self.settings_manager.save_settings(self.settings)
        print(f"Video creation {'enabled' if checked else 'disabled'}")
    
    def update_screenshot_duration(self, value):
        """Update screenshot duration setting"""
        self.settings['screenshot_duration'] = value
        self.settings_manager.save_settings(self.settings)
        print(f"Screenshot duration updated to: {value} seconds")
    
    def toggle_helper_text(self, checked):
        """Toggle helper text setting"""
        self.settings['helper_text_enabled'] = checked
        self.settings_manager.save_settings(self.settings)
        self.helper_text_input.setEnabled(checked)
        print(f"Helper text {'enabled' if checked else 'disabled'}")
    
    def update_helper_text(self, text):
        """Update helper text setting"""
        self.settings['helper_text'] = text
        self.settings_manager.save_settings(self.settings)
        print(f"Helper text updated to: '{text}'")
    
    def set_key(self, key_type):
        dialog = KeyCaptureDialog(key_type, self)
        if dialog.exec() == QDialog.Accepted and dialog.selected_key:
            # Update settings
            self.settings[key_type] = dialog.selected_key
            self.settings_manager.save_settings(self.settings)
            
            # Update label
            if key_type == 'stop_key':
                self.stop_key_label.setText(f"Current Stop Key: {dialog.selected_key}")
            else:
                self.screenshot_key_label.setText(f"Current Screenshot Key: {dialog.selected_key}") 

class GuideInfoDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("New Guide")
        self.setFixedSize(500, 400)
        
        layout = QVBoxLayout(self)
        
        # Guide name section
        name_label = QLabel("Guide Name:")
        name_label.setStyleSheet("font-weight: bold; margin-bottom: 5px;")
        layout.addWidget(name_label)
        
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Enter a name for this guide (e.g., 'Login Feature')")
        self.name_input.setText("feature_demo")  # Default value
        layout.addWidget(self.name_input)
        
        layout.addSpacing(15)
        
        # Caption/description section
        caption_label = QLabel("Caption/Description:")
        caption_label.setStyleSheet("font-weight: bold; margin-bottom: 5px;")
        layout.addWidget(caption_label)
        
        help_label = QLabel("This description will appear on the first page of the PDF:")
        help_label.setStyleSheet("color: #666; font-size: 11px; margin-bottom: 5px;")
        layout.addWidget(help_label)
        
        self.caption_input = QTextEdit()
        self.caption_input.setPlaceholderText("Enter a description for this guide...\n\nExample:\nThis guide demonstrates the login process for new users, including account creation and first-time setup.")
        self.caption_input.setMaximumHeight(150)
        layout.addWidget(self.caption_input)
        
        layout.addSpacing(15)
        
        # Buttons
        button_layout = QHBoxLayout()
        self.cancel_button = QPushButton("Cancel")
        self.ok_button = QPushButton("Start Guide")
        
        button_style = """
            QPushButton {
                font-size: 14px;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
        """
        
        self.cancel_button.setStyleSheet(button_style + """
            border: 2px solid #e74c3c;
            background-color: #e74c3c;
            color: white;
        """)
        
        self.ok_button.setStyleSheet(button_style + """
            border: 2px solid #27ae60;
            background-color: #27ae60;
            color: white;
        """)
        
        button_layout.addStretch()
        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.ok_button)
        layout.addLayout(button_layout)
        
        # Connect buttons
        self.cancel_button.clicked.connect(self.reject)
        self.ok_button.clicked.connect(self.accept)
        
        # Set focus to name input
        self.name_input.setFocus()
    
    def get_guide_info(self):
        """Return the guide name and caption"""
        return {
            'name': self.name_input.text().strip(),
            'caption': self.caption_input.toPlainText().strip()
        }

class GuidesWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("GuideShot - My Guides")
        self.setGeometry(200, 200, 800, 600)
        self.setMinimumSize(600, 400)
        
        # Setup UI
        self.setup_ui()
        self.load_guides()
    
    def setup_ui(self):
        """Setup the guides window UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Title
        title_label = QLabel("My Guides")
        title_label.setStyleSheet("""
            QLabel {
                font-size: 24px;
                font-weight: bold;
                color: #2c3e50;
                margin-bottom: 10px;
            }
        """)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        # Description
        desc_label = QLabel("Click 'Open Folder' to view your guide files (images, PDFs, videos)")
        desc_label.setStyleSheet("""
            QLabel {
                font-size: 12px;
                color: #7f8c8d;
                margin-bottom: 15px;
            }
        """)
        desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(desc_label)
        
        # Guides list
        self.guides_list = QListWidget()
        self.guides_list.setStyleSheet("""
            QListWidget {
                border: 2px solid #bdc3c7;
                border-radius: 6px;
                background-color: white;
                padding: 5px;
            }
            QListWidget::item {
                border-bottom: 1px solid #ecf0f1;
                padding: 10px;
                margin: 2px;
            }
            QListWidget::item:selected {
                background-color: #3498db;
                color: white;
            }
            QListWidget::item:hover {
                background-color: #ecf0f1;
            }
        """)
        layout.addWidget(self.guides_list)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.setStyleSheet("""
            QPushButton {
                font-size: 12px;
                padding: 8px 16px;
                border: 2px solid #3498db;
                border-radius: 4px;
                background-color: #3498db;
                color: white;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
                border-color: #2980b9;
            }
        """)
        
        self.close_button = QPushButton("Close")
        self.close_button.setStyleSheet("""
            QPushButton {
                font-size: 12px;
                padding: 8px 16px;
                border: 2px solid #e74c3c;
                border-radius: 4px;
                background-color: #e74c3c;
                color: white;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #c0392b;
                border-color: #c0392b;
            }
        """)
        
        button_layout.addWidget(self.refresh_button)
        button_layout.addStretch()
        button_layout.addWidget(self.close_button)
        layout.addLayout(button_layout)
        
        # Connect buttons
        self.refresh_button.clicked.connect(self.load_guides)
        self.close_button.clicked.connect(self.close)
    
    def load_guides(self):
        """Load and display all guides from the guides folder"""
        self.guides_list.clear()
        
        try:
            guides_folder = Path("guides")
            if not guides_folder.exists():
                # Create empty state
                item = QListWidgetItem("No guides found. Create your first guide!")
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsSelectable)
                item.setStyleSheet("color: #7f8c8d; font-style: italic;")
                self.guides_list.addItem(item)
                return
            
            # Get all guide folders
            guide_folders = [f for f in guides_folder.iterdir() if f.is_dir()]
            
            if not guide_folders:
                # Create empty state
                item = QListWidgetItem("No guides found. Create your first guide!")
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsSelectable)
                item.setStyleSheet("color: #7f8c8d; font-style: italic;")
                self.guides_list.addItem(item)
                return
            
            # Sort folders by creation time (newest first)
            guide_folders.sort(key=lambda x: x.stat().st_ctime, reverse=True)
            
            for folder in guide_folders:
                self.add_guide_item(folder)
                
        except Exception as e:
            print(f"Error loading guides: {e}")
            item = QListWidgetItem("Error loading guides")
            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsSelectable)
            item.setStyleSheet("color: #e74c3c; font-style: italic;")
            self.guides_list.addItem(item)
    
    def add_guide_item(self, folder_path):
        """Add a guide item to the list"""
        # Create custom widget for the guide item
        item_widget = QWidget()
        item_widget.setMinimumHeight(80)  # Set minimum height for the widget
        item_layout = QHBoxLayout(item_widget)
        item_layout.setContentsMargins(10, 15, 10, 15)  # Increased vertical padding
        item_layout.setSpacing(10)
        
        # Guide info
        info_layout = QVBoxLayout()
        
        # Guide name (folder name without timestamp)
        folder_name = folder_path.name
        # Try to extract the guide name (before the timestamp)
        if '_' in folder_name:
            # Split by underscore and take the first part as guide name
            guide_name = folder_name.split('_')[0]
            # Replace underscores with spaces and capitalize
            guide_name = ' '.join(word.capitalize() for word in guide_name.split('_'))
        else:
            guide_name = folder_name.replace('_', ' ').title()
        
        name_label = QLabel(guide_name)
        name_label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                font-weight: bold;
                color: #2c3e50;
                margin-bottom: 2px;
            }
        """)
        info_layout.addWidget(name_label)
        
        # Folder path and file count
        screenshot_count = len(list(folder_path.glob("*.png")))
        pdf_exists = any(folder_path.glob("*.pdf"))
        video_exists = any(folder_path.glob("*.mp4"))
        
        details = f"📁 {folder_name} • 📸 {screenshot_count} images"
        if pdf_exists:
            details += " • 📄 PDF"
        if video_exists:
            details += " • 🎥 Video"
        
        details_label = QLabel(details)
        details_label.setStyleSheet("""
            QLabel {
                font-size: 11px;
                color: #7f8c8d;
            }
        """)
        info_layout.addWidget(details_label)
        
        item_layout.addLayout(info_layout)
        item_layout.addStretch()
        
        # Open folder button
        open_button = QPushButton("Open Folder")
        open_button.setMinimumHeight(30)  # Ensure button has proper height
        open_button.setStyleSheet("""
            QPushButton {
                font-size: 11px;
                padding: 8px 16px;
                border: 1px solid #3498db;
                border-radius: 3px;
                background-color: #3498db;
                color: white;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
                border-color: #2980b9;
            }
        """)
        open_button.clicked.connect(lambda: self.open_guide_folder(folder_path))
        item_layout.addWidget(open_button)
        
        # Create list item and set the custom widget
        item = QListWidgetItem()
        # Force a larger size hint to ensure full visibility
        size_hint = item_widget.sizeHint()
        size_hint.setHeight(max(80, size_hint.height()))  # Ensure minimum 80px height
        item.setSizeHint(size_hint)
        self.guides_list.addItem(item)
        self.guides_list.setItemWidget(item, item_widget)
    
    def open_guide_folder(self, folder_path):
        """Open the guide folder in the file explorer"""
        try:
            import subprocess
            import platform
            
            if platform.system() == "Windows":
                # Windows explorer returns non-zero exit code even when successful
                # So we don't use check=True and handle the result manually
                result = subprocess.run(["explorer", str(folder_path)], capture_output=True, text=True)
                if result.returncode != 0 and result.stderr:
                    # Only show error if there's actual stderr content
                    raise subprocess.CalledProcessError(result.returncode, result.args, result.stdout, result.stderr)
            elif platform.system() == "Darwin":  # macOS
                subprocess.run(["open", str(folder_path)], check=True)
            else:  # Linux
                subprocess.run(["xdg-open", str(folder_path)], check=True)
                
            print(f"Opened guide folder: {folder_path}")
            
        except Exception as e:
            print(f"Error opening folder: {e}")
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Error", f"Could not open folder:\n{str(e)}")

class CountdownDialog(QDialog):
    def __init__(self, guide_name, parent=None):
        super().__init__(parent)
        self.guide_name = guide_name
        self.countdown_value = 3  # 3 second countdown
        
        # Setup UI
        self.setup_ui()
        self.start_countdown()
        
        # Store callbacks for when countdown finishes or is canceled
        self.countdown_finished_callback = None
        self.countdown_canceled_callback = None
    
    def setup_ui(self):
        """Setup the countdown dialog UI"""
        self.setWindowTitle("GuideShot - Get Ready!")
        self.setFixedSize(500, 450)  # Smaller, more reasonable size
        self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Window | Qt.WindowType.Tool)
        
        # Center the dialog on screen
        screen = self.screen()
        screen_geometry = screen.geometry()
        x = (screen_geometry.width() - self.width()) // 2
        y = (screen_geometry.height() - self.height()) // 2
        self.move(x, y)
        
        # Set focus to this dialog so it appears on top
        self.raise_()
        self.activateWindow()
        
        layout = QVBoxLayout(self)
        layout.setSpacing(25)  # Increased spacing
        layout.setContentsMargins(40, 40, 40, 40)  # Increased margins
        
        # Title
        title_label = QLabel("Get Ready!")
        title_label.setStyleSheet("""
            QLabel {
                font-size: 28px;
                font-weight: bold;
                color: #2c3e50;
                margin-bottom: 10px;
            }
        """)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        # Guide name
        guide_label = QLabel(f"Guide: {self.guide_name}")
        guide_label.setStyleSheet("""
            QLabel {
                font-size: 16px;
                color: #7f8c8d;
                margin-bottom: 20px;
            }
        """)
        guide_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(guide_label)
        
        # Instructions
        instructions_label = QLabel("Recording will start in...")
        instructions_label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                color: #7f8c8d;
                margin-bottom: 10px;
            }
        """)
        instructions_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(instructions_label)
        
        # Countdown number
        self.countdown_label = QLabel(str(self.countdown_value))
        self.countdown_label.setStyleSheet("""
            QLabel {
                font-size: 60px;
                font-weight: bold;
                color: #e74c3c;
                margin: 15px 0;
                padding: 5px;
                min-height: 80px;
            }
        """)
        self.countdown_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.countdown_label)
        
        # Add spacing before cancel button
        layout.addSpacing(50)  # More spacing between number and cancel button
        
        # Cancel button
        self.cancel_button = QPushButton("Cancel Recording")
        self.cancel_button.setStyleSheet("""
            QPushButton {
                font-size: 14px;
                padding: 10px 20px;
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
        """)
        self.cancel_button.clicked.connect(self.cancel_countdown)
        layout.addWidget(self.cancel_button, alignment=Qt.AlignmentFlag.AlignCenter)
    
    def start_countdown(self):
        """Start the countdown timer"""
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_countdown)
        self.timer.start(1000)  # Update every 1 second
    
    def update_countdown(self):
        """Update the countdown display"""
        self.countdown_value -= 1
        
        if self.countdown_value > 0:
            # Update the countdown number
            self.countdown_label.setText(str(self.countdown_value))
        else:
            # Countdown finished
            self.timer.stop()
            if self.countdown_finished_callback:
                self.countdown_finished_callback()
            self.close()
    
    def cancel_countdown(self):
        """Cancel the countdown and stop recording"""
        self.timer.stop()
        # Stop recording if it was started
        # Since we're not a child of main window, we need to find the main window differently
        from PySide6.QtWidgets import QApplication
        app = QApplication.instance()
        for widget in app.topLevelWidgets():
            if hasattr(widget, 'recorder') and widget.recorder.is_recording:
                widget.recorder.stop_recording()
                break
        
        # Call the canceled callback if set
        if self.countdown_canceled_callback:
            self.countdown_canceled_callback()
        
        self.close()
    
    def set_countdown_finished_callback(self, callback):
        """Set the callback function to call when countdown finishes"""
        self.countdown_finished_callback = callback
    
    def set_countdown_canceled_callback(self, callback):
        """Set the callback function to call when countdown is canceled"""
        self.countdown_canceled_callback = callback 