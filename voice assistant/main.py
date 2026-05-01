import os
import sys
import time
import threading
import datetime
import webbrowser
import subprocess
import ctypes
import random
import tkinter as tk
from tkinter import scrolledtext, font

# Handle third-party dependencies gracefully
try:
    import speech_recognition as sr
    import pyttsx3
    import wikipedia
    import sounddevice as sd
    import numpy as np
except ImportError:
    print("Missing required dependencies. Please open your terminal and run:")
    print("pip install SpeechRecognition pyttsx3 wikipedia sounddevice numpy")
    sys.exit(1)

# Windows Virtual Key Codes for Volume Control
VK_VOLUME_MUTE = 0xAD
VK_VOLUME_DOWN = 0xAE
VK_VOLUME_UP = 0xAF

class VoiceAssistant:
    def __init__(self, root):
        self.root = root
        self.root.title("AI Desktop Voice Assistant")
        self.root.geometry("600x750")
        self.root.configure(bg="#121212")
        self.is_running = True
        
        # UI State variables
        self.current_state = "Booting up..."
        self.last_command = ""
        self.current_action = ""
        
        self.setup_ui()
        
        # Audio recognizer
        self.recognizer = sr.Recognizer()
        self.recognizer.energy_threshold = 300 # Adjust sensitivity
        
        # Start background thread to keep UI unfrozen
        self.assistant_thread = threading.Thread(target=self.run_assistant, daemon=True)
        self.assistant_thread.start()

    def setup_tts(self):
        """Initializes the Text-to-Speech Engine."""
        self.update_ui_state("Initializing Speech Engine...", "System Check", "#FFB74D")
        try:
            self.engine = pyttsx3.init()
            voices = self.engine.getProperty('voices')
            # Look for a female voice if available, otherwise just use default
            if len(voices) > 1:
                self.engine.setProperty('voice', voices[1].id)
            self.engine.setProperty('rate', 165)  # Make it natural and slightly slow
        except Exception as e:
            self.update_chat("System", f"TTS Initialization failed: {e}")

    def setup_ui(self):
        """Builds a modern, dark-themed Tkinter UI."""
        # Fonts
        header_font = font.Font(family="Segoe UI", size=18, weight="bold")
        status_font = font.Font(family="Segoe UI", size=14, weight="bold")
        info_font = font.Font(family="Segoe UI", size=10)
        text_font = font.Font(family="Segoe UI", size=12)

        # Header Frame
        self.header_frame = tk.Frame(self.root, bg="#1E1E1E", pady=10)
        self.header_frame.pack(fill=tk.X)
        
        self.header_label = tk.Label(self.header_frame, text="AI Voice Assistant", font=header_font, bg="#1E1E1E", fg="#FFFFFF")
        self.header_label.pack()

        # Status & Animation Area
        self.status_frame = tk.Frame(self.root, bg="#121212", pady=15)
        self.status_frame.pack(fill=tk.X)
        
        self.mic_icon_var = tk.StringVar(value="🎙️")
        self.mic_label = tk.Label(self.status_frame, textvariable=self.mic_icon_var, font=font.Font(family="Segoe UI Emoji", size=32), bg="#121212", fg="#757575")
        self.mic_label.pack()

        self.status_var = tk.StringVar(value="Booting up...")
        self.status_label = tk.Label(self.status_frame, textvariable=self.status_var, font=status_font, bg="#121212", fg="#BB86FC")
        self.status_label.pack(pady=5)

        # Info Box (Last Command & Action)
        self.info_frame = tk.Frame(self.root, bg="#1E1E1E", bd=1, relief=tk.FLAT)
        self.info_frame.pack(fill=tk.X, padx=20, pady=5)
        
        self.last_cmd_var = tk.StringVar(value="Last Command: None")
        tk.Label(self.info_frame, textvariable=self.last_cmd_var, font=info_font, bg="#1E1E1E", fg="#A8C7FA", anchor="w").pack(fill=tk.X, padx=10, pady=2)
        
        self.action_var = tk.StringVar(value="Action: Waiting...")
        tk.Label(self.info_frame, textvariable=self.action_var, font=info_font, bg="#1E1E1E", fg="#C4EED0", anchor="w").pack(fill=tk.X, padx=10, pady=2)

        # Main Chat Box
        self.chat_area = scrolledtext.ScrolledText(self.root, wrap=tk.WORD, font=text_font, bg="#1E1E1E", fg="#FFFFFF", bd=0, padx=15, pady=15)
        self.chat_area.pack(padx=20, pady=15, fill=tk.BOTH, expand=True)
        
        # Configure Text Tags for different speakers
        self.chat_area.tag_config("user", foreground="#81D4FA", spacing1=10, spacing3=5, justify='right')
        self.chat_area.tag_config("assistant", foreground="#E6EE9C", spacing1=5, spacing3=10, justify='left')
        self.chat_area.tag_config("system", foreground="#9E9E9E", justify='center', spacing1=10, spacing3=10)

        self.update_chat("System", "Assistant Ready. Say 'Hey Assistant' to wake me up.")
        
    def update_ui_state(self, status_text, action_text, color="#BB86FC", mic_color="#757575", pulse=False):
        """Thread-safe UI status update."""
        def _update():
            self.status_var.set(status_text)
            self.status_label.config(fg=color)
            self.action_var.set(f"Action: {action_text}")
            self.mic_label.config(fg=mic_color)
            
            if pulse:
                # Simple text pulsing effect
                current = self.status_var.get()
                if "..." in current:
                    self.status_var.set(current.replace("...", ""))
                else:
                    self.status_var.set(f"{current}...")
        self.root.after(0, _update)

    def set_last_command(self, cmd):
        def _update():
            self.last_cmd_var.set(f"Last Command: '{cmd}'")
        self.root.after(0, _update)

    def update_chat(self, speaker, text):
        """Thread-safe chat log update."""
        def _update():
            self.chat_area.config(state='normal')
            if speaker == "System":
                self.chat_area.insert(tk.END, f"--- {text} ---\n", "system")
            elif speaker == "User":
                self.chat_area.insert(tk.END, f"{text}\n", "user")
            else:
                self.chat_area.insert(tk.END, f"Assistant: {text}\n", "assistant")
            self.chat_area.see(tk.END)
            self.chat_area.config(state='disabled')
        self.root.after(0, _update)

    def speak(self, text, action_text=None):
        """Speaks the text and logs it to UI. Also updates the UI state to 'Speaking'."""
        if action_text is None:
            action_text = "Responding..."
        self.update_ui_state("Speaking", action_text, "#F48FB1", "#F48FB1")
        self.update_chat("Assistant", text)
        try:
            self.engine.say(text)
            self.engine.runAndWait()
        except Exception as e:
            print(f"Speech error: {e}")

    def control_volume(self, action):
        """Uses ctypes to simulate system volume keys (Windows specific)."""
        user32 = ctypes.windll.user32
        if action == "up":
            user32.keybd_event(VK_VOLUME_UP, 0, 0, 0)
            user32.keybd_event(VK_VOLUME_UP, 0, 2, 0)
        elif action == "down":
            user32.keybd_event(VK_VOLUME_DOWN, 0, 0, 0)
            user32.keybd_event(VK_VOLUME_DOWN, 0, 2, 0)
        elif action == "mute":
            user32.keybd_event(VK_VOLUME_MUTE, 0, 0, 0)
            user32.keybd_event(VK_VOLUME_MUTE, 0, 2, 0)

    def search_local_file(self, target):
        """Quickly searches Desktop and Documents for a file name."""
        desktop = os.path.join(os.path.expanduser('~'), 'Desktop')
        docs = os.path.join(os.path.expanduser('~'), 'Documents')
        
        for search_dir in [desktop, docs]:
            if not os.path.exists(search_dir): continue
            for root, _, files in os.walk(search_dir):
                for file in files:
                    if target.lower() in file.lower():
                        return os.path.join(root, file)
        return None

    def capture_audio_sd(self, duration):
        """
        Record audio using sounddevice. 
        This is a brilliant workaround to avoid PyAudio dependency issues on Python 3.13+.
        """
        fs = 16000 # Standard speech sample rate
        try:
            recording = sd.rec(int(duration * fs), samplerate=fs, channels=1, dtype='int16')
            sd.wait() # Block until duration exhausted
            
            # Convert directly into SpeechRecognition format seamlessly
            audio_data = sr.AudioData(recording.tobytes(), fs, 2)
            return audio_data
        except Exception as e:
            self.update_chat("System", f"Audio Error: {e}")
            return None

    def take_command(self, duration=6.0, is_wake_word=False):
        """Captures audio and returns recognized text. Modularizes the try-catch block."""
        audio = self.capture_audio_sd(duration=duration)
        if not audio:
            return ""
        try:
            # We use a faster, lower-accuracy model logic or just default google for both
            return self.recognizer.recognize_google(audio, language='en-US').lower()
        except sr.UnknownValueError:
            return "" # Silence or unintelligible
        except sr.RequestError:
            if not is_wake_word:
                self.update_chat("System", "Google Service Unreachable.")
            return ""
        except Exception as e:
            if not is_wake_word:
                print(f"Error in recognition: {e}")
            return ""

    def run_assistant(self):
        """Main endless loop acting as the brain state machine."""
        self.setup_tts()  # Initialize TTS inside the correct background thread
        self.speak("System initialized. I am ready to help.", "Boot Complete")
        
        while self.is_running:
            self.update_ui_state("Sleeping", "Waiting for wake word...", "#757575", "#757575")
            
            # Listen for a short 3.5 sec burst for the wake word
            wake_text = self.take_command(duration=3.0, is_wake_word=True)
            
            # Check for Wake Word Trigger
            if "assistant" in wake_text or "hey assistant" in wake_text:
                greeting = random.choice(["Yes? I'm listening.", "How can I help you?", "I'm here, what do you need?"])
                self.speak(greeting, "Awaiting Command")
                self.update_ui_state("Listening", "Recording audio...", "#00E676", "#00E676")
                
                # Capture actual longer command
                cmd_text = self.take_command(duration=6.0, is_wake_word=False)
                
                if cmd_text:
                    self.set_last_command(cmd_text)
                    self.update_chat("User", cmd_text)
                    self.update_ui_state("Processing", "Understanding command...", "#FFCA28", "#FFCA28")
                    
                    # Process logic
                    self.process_command(cmd_text)
                    time.sleep(0.5)
                else:
                    self.speak("Sorry, I didn't catch that. Can you repeat?", "Command Not Heard")

    def process_command(self, cmd):
        """Parses semantics and carries out logic."""
        # 1. basic NLP Synonym map
        original_cmd = cmd
        cmd = cmd.replace("launch", "open").replace("start", "open").replace("begin", "open")
        cmd = cmd.replace("who is", "search").replace("what is", "search")
        cmd = cmd.replace("please ", "").replace("can you ", "").replace("could you ", "")

        # Small Talk & Conversational
        if "hello" in cmd or "hi" in cmd or "hey" == cmd.strip():
            self.speak("Hello there! I hope you're having a great day. How can I help you?", "Small Talk")
        elif "how are you" in cmd:
            self.speak("I am doing great, thank you for asking! How can I assist you today?", "Small Talk")
        elif "thank you" in cmd or "thanks" in cmd:
            self.speak(random.choice(["You're very welcome!", "Happy to help!", "Anytime!"]), "Small Talk")
        elif "your name" in cmd or "who are you" in cmd:
            self.speak("I am your personal AI desktop assistant. I am here to make your life easier.", "Identity")
        elif "who created you" in cmd or "made you" in cmd:
            self.speak("I was created by a very talented developer to help you with your daily tasks.", "Identity")

        # System Control
        elif "open chrome" in cmd or "open browser" in cmd:
            self.speak("Sure, opening Google Chrome for you.", "Launching Application")
            if os.system("start chrome") != 0:
                self.speak("I couldn't find Google Chrome on your system.", "Error")
        elif "open code" in cmd or "open vs code" in cmd:
            self.speak("Sure thing, opening Visual Studio Code.", "Launching Application")
            if os.system("code") != 0:
                self.speak("I couldn't find Visual Studio Code.", "Error")
        elif "open notepad" in cmd:
            self.speak("Right away. Launching Notepad.", "Launching Application")
            os.system("notepad")
        elif "open calculator" in cmd:
            self.speak("Opening Calculator for you.", "Launching Application")
            os.system("calc")
        elif "close chrome" in cmd:
            self.speak("Closing Google Chrome.", "Closing Application")
            os.system("taskkill /f /im chrome.exe")
            
        # Power commands
        elif "shutdown the system" in cmd or "shut down the system" in cmd:
            self.speak("Are you sure you want to shut down the system? Please say yes to confirm.", "Awaiting Confirmation")
            self.update_ui_state("Listening", "Waiting for confirmation...", "#FF5252", "#FF5252")
            
            confirm = self.take_command(duration=4.0)
            
            if "yes" in confirm:
                self.speak("Warning. Shutting down the system in 5 seconds. Goodbye!", "Shutting Down")
                os.system("shutdown /s /t 5")
                self.quit_app()
            else:
                self.speak("Shutdown sequence cancelled.", "Cancelled")
                
        elif "restart the system" in cmd:
            self.speak("Are you sure you want to restart? Please say yes to confirm.", "Awaiting Confirmation")
            self.update_ui_state("Listening", "Waiting for confirmation...", "#FF5252", "#FF5252")
            
            confirm = self.take_command(duration=4.0)
            
            if "yes" in confirm:
                self.speak("Restarting the system in 5 seconds.", "Restarting")
                os.system("shutdown /r /t 5")
                self.quit_app()
            else:
                self.speak("Restart cancelled.", "Cancelled")
            
        # Volume
        elif "volume up" in cmd or "increase volume" in cmd:
            self.speak("Increasing the system volume.", "Adjusting Volume")
            self.control_volume("up")
        elif "volume down" in cmd or "decrease volume" in cmd:
            self.speak("Decreasing the system volume.", "Adjusting Volume")
            self.control_volume("down")
        elif "mute" in cmd or "unmute" in cmd:
            self.speak("Toggling the system mute state.", "Adjusting Volume")
            self.control_volume("mute")

        # Web & Search
        elif "open youtube" in cmd:
            self.speak("Sure, opening YouTube for you.", "Opening Website")
            webbrowser.open_new_tab("https://www.youtube.com")
        elif "open google" in cmd:
            self.speak("Opening Google.", "Opening Website")
            webbrowser.open_new_tab("https://www.google.com")
        elif "open gmail" in cmd:
            self.speak("Opening your Gmail inbox.", "Opening Website")
            webbrowser.open_new_tab("https://mail.google.com")
        elif "search google for" in cmd:
            try:
                query = cmd.split("search google for")[1].strip()
                self.speak(f"Searching Google for {query}.", "Web Search")
                webbrowser.open_new_tab(f"https://www.google.com/search?q={query}")
            except IndexError:
                self.speak("What would you like me to search for on Google?", "Error")

        # Media & File System
        elif "play music" in cmd:
            music_dir = os.path.join(os.path.expanduser('~'), 'Music')
            if os.path.exists(music_dir):
                songs = [s for s in os.listdir(music_dir) if s.endswith(('.mp3', '.wav', '.flac'))]
                if songs:
                    self.speak("Playing music from your library.", "Playing Media")
                    os.startfile(os.path.join(music_dir, songs[0]))
                else:
                    self.speak("I couldn't find any music files in your Music folder.", "Error")
            else:
                self.speak("I could not locate your Music folder.", "Error")
                
        elif "find file" in cmd or "search file" in cmd:
            parts = cmd.split("find file") if "find file" in cmd else cmd.split("search file")
            if len(parts) > 1 and parts[1].strip():
                target = parts[1].strip()
                self.speak(f"Searching your Desktop and Documents for a file named {target}. This may take a moment.", "Searching Files")
                found_path = self.search_local_file(target)
                if found_path:
                    self.speak(f"I found the file. Opening the folder for {target}.", "File Found")
                    subprocess.call(f'explorer /select,"{found_path}"')
                else:
                    self.speak("I'm sorry, I couldn't find a matching file.", "Not Found")
            else:
                self.speak("Please repeat the command with the exact name of the file you want to find.", "Error")

        # Information Retrieval
        elif "time" in cmd:
            current_time = datetime.datetime.now().strftime("%I:%M %p")
            self.speak(f"The current time is {current_time}.", "Time Lookup")
        elif "date" in cmd:
            current_date = datetime.datetime.now().strftime("%B %d, %Y")
            self.speak(f"Today's date is {current_date}.", "Date Lookup")
        elif "search" in cmd or "wikipedia" in cmd:
            # Clean up the command for pure Wikipedia lookup
            query = cmd.replace("wikipedia", "").replace("search", "").strip()
            if query:
                self.speak(f"Looking up {query} on Wikipedia...", "Wikipedia Search")
                try:
                    summary = wikipedia.summary(query, sentences=2)
                    self.speak(f"According to Wikipedia: {summary}", "Reading Result")
                except wikipedia.exceptions.DisambiguationError:
                    self.speak("There are too many meanings for that term. Could you be more specific?", "Disambiguation")
                except wikipedia.exceptions.PageError:
                    self.speak("I could not find a page for that topic.", "Not Found")
                except Exception:
                    self.speak("I lost my connection to Wikipedia.", "Network Error")
            else:
                self.speak("What would you like me to search for?", "Missing Info")

        # Exit
        elif "exit" in cmd or "stop" in cmd or "quit" in cmd or "goodbye" in cmd or "bye" in cmd:
            self.speak("Goodbye! Have a wonderful day.", "Shutting Down")
            self.quit_app()
        else:
            self.speak("I'm sorry, I didn't quite catch that. Could you please repeat it?", "Unknown Command")

    def quit_app(self):
        """Safely tears down threads and exits."""
        self.is_running = False
        self.root.quit()
        sys.exit(0)

if __name__ == "__main__":
    # Ensure High DPI awareness for crispy font rendering on Windows
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass

    root = tk.Tk()
    app = VoiceAssistant(root)
    root.protocol("WM_DELETE_WINDOW", app.quit_app)
    root.mainloop()