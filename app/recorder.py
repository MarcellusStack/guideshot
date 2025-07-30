import keyboard
from datetime import datetime
from pathlib import Path
import pyautogui
from PIL import Image, ImageDraw
from PySide6.QtCore import QObject, Signal, QTimer
from app.voice_manager import VoiceManager

class ScreenshotRecorder(QObject):
    """Handles screenshot recording functionality"""
    
    # Qt signals for thread-safe communication
    screenshot_signal = Signal()
    stop_signal = Signal()
    
    def __init__(self):
        super().__init__()
        self.is_recording = False
        self.screenshot_recording_enabled = False  # New flag to control screenshot recording
        self.screenshots_folder = Path("guides")
        self.screenshots_folder.mkdir(exist_ok=True)
        self.current_session_folder = None
        
        # Screenshot timing
        self.last_screenshot_time = 0
        self.screenshot_cooldown = 0.5  # seconds
        
        # Mouse detection
        self.last_mouse_state = False
        self.mouse_timer = None
        self.mouse_listener = None
        
        # Voice recording
        self.voice_manager = VoiceManager()
        self.is_voice_recording = False
        self.is_voice_key_held = False  # Track if voice key is currently being held
        self.screenshot_counter = 0  # Track screenshot number for voice data
    
    def create_session_folder(self, session_name=None):
        """Create a new session folder for guides"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if session_name:
            # Use custom name with timestamp
            folder_name = f"{session_name}_{timestamp}"
        else:
            # Fallback to default naming
            folder_name = f"session_{timestamp}"
            
        self.current_session_folder = self.screenshots_folder / folder_name
        self.current_session_folder.mkdir(exist_ok=True)
        return self.current_session_folder
    
    def setup_hotkeys(self, settings):
        """Setup keyboard hotkeys for recording"""
        keyboard.unhook_all()
        
        try:
            screenshot_key = settings.get('screenshot_key', 'space').lower()
            stop_key = settings.get('stop_key', 'esc').lower()
            mouse_enabled = settings.get('mouse_click_enabled', False)
            voice_enabled = settings.get('voice_enabled', False)
            voice_key = settings.get('voice_key', 'v').lower()
            
            print(f"Setting up hotkeys: Screenshot='{screenshot_key}', Stop='{stop_key}', Mouse={mouse_enabled}, Voice={voice_enabled}")
            
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
            
            def voice_press_wrapper():
                if self.is_recording and voice_enabled and not self.is_voice_key_held:
                    print(f"Voice key '{voice_key}' pressed - starting voice recording...")
                    self.is_voice_key_held = True
                    self.start_voice_recording()
                elif self.is_voice_key_held:
                    # Key is being held down (repeat), ignore
                    pass
            
            def voice_release_wrapper():
                if self.is_recording and voice_enabled and self.is_voice_key_held:
                    print(f"Voice key '{voice_key}' released - stopping voice recording and taking screenshot...")
                    self.is_voice_key_held = False
                    self.stop_voice_recording_and_screenshot()
            
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
            
            # Setup voice recording hotkeys if enabled
            if voice_enabled:
                try:
                    keyboard.on_press_key(voice_key, lambda _: voice_press_wrapper())
                    keyboard.on_release_key(voice_key, lambda _: voice_release_wrapper())
                    print(f"Voice hotkey '{voice_key}' registered (hold to record)")
                except Exception as e:
                    print(f"Failed to register voice hotkeys: {e}")
                
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
            
        if not self.screenshot_recording_enabled:
            print("Screenshot recording not yet enabled (countdown in progress), ignoring request")
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
            circle_radius = self.settings.get('circle_size', 20)
            
            # Convert hex color to RGB tuple
            circle_color_hex = self.settings.get('circle_color', '#FF0000')
            circle_color = self.hex_to_rgb(circle_color_hex)
            
            # Create a transparent overlay for the inner circle
            overlay = Image.new('RGBA', screenshot.size, (0, 0, 0, 0))
            overlay_draw = ImageDraw.Draw(overlay)
            
            # Draw inner filled circle with reduced opacity (40% of original)
            inner_color = (*circle_color, 102)  # RGBA with 40% opacity (102/255)
            overlay_draw.ellipse([
                mouse_x - circle_radius, mouse_y - circle_radius,
                mouse_x + circle_radius, mouse_y + circle_radius
            ], fill=inner_color)
            
            # Composite the overlay with the screenshot
            screenshot = screenshot.convert('RGBA')
            screenshot = Image.alpha_composite(screenshot, overlay)
            screenshot = screenshot.convert('RGB')
            
            # Draw outer circle outline on top
            draw = ImageDraw.Draw(screenshot)
            draw.ellipse([
                mouse_x - circle_radius, mouse_y - circle_radius,
                mouse_x + circle_radius, mouse_y + circle_radius
            ], outline=circle_color, width=3)
            
            # Draw helper text if enabled
            if self.settings.get('helper_text_enabled', False):
                helper_text = self.settings.get('helper_text', 'Click here')
                if helper_text.strip():  # Only draw if text is not empty
                    self.draw_helper_text(screenshot, mouse_x, mouse_y, circle_radius, helper_text)
            
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
    
    def draw_helper_text(self, screenshot, mouse_x, mouse_y, circle_radius, helper_text):
        """Draw helper text with grey background under the circle"""
        try:
            from PIL import ImageFont
            draw = ImageDraw.Draw(screenshot)
            
            # Try to use a better font, fallback to default if not available
            try:
                # Try common system fonts
                font_size = max(12, circle_radius // 2)  # Scale font size with circle
                font = ImageFont.truetype("arial.ttf", font_size)
            except:
                try:
                    font = ImageFont.truetype("Arial.ttf", font_size)
                except:
                    try:
                        font = ImageFont.load_default()
                    except:
                        # Use draw methods without font if all else fails
                        font = None
            
            # Get text dimensions
            if font:
                bbox = draw.textbbox((0, 0), helper_text, font=font)
                text_width = bbox[2] - bbox[0]
                text_height = bbox[3] - bbox[1]
            else:
                # Fallback text size estimation
                text_width = len(helper_text) * 6
                text_height = 11
            
            # Calculate position below the circle with some padding
            padding = 4
            text_x = mouse_x - text_width // 2
            text_y = mouse_y + circle_radius + 8  # 8 pixels below circle
            
            # Ensure text doesn't go off screen edges
            screen_width = screenshot.width
            screen_height = screenshot.height
            
            if text_x < padding:
                text_x = padding
            elif text_x + text_width + padding > screen_width:
                text_x = screen_width - text_width - padding
                
            if text_y + text_height + padding > screen_height:
                text_y = mouse_y - circle_radius - text_height - 8  # Move above circle
            
            # Draw subtle grey background rectangle
            bg_x1 = text_x - padding
            bg_y1 = text_y - padding
            bg_x2 = text_x + text_width + padding
            bg_y2 = text_y + text_height + padding
            
            # Semi-transparent grey background
            overlay = Image.new('RGBA', screenshot.size, (0, 0, 0, 0))
            overlay_draw = ImageDraw.Draw(overlay)
            overlay_draw.rectangle([bg_x1, bg_y1, bg_x2, bg_y2], 
                                 fill=(128, 128, 128, 180))  # Grey with transparency
            
            # Composite overlay with screenshot
            screenshot_rgba = screenshot.convert('RGBA')
            screenshot_with_bg = Image.alpha_composite(screenshot_rgba, overlay)
            screenshot_final = screenshot_with_bg.convert('RGB')
            
            # Copy the modified screenshot back
            screenshot.paste(screenshot_final)
            
            # Draw white text on top
            draw = ImageDraw.Draw(screenshot)
            if font:
                draw.text((text_x, text_y), helper_text, fill=(255, 255, 255), font=font)
            else:
                draw.text((text_x, text_y), helper_text, fill=(255, 255, 255))
                
        except Exception as e:
            print(f"Error drawing helper text: {e}")
            # Silently fail - helper text is optional
    
    def start_recording(self, settings, session_name=None, guide_info=None):
        """Start recording session"""
        self.is_recording = True
        self.screenshot_recording_enabled = False  # Disable screenshot recording initially
        self.settings = settings  # Store settings for screenshot function
        self.guide_info = guide_info  # Store guide information for PDF
        self.create_session_folder(session_name)
        self.setup_hotkeys(settings)
        return self.current_session_folder
    
    def enable_screenshot_recording(self):
        """Enable screenshot recording after countdown"""
        self.screenshot_recording_enabled = True
        print("Screenshot recording enabled - ready to capture!")
    
    def start_voice_recording(self):
        """Start voice recording for current screenshot"""
        if self.is_voice_recording:
            print("Voice recording already in progress")
            return
        
        try:
            # Create audio file path
            self.screenshot_counter += 1
            audio_filename = f"voice_{self.screenshot_counter:03d}.wav"
            audio_path = self.current_session_folder / audio_filename
            
            # Start recording
            self.is_voice_recording = True
            success = self.voice_manager.start_recording(audio_path)
            
            if success:
                print(f"Voice recording started: {audio_path}")
            else:
                print("Failed to start voice recording")
                self.is_voice_recording = False
                self.is_voice_key_held = False
                
        except Exception as e:
            print(f"Error starting voice recording: {e}")
            self.is_voice_recording = False
            self.is_voice_key_held = False
    
    def stop_voice_recording_and_screenshot(self):
        """Stop voice recording and take screenshot with voice data"""
        if not self.is_voice_recording:
            print("No voice recording in progress")
            return
        
        try:
            # Stop voice recording
            audio_file = self.voice_manager.stop_recording()
            self.is_voice_recording = False
            
            if not audio_file:
                print("Voice recording failed")
                return
            
            # Process speech to text if enabled
            text = ""
            if self.settings.get('speech_to_text', True):
                print("Converting speech to text...")
                voice_language = self.settings.get('voice_language', 'de')
                text = self.voice_manager.speech_to_text(audio_file, voice_language)
                print(f"Transcribed text: {text}")
            
            # Generate TTS audio if enabled
            tts_file = None
            if self.settings.get('text_to_speech', True) and text:
                print("Generating TTS audio...")
                tts_filename = f"tts_{self.screenshot_counter:03d}.wav"
                tts_file = self.current_session_folder / tts_filename
                tts_voice = self.settings.get('tts_voice', 'default')
                voice_language = self.settings.get('voice_language', 'de')
                
                success = self.voice_manager.text_to_speech(text, tts_file, tts_voice, voice_language)
                if not success:
                    tts_file = None
                    print("TTS generation failed")
                else:
                    print(f"TTS audio generated: {tts_file}")
            
            # Save voice data
            self.voice_manager.save_voice_data(
                self.current_session_folder,
                self.screenshot_counter,
                audio_file,
                text,
                tts_file
            )
            
            # Take screenshot
            self.take_screenshot_with_voice(text)
            
            print(f"Voice recording and screenshot completed for #{self.screenshot_counter}")
            
        except Exception as e:
            print(f"Error stopping voice recording: {e}")
            self.is_voice_recording = False
            self.is_voice_key_held = False
    
    def take_screenshot_with_voice(self, voice_text=""):
        """Take a screenshot with optional voice text overlay"""
        if not self.is_recording:
            print("Not recording, ignoring screenshot request")
            return
            
        if not self.screenshot_recording_enabled:
            print("Screenshot recording not yet enabled (countdown in progress), ignoring request")
            return
            
        current_time = datetime.now().timestamp()
        if current_time - self.last_screenshot_time < self.screenshot_cooldown:
            print("Screenshot cooldown active, ignoring request")
            return
            
        try:
            print("Taking screenshot with voice data...")
            # Get current mouse position
            mouse_x, mouse_y = pyautogui.position()
            
            # Take screenshot
            screenshot = pyautogui.screenshot()
            
            # Convert to PIL Image if it's not already
            if not isinstance(screenshot, Image.Image):
                screenshot = Image.frombytes('RGB', screenshot.size, screenshot.rgb)
            
            # Draw circle at mouse position using settings
            circle_radius = self.settings.get('circle_size', 20)
            
            # Convert hex color to RGB tuple
            circle_color_hex = self.settings.get('circle_color', '#FF0000')
            circle_color = self.hex_to_rgb(circle_color_hex)
            
            # Create a transparent overlay for the inner circle
            overlay = Image.new('RGBA', screenshot.size, (0, 0, 0, 0))
            overlay_draw = ImageDraw.Draw(overlay)
            
            # Draw inner filled circle with reduced opacity (40% of original)
            inner_color = (*circle_color, 102)  # RGBA with 40% opacity (102/255)
            overlay_draw.ellipse([
                mouse_x - circle_radius, mouse_y - circle_radius,
                mouse_x + circle_radius, mouse_y + circle_radius
            ], fill=inner_color)
            
            # Composite the overlay with the screenshot
            screenshot = screenshot.convert('RGBA')
            screenshot = Image.alpha_composite(screenshot, overlay)
            screenshot = screenshot.convert('RGB')
            
            # Draw outer circle outline on top
            draw = ImageDraw.Draw(screenshot)
            draw.ellipse([
                mouse_x - circle_radius, mouse_y - circle_radius,
                mouse_x + circle_radius, mouse_y + circle_radius
            ], outline=circle_color, width=3)
            
            # Draw helper text if enabled
            if self.settings.get('helper_text_enabled', False):
                helper_text = self.settings.get('helper_text', 'Click here')
                if helper_text.strip():  # Only draw if text is not empty
                    self.draw_helper_text(screenshot, mouse_x, mouse_y, circle_radius, helper_text)
            
            # Draw voice text if provided
            if voice_text and voice_text.strip():
                self.draw_voice_text(screenshot, voice_text)
            
            # Save screenshot
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            screenshot_path = self.current_session_folder / f"screenshot_{timestamp}.png"
            screenshot.save(str(screenshot_path))
            
            self.last_screenshot_time = datetime.now().timestamp()
            print(f"Screenshot with voice saved successfully: {screenshot_path}")
            
        except Exception as e:
            print(f"Error taking screenshot with voice: {e}")
    
    def draw_voice_text(self, screenshot, voice_text):
        """Draw voice text overlay on screenshot"""
        try:
            from PIL import ImageFont
            draw = ImageDraw.Draw(screenshot)
            
            # Try to use a better font
            try:
                font_size = 16
                font = ImageFont.truetype("arial.ttf", font_size)
            except:
                try:
                    font = ImageFont.truetype("Arial.ttf", font_size)
                except:
                    try:
                        font = ImageFont.load_default()
                    except:
                        font = None
            
            # Prepare text with line breaks for better readability
            max_length = 60  # Shorter lines for better readability in top-left corner
            if len(voice_text) > max_length:
                # Break into multiple lines
                words = voice_text.split()
                lines = []
                current_line = ""
                for word in words:
                    if len(current_line + " " + word) <= max_length:
                        current_line += (" " + word) if current_line else word
                    else:
                        if current_line:
                            lines.append(current_line)
                        current_line = word
                if current_line:
                    lines.append(current_line)
                display_text = "\n".join(lines[:3])  # Max 3 lines
                if len(lines) > 3:
                    display_text += "..."
            else:
                display_text = voice_text
            
            # Get text dimensions for multi-line text
            if font:
                lines = display_text.split('\n')
                line_heights = []
                max_width = 0
                for line in lines:
                    bbox = draw.textbbox((0, 0), line, font=font)
                    line_width = bbox[2] - bbox[0]
                    line_height = bbox[3] - bbox[1]
                    max_width = max(max_width, line_width)
                    line_heights.append(line_height)
                text_width = max_width
                text_height = sum(line_heights) + (len(lines) - 1) * 4  # 4px line spacing
            else:
                lines = display_text.split('\n')
                text_width = max(len(line) * 8 for line in lines)
                text_height = len(lines) * 18
            
            # Position at top of screen with more padding for better visibility
            padding = 20
            text_x = padding
            text_y = padding
            
            # Draw enhanced semi-transparent background
            bg_padding = 12
            bg_color = (30, 30, 30, 200)  # Darker background with higher opacity
            bg_rect = [text_x - bg_padding, text_y - bg_padding, 
                      text_x + text_width + bg_padding, text_y + text_height + bg_padding]
            
            overlay = Image.new('RGBA', screenshot.size, (0, 0, 0, 0))
            overlay_draw = ImageDraw.Draw(overlay)
            overlay_draw.rectangle(bg_rect, fill=bg_color)
            
            # Add a subtle border for better visibility
            border_color = (100, 100, 100, 150)
            overlay_draw.rectangle([bg_rect[0], bg_rect[1], bg_rect[2], bg_rect[1] + 2], fill=border_color)  # Top
            overlay_draw.rectangle([bg_rect[0], bg_rect[1], bg_rect[0] + 2, bg_rect[3]], fill=border_color)  # Left
            
            # Composite background with screenshot
            screenshot_rgba = screenshot.convert('RGBA')
            screenshot_with_bg = Image.alpha_composite(screenshot_rgba, overlay)
            screenshot_final = screenshot_with_bg.convert('RGB')
            screenshot.paste(screenshot_final)
            
            # Draw text on top (line by line for multi-line support)
            draw = ImageDraw.Draw(screenshot)
            lines = display_text.split('\n') if '\n' in display_text else [display_text]
            current_y = text_y
            
            for line in lines:
                if font:
                    draw.text((text_x, current_y), line, fill=(255, 255, 255), font=font)
                    bbox = draw.textbbox((text_x, current_y), line, font=font)
                    line_height = bbox[3] - bbox[1]
                else:
                    draw.text((text_x, current_y), line, fill=(255, 255, 255))
                    line_height = 18
                current_y += line_height + 4  # 4px line spacing
                
            print(f"Voice text drawn on screenshot: {voice_text[:50]}...")
                
        except Exception as e:
            print(f"Error drawing voice text: {e}")
    
    def stop_recording(self, updated_settings=None):
        """Stop recording and cleanup"""
        if not self.is_recording:
            return 0
            
        self.is_recording = False
        
        # Reset voice recording state
        self.is_voice_key_held = False
        self.is_voice_recording = False
        
        # Update settings if provided
        if updated_settings:
            self.settings = updated_settings
        
        # Make sure we have the latest settings
        print(f"Current PDF setting: {self.settings.get('create_pdf', False)}")
        
        # Cleanup keyboard hooks
        try:
            keyboard.unhook_all()
            print("Keyboard hooks cleaned up")
        except Exception as e:
            print(f"Error cleaning up hotkeys: {e}")
        
        # Cleanup mouse detection
        self.cleanup_mouse_detection()
        
        # Count guides
        screenshot_count = len(list(self.current_session_folder.glob("*.png"))) if self.current_session_folder else 0
        
        # PDF and video creation will be handled by the processing dialog
        # to avoid double creation and provide better user feedback
        print("Recording stopped. PDF/video creation will be handled by processing dialog.")
        
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
    
    def create_pdf_from_guides(self):
        """Create a PDF from all guides in the session folder"""
        print(f"Starting PDF creation...")
        print(f"Session folder: {self.current_session_folder}")
        
        if not self.current_session_folder or not self.current_session_folder.exists():
            raise Exception("No session folder found")
        
        # Get all PNG files sorted by filename (which includes timestamp)
        screenshot_files = sorted(self.current_session_folder.glob("*.png"))
        print(f"Found {len(screenshot_files)} PNG files")
        
        if not screenshot_files:
            raise Exception("No guides found in session folder")
        
        print(f"Creating PDF from {len(screenshot_files)} guides...")
        
        try:
            print("Importing reportlab...")
            # Import reportlab for PDF creation
            from reportlab.lib.pagesizes import letter, A4
            from reportlab.platypus import SimpleDocTemplate, Image as RLImage, Paragraph, Spacer
            from reportlab.lib.styles import getSampleStyleSheet
            from reportlab.lib.units import inch
            print("Reportlab imported successfully")
            
            # Create PDF filename
            pdf_filename = f"{self.current_session_folder.name}.pdf"
            pdf_path = self.current_session_folder / pdf_filename
            print(f"PDF will be created at: {pdf_path}")
            
            # Create PDF document
            doc = SimpleDocTemplate(str(pdf_path), pagesize=A4)
            story = []
            styles = getSampleStyleSheet()
            print("PDF document initialized")
            
            # Add title page with guide information
            if self.guide_info:
                # Guide title
                guide_title = self.guide_info.get('name', 'Untitled Guide')
                title = Paragraph(guide_title, styles['Title'])
                story.append(title)
                story.append(Spacer(1, 0.3*inch))
                
                # Guide caption/description
                guide_caption = self.guide_info.get('caption', '')
                if guide_caption:
                    caption_paragraph = Paragraph(guide_caption, styles['Normal'])
                    story.append(caption_paragraph)
                    story.append(Spacer(1, 0.3*inch))
                
                # Screenshot count
                screenshot_count_text = f"Total Steps: {len(screenshot_files)}"
                count_paragraph = Paragraph(screenshot_count_text, styles['Heading3'])
                story.append(count_paragraph)
                story.append(Spacer(1, 0.5*inch))
                
                # Page break after title page
                from reportlab.platypus import PageBreak
                story.append(PageBreak())
            else:
                # Fallback title if no guide info
                title = Paragraph(f"Screenshot Session: {self.current_session_folder.name}", styles['Title'])
                story.append(title)
                story.append(Spacer(1, 0.2*inch))
            
            print("Title page added to PDF")
            
            # Load voice data if available
            voice_data = {}
            voice_data_file = self.current_session_folder / "voice_data.json"
            if voice_data_file.exists():
                try:
                    import json
                    with open(voice_data_file, 'r', encoding='utf-8') as f:
                        voice_data = json.load(f)
                    print(f"Loaded voice data for {len(voice_data)} screenshots")
                except Exception as e:
                    print(f"Error loading voice data: {e}")
            
            # Add each screenshot to PDF
            for step_number, screenshot_file in enumerate(screenshot_files, 1):
                try:
                    # Add step title (starting from 1)
                    step_title = Paragraph(f"Step {step_number}", styles['Heading2'])
                    story.append(step_title)
                    story.append(Spacer(1, 0.1*inch))
                    
                    # Open and resize image to fit page
                    with Image.open(screenshot_file) as img:
                        # Calculate size to fit page (A4 with margins)
                        max_width = 7*inch  # A4 width minus margins
                        max_height = 8*inch  # A4 height minus margins (reduced to leave space for caption)
                        
                        # Calculate scale factor
                        scale_w = max_width / img.width
                        scale_h = max_height / img.height
                        scale = min(scale_w, scale_h, 1)  # Don't scale up
                        
                        new_width = img.width * scale
                        new_height = img.height * scale
                        
                        # Add image to PDF
                        rl_image = RLImage(str(screenshot_file), width=new_width, height=new_height)
                        story.append(rl_image)
                        story.append(Spacer(1, 0.1*inch))
                        
                        # Add voice caption if available
                        voice_key = str(step_number)  # Voice data uses simple numbered keys
                        if voice_key in voice_data and voice_data[voice_key].get('text'):
                            transcribed_text = voice_data[voice_key]['text']
                            if transcribed_text and transcribed_text.strip():
                                # Create caption paragraph
                                caption_style = styles['BodyText'].clone('caption')
                                caption_style.fontSize = 10
                                caption_style.leading = 12
                                caption_style.leftIndent = 0.5*inch
                                caption_style.rightIndent = 0.5*inch
                                caption_style.textColor = (0.4, 0.4, 0.4)  # Gray color
                                
                                caption = Paragraph(f"<i>Caption: {transcribed_text}</i>", caption_style)
                                story.append(caption)
                                print(f"Added voice caption for step {step_number}: {transcribed_text[:50]}...")
                        
                        story.append(Spacer(1, 0.2*inch))
                        
                except Exception as e:
                    print(f"Error adding screenshot {screenshot_file} to PDF: {e}")
                    continue
            
            # Build PDF
            print(f"Building PDF with {len(story)} elements...")
            doc.build(story)
            print(f"PDF built successfully at: {pdf_path}")
            return pdf_path
            
        except ImportError:
            # Fallback to simpler PDF creation using PIL and img2pdf if reportlab not available
            try:
                import img2pdf
                
                pdf_filename = f"{self.current_session_folder.name}.pdf"
                pdf_path = self.current_session_folder / pdf_filename
                
                # Convert images to PDF
                with open(pdf_path, "wb") as f:
                    f.write(img2pdf.convert([str(img) for img in screenshot_files]))
                
                return pdf_path
                
            except ImportError:
                raise Exception("PDF creation requires 'reportlab' or 'img2pdf' package. Install with: pip install reportlab")
    
    def create_video_from_guides(self):
        """Create a video from all guides in the session folder"""
        print(f"Starting video creation...")
        print(f"Session folder: {self.current_session_folder}")
        
        if not self.current_session_folder or not self.current_session_folder.exists():
            raise Exception("No session folder found")
        
        # Get all PNG files sorted by filename (which includes timestamp)
        screenshot_files = sorted(self.current_session_folder.glob("*.png"))
        print(f"Found {len(screenshot_files)} PNG files")
        
        if not screenshot_files:
            raise Exception("No guides found in session folder")
        
        print(f"Creating video from {len(screenshot_files)} guides...")
        
        try:
            print("Importing moviepy...")
            from moviepy import ImageSequenceClip, TextClip, CompositeVideoClip, ColorClip, concatenate_videoclips
            print("MoviePy imported successfully")
            
            # Create video filename
            video_filename = f"{self.current_session_folder.name}.mp4"
            video_path = self.current_session_folder / video_filename
            print(f"Video will be created at: {video_path}")
            
            # Load voice data if available
            voice_data = {}
            voice_data_file = self.current_session_folder / "voice_data.json"
            if voice_data_file.exists():
                try:
                    import json
                    with open(voice_data_file, 'r', encoding='utf-8') as f:
                        voice_data = json.load(f)
                    print(f"Loaded voice data for {len(voice_data)} screenshots")
                    print(f"Voice data keys: {list(voice_data.keys())}")
                    for key, data in voice_data.items():
                        print(f"  {key}: text='{data.get('text', '')[:30]}...', tts_file='{data.get('tts_file', 'None')}', duration={data.get('duration', 0)}")
                except Exception as e:
                    print(f"Error loading voice data: {e}")
            else:
                print(f"No voice data file found at: {voice_data_file}")
            
            # Get fallback screenshot duration from settings
            default_duration = self.settings.get('screenshot_duration', 2.0)
            
            # Get video dimensions from first screenshot
            from PIL import Image
            with Image.open(screenshot_files[0]) as first_img:
                video_width, video_height = first_img.size
            print(f"Video dimensions: {video_width}x{video_height}")
            
            # Create title scene if guide info is available
            clips_to_concatenate = []
            total_content_duration = 0
            
            if self.guide_info:
                print("Creating title scene...")
                title_duration = 3.0  # Title scene duration in seconds
                
                # Create background color clip
                background = ColorClip(size=(video_width, video_height), color=(30, 30, 30), duration=title_duration)
                
                # Create text clips
                title_clips = [background]
                
                # Guide title
                guide_title = self.guide_info.get('name', 'Untitled Guide')
                title_text = TextClip(
                    text=guide_title,
                    font_size=min(video_width//20, 60),  # Responsive font size
                    color='white'
                ).with_position('center').with_start(0).with_duration(title_duration)
                title_clips.append(title_text)
                
                # Guide caption (if available)
                guide_caption = self.guide_info.get('caption', '')
                if guide_caption:
                    # Limit caption length for display
                    if len(guide_caption) > 200:
                        guide_caption = guide_caption[:200] + "..."
                    
                    caption_text = TextClip(
                        text=guide_caption,
                        font_size=min(video_width//40, 24),  # Smaller font for caption
                        color='lightgray'
                    ).with_position(('center', video_height * 0.6)).with_start(0).with_duration(title_duration)
                    title_clips.append(caption_text)
                
                # Compose title scene
                title_scene = CompositeVideoClip(title_clips)
                clips_to_concatenate.append(title_scene)
                print("Title scene created successfully")
            
            # Create individual clips for each screenshot with voice sync
            print("Creating individual clips with voice sync...")
            from moviepy import ImageClip, AudioFileClip, CompositeVideoClip
            
            for step_number, screenshot_file in enumerate(screenshot_files, 1):
                try:
                    # Get voice data for this screenshot
                    voice_key = str(step_number)  # Voice data uses simple numbered keys
                    screenshot_duration = default_duration  # Fallback duration
                    audio_clip = None
                    
                    if voice_key in voice_data:
                        # Try to get audio duration from TTS file first
                        tts_file = voice_data[voice_key].get('tts_file')
                        if tts_file:
                            # Handle both absolute and relative paths
                            tts_path = Path(tts_file)
                            if not tts_path.is_absolute():
                                tts_path = self.current_session_folder / tts_file
                            if tts_path.exists():
                                try:
                                    audio_clip = AudioFileClip(str(tts_path))
                                    screenshot_duration = max(audio_clip.duration, 1.0)  # Minimum 1 second
                                    print(f"Step {step_number}: Using TTS audio duration {screenshot_duration:.1f}s")
                                except Exception as e:
                                    print(f"Error loading TTS audio for step {step_number}: {e}")
                        
                        # If no TTS audio, try to use recorded audio duration
                        if not audio_clip:
                            stored_duration = voice_data[voice_key].get('duration', 0)
                            if stored_duration > 0:
                                screenshot_duration = max(stored_duration, 1.0)  # Minimum 1 second
                                print(f"Step {step_number}: Using recorded audio duration {screenshot_duration:.1f}s")
                            else:
                                print(f"Step {step_number}: No duration found, using default {screenshot_duration:.1f}s")
                    else:
                        print(f"Step {step_number}: No voice data found, using default {screenshot_duration:.1f}s")
                    
                    # Create image clip with dynamic duration
                    image_clip = ImageClip(str(screenshot_file)).with_duration(screenshot_duration)
                    
                    # Add audio if available
                    if audio_clip:
                        # Ensure audio duration matches image duration
                        if audio_clip.duration > screenshot_duration:
                            audio_clip = audio_clip.subclipped(0, screenshot_duration)
                        elif audio_clip.duration < screenshot_duration:
                            # Pad with silence if needed
                            pass  # Image will continue after audio ends
                        
                        # Combine image and audio
                        clip_with_audio = image_clip.with_audio(audio_clip)
                        clips_to_concatenate.append(clip_with_audio)
                        print(f"Step {step_number}: Added with audio ({screenshot_duration:.1f}s)")
                    else:
                        clips_to_concatenate.append(image_clip)
                        print(f"Step {step_number}: Added without audio ({screenshot_duration:.1f}s)")
                    
                    total_content_duration += screenshot_duration
                    
                except Exception as e:
                    print(f"Error creating clip for step {step_number}: {e}")
                    # Fallback to basic image clip
                    fallback_clip = ImageClip(str(screenshot_file)).with_duration(default_duration)
                    clips_to_concatenate.append(fallback_clip)
                    total_content_duration += default_duration
            
            print(f"Total video content duration: {total_content_duration:.1f}s")
            
            # Concatenate all clips
            if len(clips_to_concatenate) > 1:
                print("Combining title scene with guides...")
                final_clip = concatenate_videoclips(clips_to_concatenate)
            else:
                final_clip = clips_to_concatenate[0]
            
            # Write the video file
            print("Writing video file... (this may take a moment)")
            final_clip.write_videofile(
                str(video_path),
                fps=24,  # Standard video FPS
                codec='libx264',  # H.264 codec for good compatibility
                audio=True  # Include audio from voice recordings
            )
            
            # Clean up
            final_clip.close()
            if len(clips_to_concatenate) > 1:
                clips_to_concatenate[0].close()  # Close title scene
                clips_to_concatenate[1].close()  # Close screenshot clip
            
            print(f"Video created successfully at: {video_path}")
            return video_path
            
        except ImportError:
            # Fallback message if moviepy is not available
            raise Exception("Video creation requires 'moviepy' package. Install with: pip install moviepy")
        except Exception as e:
            print(f"Unexpected error during video creation: {e}")
            raise
    
    def get_screenshot_count(self):
        """Get current screenshot count"""
        if self.current_session_folder and self.current_session_folder.exists():
            return len(list(self.current_session_folder.glob("*.png")))
        return 0 