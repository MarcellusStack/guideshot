from PySide6.QtWidgets import (
    QDialog, QLabel, QPushButton, QVBoxLayout, QCheckBox
)
from PySide6.QtCore import Qt
from .settings import SettingsManager

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
        self.setWindowTitle("Key Settings")
        self.setFixedSize(400, 350)
        
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
        self.mouse_click_checkbox = QCheckBox("Enable mouse click for screenshots")
        self.mouse_click_checkbox.setChecked(self.settings.get('mouse_click_enabled', False))
        layout.addWidget(self.mouse_click_checkbox)
        
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
        self.close_btn.clicked.connect(self.accept)
        
    def toggle_mouse_click(self, checked):
        self.settings['mouse_click_enabled'] = checked
        self.settings_manager.save_settings(self.settings)
        print(f"Mouse click detection {'enabled' if checked else 'disabled'}")
        
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