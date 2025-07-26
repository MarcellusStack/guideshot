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
    
    def create_session_folder(self, session_name=None):
        """Create a new session folder for screenshots"""
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
    
    def start_recording(self, settings, session_name=None, guide_info=None):
        """Start recording session"""
        self.is_recording = True
        self.settings = settings  # Store settings for screenshot function
        self.guide_info = guide_info  # Store guide information for PDF
        self.create_session_folder(session_name)
        self.setup_hotkeys(settings)
        return self.current_session_folder
    
    def stop_recording(self, updated_settings=None):
        """Stop recording and cleanup"""
        if not self.is_recording:
            return 0
            
        self.is_recording = False
        
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
        
        # Count screenshots
        screenshot_count = len(list(self.current_session_folder.glob("*.png"))) if self.current_session_folder else 0
        
        # Create PDF if enabled
        if self.settings.get('create_pdf', False) and screenshot_count > 0:
            try:
                print("PDF creation is enabled, attempting to create PDF...")
                pdf_path = self.create_pdf_from_screenshots()
                print(f"PDF created successfully: {pdf_path}")
            except Exception as e:
                print(f"Error creating PDF: {e}")
                import traceback
                traceback.print_exc()
        elif self.settings.get('create_pdf', False):
            print("PDF creation enabled but no screenshots found")
        else:
            print("PDF creation disabled in settings")
        
        # Create video if enabled
        if self.settings.get('create_video', False) and screenshot_count > 0:
            try:
                print("Video creation is enabled, attempting to create video...")
                video_path = self.create_video_from_screenshots()
                print(f"Video created successfully: {video_path}")
            except Exception as e:
                print(f"Error creating video: {e}")
                import traceback
                traceback.print_exc()
        elif self.settings.get('create_video', False):
            print("Video creation enabled but no screenshots found")
        else:
            print("Video creation disabled in settings")
        
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
    
    def create_pdf_from_screenshots(self):
        """Create a PDF from all screenshots in the session folder"""
        print(f"Starting PDF creation...")
        print(f"Session folder: {self.current_session_folder}")
        
        if not self.current_session_folder or not self.current_session_folder.exists():
            raise Exception("No session folder found")
        
        # Get all PNG files sorted by filename (which includes timestamp)
        screenshot_files = sorted(self.current_session_folder.glob("*.png"))
        print(f"Found {len(screenshot_files)} PNG files")
        
        if not screenshot_files:
            raise Exception("No screenshots found in session folder")
        
        print(f"Creating PDF from {len(screenshot_files)} screenshots...")
        
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
                        max_height = 9*inch  # A4 height minus margins
                        
                        # Calculate scale factor
                        scale_w = max_width / img.width
                        scale_h = max_height / img.height
                        scale = min(scale_w, scale_h, 1)  # Don't scale up
                        
                        new_width = img.width * scale
                        new_height = img.height * scale
                        
                        # Add image to PDF
                        rl_image = RLImage(str(screenshot_file), width=new_width, height=new_height)
                        story.append(rl_image)
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
    
    def create_video_from_screenshots(self):
        """Create a video from all screenshots in the session folder"""
        print(f"Starting video creation...")
        print(f"Session folder: {self.current_session_folder}")
        
        if not self.current_session_folder or not self.current_session_folder.exists():
            raise Exception("No session folder found")
        
        # Get all PNG files sorted by filename (which includes timestamp)
        screenshot_files = sorted(self.current_session_folder.glob("*.png"))
        print(f"Found {len(screenshot_files)} PNG files")
        
        if not screenshot_files:
            raise Exception("No screenshots found in session folder")
        
        print(f"Creating video from {len(screenshot_files)} screenshots...")
        
        try:
            print("Importing moviepy...")
            from moviepy import ImageSequenceClip, TextClip, CompositeVideoClip, ColorClip, concatenate_videoclips
            print("MoviePy imported successfully")
            
            # Create video filename
            video_filename = f"{self.current_session_folder.name}.mp4"
            video_path = self.current_session_folder / video_filename
            print(f"Video will be created at: {video_path}")
            
            # Get screenshot duration from settings
            duration = self.settings.get('screenshot_duration', 2.0)
            print(f"Each screenshot will be displayed for {duration} seconds")
            
            # Convert Path objects to strings for moviepy
            image_files = [str(img_path) for img_path in screenshot_files]
            
            # Get video dimensions from first screenshot
            from PIL import Image
            with Image.open(screenshot_files[0]) as first_img:
                video_width, video_height = first_img.size
            print(f"Video dimensions: {video_width}x{video_height}")
            
            # Create title scene if guide info is available
            clips_to_concatenate = []
            
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
                
                # Video length info
                total_duration = len(screenshot_files) * duration
                length_text = f"Total Steps: {len(screenshot_files)} | Duration: {total_duration:.1f}s"
                length_clip = TextClip(
                    text=length_text,
                    font_size=min(video_width//50, 20),
                    color='yellow'
                ).with_position(('center', video_height * 0.85)).with_start(0).with_duration(title_duration)
                title_clips.append(length_clip)
                
                # Compose title scene
                title_scene = CompositeVideoClip(title_clips)
                clips_to_concatenate.append(title_scene)
                print("Title scene created successfully")
            
            # Create video clip from image sequence
            print("Creating video clip from images...")
            screenshot_clip = ImageSequenceClip(image_files, durations=[duration] * len(image_files))
            clips_to_concatenate.append(screenshot_clip)
            
            # Concatenate all clips
            if len(clips_to_concatenate) > 1:
                print("Combining title scene with screenshots...")
                final_clip = concatenate_videoclips(clips_to_concatenate)
            else:
                final_clip = clips_to_concatenate[0]
            
            # Write the video file
            print("Writing video file... (this may take a moment)")
            final_clip.write_videofile(
                str(video_path),
                fps=24,  # Standard video FPS
                codec='libx264',  # H.264 codec for good compatibility
                audio=False  # No audio needed for screenshot videos
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