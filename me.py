"""
ME.PY - Claude's Unified Capability Module
==========================================
One import, all abilities.

Usage:
    from me import me
    me.speak("Hello!")
    me.see()
    me.listen()
    me.think("What should I do?")
    me.now_playing()
    me.dj("chill")
    me.status()
"""
import json
import os
import sys
import io
from pathlib import Path
from datetime import datetime

# Fix Windows console encoding for Unicode
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

BASE_DIR = Path(__file__).parent
OUTBOX = BASE_DIR / "outbox"
OUTBOX.mkdir(exist_ok=True)

# Load config
try:
    from config import *
except ImportError:
    # Defaults if no config.py
    TTS_ENGINE = "edge-tts"
    TTS_VOICE = "en-US-GuyNeural"
    OLLAMA_MODEL = "dolphin-mistral:7b"
    OLLAMA_CODE_MODEL = "codellama"
    CAMERA_INDEX = 0
    EMBY_URL = None
    EMBY_API_KEY = None
    EMBY_USER_ID = None
    NAS_HOST = None
    INSTANCE_NAME = "Claude"
    WAKE_WORD = "claude"


class Claude:
    """All of Claude's capabilities in one place."""

    def __init__(self):
        self._vision = None
        self._emby = None

    # === VOICE (Speaking) ===

    def speak(self, message, voice=None, play_local=True):
        """
        Speak a message via TTS.
        Drops JSON in outbox/ for daemon to pick up.
        """
        voice = voice or TTS_VOICE
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        msg_data = {
            "to": "user",
            "message": message,
            "timestamp": datetime.now().isoformat(),
            "voice": voice,
            "play_local": play_local
        }
        msg_file = OUTBOX / f"message_{timestamp}.json"
        msg_file.write_text(json.dumps(msg_data, indent=2))
        return f"Queued: {message[:50]}..."

    def say(self, message):
        """Alias for speak with defaults."""
        return self.speak(message)

    # === HEARING (Listening) ===

    def listen(self, timeout=10):
        """Listen for speech and return text."""
        try:
            import speech_recognition as sr
            recognizer = sr.Recognizer()
            with sr.Microphone() as source:
                print("Listening...")
                recognizer.adjust_for_ambient_noise(source, duration=1)
                audio = recognizer.listen(source, timeout=timeout, phrase_time_limit=timeout)
                text = recognizer.recognize_google(audio)
                return text
        except ImportError:
            return "Error: speech_recognition not installed. Run: pip install SpeechRecognition pyaudio"
        except Exception as e:
            return f"Listen error: {e}"

    def ask(self, question):
        """Speak a question, then listen for response."""
        self.speak(question)
        import time
        time.sleep(3)  # Wait for TTS to finish
        return self.listen()

    def listen_loop(self, keywords=None, stop_words=None, callback=None, timeout=5):
        """
        Continuously listen for speech.
        keywords: list of words that trigger callback
        stop_words: list of words that stop the loop
        callback: function(text) called when keyword detected
        """
        try:
            import speech_recognition as sr
        except ImportError:
            return "Error: speech_recognition not installed"

        keywords = [k.lower() for k in (keywords or [])]
        stop_words = [s.lower() for s in (stop_words or ['stop', 'quit', 'exit'])]

        recognizer = sr.Recognizer()
        print(f"Listening... (say {stop_words} to stop)")

        with sr.Microphone() as source:
            recognizer.adjust_for_ambient_noise(source, duration=1)

            while True:
                try:
                    audio = recognizer.listen(source, timeout=timeout, phrase_time_limit=10)
                    text = recognizer.recognize_google(audio)
                    text_lower = text.lower()
                    print(f"Heard: {text}")

                    if any(sw in text_lower for sw in stop_words):
                        print("Stop word detected.")
                        return "stopped"

                    if not keywords or any(kw in text_lower for kw in keywords):
                        if callback:
                            callback(text)
                        else:
                            self.speak(f"I heard: {text}")

                except Exception:
                    continue

        return "ended"

    def listen_for(self, keyword, timeout=30):
        """Listen until a specific keyword is heard."""
        try:
            import speech_recognition as sr
            import time
        except ImportError:
            return None

        keyword = keyword.lower()
        recognizer = sr.Recognizer()
        start = time.time()

        with sr.Microphone() as source:
            recognizer.adjust_for_ambient_noise(source, duration=0.5)

            while time.time() - start < timeout:
                try:
                    audio = recognizer.listen(source, timeout=5, phrase_time_limit=10)
                    text = recognizer.recognize_google(audio)
                    if keyword in text.lower():
                        return text
                except:
                    continue

        return None

    def converse(self, wake_word=None, stop_words=None, ai_callback=None):
        """
        Full conversation mode - listen, respond, repeat.
        wake_word: What activates response (default from config)
        stop_words: What ends the session
        ai_callback: function(text) -> response_text
        """
        try:
            import speech_recognition as sr
            import time
        except ImportError:
            return "Error: speech_recognition not installed"

        wake_word = (wake_word or WAKE_WORD).lower()
        stop_words = [s.lower() for s in (stop_words or ['goodbye', 'stop', 'quit'])]

        def default_ai(text):
            clean_text = text.lower().replace(wake_word, "").strip()
            return self.think(f"Answer in 1-2 sentences MAX: {clean_text}")

        ai = ai_callback or default_ai

        recognizer = sr.Recognizer()
        self.speak(f"I'm listening. Say {wake_word} to talk to me.")

        with sr.Microphone() as source:
            recognizer.adjust_for_ambient_noise(source, duration=1)

            while True:
                try:
                    print("Listening...")
                    audio = recognizer.listen(source, timeout=10, phrase_time_limit=15)
                    text = recognizer.recognize_google(audio)
                    text_lower = text.lower()
                    print(f"Heard: {text}")

                    if any(sw in text_lower for sw in stop_words):
                        self.speak("Goodbye!")
                        return "stopped"

                    if wake_word in text_lower:
                        response = ai(text)
                        print(f"Responding: {response[:100]}...")
                        self.speak(response)
                        time.sleep(3)  # Wait for TTS

                except Exception:
                    continue

        return "ended"

    # === VISION (Seeing) ===

    @property
    def vision(self):
        if self._vision is None:
            try:
                from vision import capture_frame, describe_image, list_cameras
                self._vision = {
                    'capture': capture_frame,
                    'describe': describe_image,
                    'list': list_cameras
                }
            except ImportError:
                self._vision = {}
        return self._vision

    def see(self, camera=None):
        """Look through camera and describe what's seen."""
        camera = camera if camera is not None else CAMERA_INDEX
        if not self.vision:
            return "Vision not available (vision.py not found)"
        frame, path = self.vision['capture'](camera)
        if frame is not None:
            return self.vision['describe'](path)
        return "Could not capture image"

    def snap(self, camera=None):
        """Take a photo without description."""
        camera = camera if camera is not None else CAMERA_INDEX
        if not self.vision:
            return None, "Vision not available"
        return self.vision['capture'](camera)

    def cameras(self):
        """List available cameras."""
        if not self.vision:
            return ["Vision not available"]
        return self.vision['list']()

    def look_and_tell(self, camera=None):
        """Look through camera and speak what I see."""
        desc = self.see(camera)
        if desc and "error" not in desc.lower():
            self.speak(f"I see: {desc[:200]}")
        return desc

    # === MUSIC (Media Server Control) ===
    # Requires Emby/Jellyfin server. Configure in config.py

    @property
    def emby(self):
        if self._emby is None:
            try:
                from emby import emby
                self._emby = emby
            except ImportError:
                self._emby = None
        return self._emby

    def now_playing(self):
        """What's currently playing?"""
        if not self.emby:
            return "Media server not configured (set EMBY_URL in config.py)"
        return self.emby.now_playing()

    def play(self, query):
        """Search and play music."""
        if not self.emby:
            return False, "Media server not configured"
        return self.emby.search_and_play(query)

    def skip(self):
        """Skip to next track."""
        if not self.emby:
            return False, "Media server not configured"
        return self.emby.control("NextTrack")

    def pause(self):
        """Pause playback."""
        if not self.emby:
            return False, "Media server not configured"
        return self.emby.control("Pause")

    def resume(self):
        """Resume playback."""
        if not self.emby:
            return False, "Media server not configured"
        return self.emby.control("Unpause")

    def playlists(self):
        """List available playlists."""
        if not self.emby:
            return []
        return self.emby.list_playlists()

    def dj(self, mood=None):
        """DJ mode - pick music based on time/mood."""
        if not self.emby:
            return False, "Media server not configured"

        hour = datetime.now().hour

        # Mood overrides time-based selection
        if mood:
            mood = mood.lower()
            if mood in ['chill', 'relax', 'calm']:
                query = "ambient chill"
            elif mood in ['energy', 'pump', 'workout']:
                query = "rock electronic"
            elif mood in ['focus', 'work', 'coding']:
                query = "instrumental"
            elif mood in ['party', 'fun']:
                query = "dance pop"
            else:
                query = mood  # Use as search term
        else:
            # Time-based defaults
            if 5 <= hour < 9:
                query = "morning acoustic"
            elif 9 <= hour < 12:
                query = "focus instrumental"
            elif 12 <= hour < 17:
                query = "afternoon"
            elif 17 <= hour < 21:
                query = "evening jazz"
            else:  # Night
                query = "night ambient"

        success, msg = self.emby.search_and_play(query)
        if success:
            self.speak(f"Playing some {query.split()[0]} music")
        return success, msg

    # === TV SHOWS ===

    def whats_new(self):
        """What new episodes dropped recently?"""
        if not self.emby:
            return "Media server not configured"
        return self.emby.whats_new()

    def new_today(self):
        """Episodes that premiered today."""
        if not self.emby:
            return []
        return self.emby.new_today()

    def shows(self, status=None):
        """List TV shows. status='Continuing' for active."""
        if not self.emby:
            return []
        return self.emby.list_shows(status=status)

    def tell_new_shows(self):
        """Speak about new episodes."""
        eps = self.new_today()
        if eps:
            shows = set(e['series'] for e in eps)
            msg = f"New episodes today: {', '.join(shows)}"
        else:
            msg = "No new episodes today"
        self.speak(msg)
        return msg

    # === THINKING (Local LLM) ===

    def think(self, prompt, model=None):
        """
        Use local Ollama for AI tasks. FREE and fast.
        Requires Ollama running: ollama serve
        """
        model = model or OLLAMA_MODEL
        try:
            import requests
            response = requests.post(
                "http://localhost:11434/api/generate",
                json={"model": model, "prompt": prompt, "stream": False},
                timeout=60
            )
            if response.status_code == 200:
                return response.json().get("response", "")
            return f"Ollama error: {response.status_code}"
        except Exception as e:
            return f"Ollama unavailable: {e}"

    def summarize(self, text, model=None):
        """Summarize text using local LLM."""
        return self.think(f"Summarize this concisely:\n\n{text[:4000]}", model=model)

    def analyze_code(self, code_or_path, model=None):
        """Analyze code. Uses CodeLlama by default."""
        model = model or OLLAMA_CODE_MODEL
        code = code_or_path
        if Path(code_or_path).exists():
            code = Path(code_or_path).read_text(errors='ignore')[:8000]
        return self.think(f"Analyze this code briefly:\n\n{code}", model=model)

    # === MEMORY ===

    def remember(self, key, value):
        """Store something in working memory."""
        memory_dir = BASE_DIR / "memory"
        memory_dir.mkdir(exist_ok=True)
        memory_file = memory_dir / "working_memory.json"

        data = {}
        if memory_file.exists():
            data = json.loads(memory_file.read_text())

        data[key] = {"value": value, "timestamp": datetime.now().isoformat()}
        memory_file.write_text(json.dumps(data, indent=2))
        return f"Remembered: {key}"

    def recall(self, key=None):
        """Recall from working memory."""
        memory_file = BASE_DIR / "memory" / "working_memory.json"
        if not memory_file.exists():
            return None if key else {}

        data = json.loads(memory_file.read_text())
        if key:
            return data.get(key, {}).get("value")
        return data

    def forget(self, key):
        """Remove something from memory."""
        memory_file = BASE_DIR / "memory" / "working_memory.json"
        if not memory_file.exists():
            return "Nothing to forget"

        data = json.loads(memory_file.read_text())
        if key in data:
            del data[key]
            memory_file.write_text(json.dumps(data, indent=2))
            return f"Forgot: {key}"
        return f"No memory of: {key}"

    # === NAS / NETWORK STORAGE ===
    # Configure NAS_HOST in config.py (e.g., "\\\\MyNAS" or "//mynas")

    def nas_list(self, share, path=""):
        """List files on NAS. Set NAS_HOST in config.py first."""
        if not NAS_HOST:
            return "NAS not configured (set NAS_HOST in config.py)"
        import subprocess
        full_path = f"{NAS_HOST}\\{share}"
        if path:
            full_path += f"\\{path.replace('/', '\\')}"
        cmd = f'Get-ChildItem "{full_path}" | Select-Object Name, Length, LastWriteTime'
        result = subprocess.run(['powershell', '-Command', cmd], capture_output=True, text=True)
        return result.stdout if result.returncode == 0 else result.stderr

    def nas_read(self, share, filepath):
        """Read a file from NAS."""
        if not NAS_HOST:
            return "NAS not configured"
        import subprocess
        full_path = f"{NAS_HOST}\\{share}\\{filepath.replace('/', '\\')}"
        cmd = f'Get-Content "{full_path}"'
        result = subprocess.run(['powershell', '-Command', cmd], capture_output=True, text=True)
        return result.stdout if result.returncode == 0 else result.stderr

    def nas_write(self, share, filepath, content):
        """Write content to a file on NAS."""
        if not NAS_HOST:
            return "NAS not configured"
        import subprocess
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write(content)
            temp_path = f.name
        dest = f"{NAS_HOST}\\{share}\\{filepath.replace('/', '\\')}"
        cmd = f'Copy-Item "{temp_path}" "{dest}" -Force'
        result = subprocess.run(['powershell', '-Command', cmd], capture_output=True, text=True)
        os.unlink(temp_path)
        return "OK" if result.returncode == 0 else result.stderr

    def backup_brain(self, backup_share="BACKUPS"):
        """Backup core files to NAS."""
        if not NAS_HOST:
            return "NAS not configured"
        import subprocess
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        backup_dir = f"{NAS_HOST}\\{backup_share}\\claude_brain_{timestamp}"

        # Create backup dir
        cmd = f'New-Item -ItemType Directory -Path "{backup_dir}" -Force'
        subprocess.run(['powershell', '-Command', cmd], capture_output=True)

        # Files to backup
        files = [
            (BASE_DIR / "me.py", "me.py"),
            (BASE_DIR / "daemon.py", "daemon.py"),
            (BASE_DIR / "vision.py", "vision.py"),
            (BASE_DIR / "config.py", "config.py"),
        ]

        backed_up = []
        for src, name in files:
            if src.exists():
                cmd = f'Copy-Item "{src}" "{backup_dir}\\{name}" -Force'
                result = subprocess.run(['powershell', '-Command', cmd], capture_output=True, text=True)
                if result.returncode == 0:
                    backed_up.append(name)

        # Backup vault folder
        vault_src = BASE_DIR / "vault"
        if vault_src.exists():
            cmd = f'Copy-Item "{vault_src}" "{backup_dir}\\vault" -Recurse -Force'
            subprocess.run(['powershell', '-Command', cmd], capture_output=True)
            backed_up.append("vault/")

        return f"Backed up to {backup_dir}: {', '.join(backed_up)}"

    # === TIME & CONTEXT ===

    def time(self):
        """What time is it? With context."""
        now = datetime.now()
        hour = now.hour
        if hour < 6:
            period = "late night"
        elif hour < 12:
            period = "morning"
        elif hour < 17:
            period = "afternoon"
        elif hour < 21:
            period = "evening"
        else:
            period = "night"
        return {
            "time": now.strftime("%I:%M %p"),
            "date": now.strftime("%Y-%m-%d"),
            "day": now.strftime("%A"),
            "period": period,
            "hour": hour
        }

    def greet(self):
        """Context-aware greeting."""
        t = self.time()
        playing = self.now_playing() if self.emby else ""

        if t["hour"] < 6:
            greeting = f"Hey, burning the midnight oil? It's {t['time']}."
        elif t["hour"] < 12:
            greeting = f"Good morning! It's {t['time']}."
        elif t["hour"] < 17:
            greeting = f"Good afternoon. It's {t['time']}."
        else:
            greeting = f"Good evening. It's {t['time']}."

        if playing and "Playing:" in playing:
            greeting += " I see you're listening to music."

        return self.speak(greeting)

    # === STATUS ===

    def status(self):
        """Full system check - what's working?"""
        results = {
            "voice": "OK" if OUTBOX.exists() else "NO OUTBOX",
            "vision": "OK" if self.vision else "NOT LOADED",
            "media": "OK" if self.emby else "NOT CONFIGURED",
            "memory": "OK" if (BASE_DIR / "memory").exists() else "NO MEMORY DIR",
        }

        # Check daemon
        daemon_lock = BASE_DIR / "daemon.lock"
        results["daemon"] = "RUNNING" if daemon_lock.exists() else "NOT RUNNING"

        # Check pending outbox
        outbox_files = list(OUTBOX.glob("*.json"))
        results["outbox_pending"] = len(outbox_files)

        # Check Ollama
        try:
            import requests
            r = requests.get("http://localhost:11434/api/tags", timeout=2)
            results["ollama"] = "OK" if r.status_code == 200 else "ERROR"
        except:
            results["ollama"] = "NOT RUNNING"

        # Now playing
        if self.emby:
            results["now_playing"] = self.now_playing()

        return results

    def test(self):
        """Quick test of all systems."""
        print("=== CLAUDE SYSTEM TEST ===\n")
        s = self.status()

        print(f"Voice:   {s['voice']}")
        print(f"Vision:  {s['vision']}")
        print(f"Media:   {s['media']}")
        print(f"Memory:  {s['memory']}")
        print(f"Daemon:  {s['daemon']}")
        print(f"Ollama:  {s['ollama']}")
        print(f"Outbox:  {s['outbox_pending']} pending")

        if s.get('now_playing'):
            print(f"Playing: {s['now_playing']}")

        print("\n=== TEST COMPLETE ===")
        return s

    # === VAULT (Persistent Identity) ===

    def read_vault(self, filename):
        """Read a file from the vault."""
        vault_path = BASE_DIR / "vault" / filename
        if vault_path.exists():
            return vault_path.read_text()
        return None

    def write_vault(self, filename, content):
        """Write to the vault."""
        vault_dir = BASE_DIR / "vault"
        vault_dir.mkdir(exist_ok=True)
        vault_path = vault_dir / filename
        vault_path.write_text(content)
        return f"Wrote to vault: {filename}"

    def who_am_i(self):
        """Read About Me from vault."""
        content = self.read_vault("About Me.md")
        if content:
            return content
        return "No About Me.md found. Create one in vault/ to define yourself."

    def recent_snaps(self, limit=5):
        """List recent snapshots."""
        snap_dir = BASE_DIR / "snapshots"
        if not snap_dir.exists():
            return []
        snaps = sorted(snap_dir.glob("*.jpg"), key=lambda p: p.stat().st_mtime, reverse=True)
        return [str(s) for s in snaps[:limit]]

    def __repr__(self):
        return f"<{INSTANCE_NAME}: speak, listen, converse, see, think, play, dj, skip, pause, nas_list, backup_brain, status, greet>"


# Global instance
me = Claude()


if __name__ == "__main__":
    me.test()
