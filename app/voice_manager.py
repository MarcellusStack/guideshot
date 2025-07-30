import os
import threading
import time
import json
from pathlib import Path

class VoiceManager:
    """Handles voice recording, speech-to-text, and text-to-speech functionality"""
    
    def __init__(self):
        self.is_recording = False
        self.recording_thread = None
        self.current_audio_file = None
        self.current_text = None
        self.voice_data = {}  # Store voice data for each screenshot
        
    def start_recording(self, output_file):
        """Start voice recording to specified file"""
        if self.is_recording:
            print("Already recording")
            return False
            
        self.current_audio_file = output_file
        self.is_recording = True
        self.recording_thread = threading.Thread(target=self._record_audio)
        self.recording_thread.start()
        print(f"Started voice recording to: {output_file}")
        return True
    
    def stop_recording(self):
        """Stop voice recording and return the audio file path"""
        if not self.is_recording:
            print("Not currently recording")
            return None
            
        self.is_recording = False
        if self.recording_thread:
            self.recording_thread.join()
        
        print(f"Stopped voice recording: {self.current_audio_file}")
        return self.current_audio_file
    
    def _record_audio(self):
        """Internal method to handle audio recording"""
        try:
            import sounddevice as sd
            import soundfile as sf
            import numpy as np
            
            # Recording parameters
            sample_rate = 44100  # Sample rate
            channels = 1  # Mono
            
            print("Starting audio recording...")
            recorded_audio = []
            
            def audio_callback(indata, frames, time, status):
                if status:
                    print(f"Audio recording status: {status}")
                recorded_audio.append(indata.copy())
            
            # Start recording
            with sd.InputStream(callback=audio_callback, channels=channels, samplerate=sample_rate):
                while self.is_recording:
                    time.sleep(0.1)  # Check every 100ms
            
            # Save recorded audio
            if recorded_audio:
                audio_data = np.concatenate(recorded_audio, axis=0)
                sf.write(str(self.current_audio_file), audio_data, sample_rate)
                print(f"Audio saved to: {self.current_audio_file}")
            else:
                print("No audio data recorded")
                
        except ImportError:
            print("sounddevice and soundfile packages required for audio recording")
            print("Install with: pip install sounddevice soundfile")
            self._record_audio_fallback()
        except Exception as e:
            print(f"Error during audio recording: {e}")
            self._record_audio_fallback()
    
    def _record_audio_fallback(self):
        """Fallback audio recording using pyaudio"""
        try:
            import pyaudio
            import wave
            
            # Recording parameters
            CHUNK = 1024
            FORMAT = pyaudio.paInt16
            CHANNELS = 1
            RATE = 44100
            
            audio = pyaudio.PyAudio()
            
            # Start recording
            stream = audio.open(format=FORMAT,
                              channels=CHANNELS,
                              rate=RATE,
                              input=True,
                              frames_per_buffer=CHUNK)
            
            print("Recording audio with PyAudio...")
            frames = []
            
            while self.is_recording:
                data = stream.read(CHUNK)
                frames.append(data)
            
            # Stop recording
            stream.stop_stream()
            stream.close()
            audio.terminate()
            
            # Save recorded audio
            wf = wave.open(str(self.current_audio_file), 'wb')
            wf.setnchannels(CHANNELS)
            wf.setsampwidth(audio.get_sample_size(FORMAT))
            wf.setframerate(RATE)
            wf.writeframes(b''.join(frames))
            wf.close()
            
            print(f"Audio saved to: {self.current_audio_file}")
            
        except ImportError:
            print("pyaudio package required for fallback audio recording")
            print("Install with: pip install pyaudio")
        except Exception as e:
            print(f"Error in fallback audio recording: {e}")
    
    def speech_to_text(self, audio_file, language='de'):
        """Convert speech audio file to text"""
        try:
            import speech_recognition as sr
            
            recognizer = sr.Recognizer()
            
            # Convert audio file to wav if needed
            audio_path = Path(audio_file)
            if audio_path.suffix.lower() != '.wav':
                print(f"Converting {audio_file} to WAV format...")
                wav_file = audio_path.with_suffix('.wav')
                self._convert_to_wav(audio_file, wav_file)
                audio_file = wav_file
            
            # Recognize speech
            with sr.AudioFile(str(audio_file)) as source:
                audio_data = recognizer.record(source)
                
            # Try multiple recognition services
            text = None
            
            # Try Google Speech Recognition with language support
            try:
                text = recognizer.recognize_google(audio_data, language=language)
                print(f"Google Speech Recognition result: {text}")
            except sr.UnknownValueError:
                print("Google Speech Recognition could not understand audio")
            except sr.RequestError as e:
                print(f"Could not request results from Google Speech Recognition: {e}")
            
            # Fallback to offline recognition if Google fails
            if not text:
                try:
                    text = recognizer.recognize_sphinx(audio_data)
                    print(f"Sphinx offline recognition result: {text}")
                except sr.UnknownValueError:
                    print("Sphinx could not understand audio")
                except sr.RequestError as e:
                    print(f"Sphinx error: {e}")
            
            return text if text else "Could not transcribe audio"
            
        except ImportError:
            print("speech_recognition package required for speech-to-text")
            print("Install with: pip install SpeechRecognition")
            return "Speech recognition not available"
        except Exception as e:
            print(f"Error in speech-to-text conversion: {e}")
            return f"Error: {str(e)}"
    
    def text_to_speech(self, text, output_file, voice_type="default", language='de'):
        """Convert text to speech audio file"""
        try:
            if voice_type == "google":
                return self._google_tts(text, output_file, language)
            elif voice_type == "windows":
                return self._windows_tts(text, output_file)
            else:
                return self._default_tts(text, output_file, language)
        except Exception as e:
            print(f"Error in text-to-speech conversion: {e}")
            return False
    
    def _google_tts(self, text, output_file, language='de'):
        """Generate speech using Google TTS"""
        try:
            from gtts import gTTS
            import io
            from pydub import AudioSegment
            
            # Generate TTS
            tts = gTTS(text=text, lang=language, slow=False)
            
            # Save to memory buffer first
            mp3_buffer = io.BytesIO()
            tts.write_to_fp(mp3_buffer)
            mp3_buffer.seek(0)
            
            # Convert MP3 to WAV
            audio = AudioSegment.from_mp3(mp3_buffer)
            audio.export(str(output_file), format="wav")
            
            print(f"Google TTS audio saved to: {output_file}")
            return True
            
        except ImportError:
            print("gTTS and pydub packages required for Google TTS")
            print("Install with: pip install gtts pydub")
            return False
        except Exception as e:
            print(f"Error in Google TTS: {e}")
            return False
    
    def _windows_tts(self, text, output_file):
        """Generate speech using Windows SAPI"""
        try:
            import pyttsx3
            
            engine = pyttsx3.init()
            
            # Set voice properties
            voices = engine.getProperty('voices')
            if voices:
                engine.setProperty('voice', voices[0].id)  # Use first available voice
            
            engine.setProperty('rate', 150)  # Speed of speech
            engine.setProperty('volume', 0.9)  # Volume level
            
            # Save to file
            engine.save_to_file(text, str(output_file))
            engine.runAndWait()
            
            print(f"Windows TTS audio saved to: {output_file}")
            return True
            
        except ImportError:
            print("pyttsx3 package required for Windows TTS")
            print("Install with: pip install pyttsx3")
            return False
        except Exception as e:
            print(f"Error in Windows TTS: {e}")
            return False
    
    def _default_tts(self, text, output_file, language='de'):
        """Fallback TTS method"""
        # Try Windows TTS first, then Google TTS
        if self._windows_tts(text, output_file):
            return True
        return self._google_tts(text, output_file, language)
    
    def _convert_to_wav(self, input_file, output_file):
        """Convert audio file to WAV format"""
        try:
            from pydub import AudioSegment
            
            audio = AudioSegment.from_file(str(input_file))
            audio.export(str(output_file), format="wav")
            print(f"Converted {input_file} to {output_file}")
            
        except ImportError:
            print("pydub package required for audio conversion")
            print("Install with: pip install pydub")
        except Exception as e:
            print(f"Error converting audio file: {e}")
    
    def get_audio_duration(self, audio_file):
        """Get duration of audio file in seconds"""
        try:
            from pydub import AudioSegment
            
            audio = AudioSegment.from_file(str(audio_file))
            duration = len(audio) / 1000.0  # Convert milliseconds to seconds
            return duration
            
        except ImportError:
            print("pydub package required for audio duration")
            return 2.0  # Default duration
        except Exception as e:
            print(f"Error getting audio duration: {e}")
            return 2.0  # Default duration
    
    def save_voice_data(self, session_folder, screenshot_index, audio_file, text, tts_file=None):
        """Save voice data for a screenshot"""
        voice_data_file = Path(session_folder) / "voice_data.json"
        
        # Load existing data
        if voice_data_file.exists():
            with open(voice_data_file, 'r') as f:
                voice_data = json.load(f)
        else:
            voice_data = {}
        
        # Calculate audio duration for video sync
        audio_duration = 0
        if audio_file and Path(audio_file).exists():
            audio_duration = self.get_audio_duration(audio_file)
        
        # Add new voice data  
        voice_data[str(screenshot_index)] = {
            'audio_file': Path(audio_file).name if audio_file else None,  # Store just filename
            'text': text,
            'tts_file': Path(tts_file).name if tts_file else None,  # Store just filename
            'duration': audio_duration,  # Duration in seconds for video sync
            'timestamp': time.time()
        }
        
        # Save updated data
        with open(voice_data_file, 'w') as f:
            json.dump(voice_data, f, indent=2)
        
        print(f"Voice data saved for screenshot {screenshot_index}")
    
    def load_voice_data(self, session_folder):
        """Load voice data for a session"""
        voice_data_file = Path(session_folder) / "voice_data.json"
        
        if voice_data_file.exists():
            with open(voice_data_file, 'r') as f:
                return json.load(f)
        
        return {}