from PySide6.QtWidgets import (
    QDialog, QLabel, QPushButton, QVBoxLayout, QCheckBox, 
    QHBoxLayout, QSpinBox, QColorDialog, QLineEdit, QTextEdit, QDoubleSpinBox
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
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