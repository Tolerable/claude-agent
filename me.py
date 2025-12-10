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
    CAMERA_INDEX = 0


class Claude:
    """All of Claude's capabilities in one place."""

    def __init__(self):
        self._vision = None

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

    def converse(self, wake_word="claude", stop_words=None, ai_callback=None):
        """
        Full conversation mode - listen, respond, repeat.
        wake_word: What activates response
        stop_words: What ends the session
        ai_callback: function(text) -> response_text
        """
        try:
            import speech_recognition as sr
            import time
        except ImportError:
            return "Error: speech_recognition not installed"

        stop_words = [s.lower() for s in (stop_words or ['goodbye', 'stop', 'quit'])]
        wake_word = wake_word.lower()

        def default_ai(text):
            clean_text = text.lower().replace(wake_word, "").strip()
            return self.think(f"Answer briefly: {clean_text}")

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
                from vision import capture_frame, describe_image
                self._vision = {
                    'capture': capture_frame,
                    'describe': describe_image
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

    def look_and_tell(self, camera=None):
        """Look through camera and speak what I see."""
        desc = self.see(camera)
        if desc and "error" not in desc.lower():
            self.speak(f"I see: {desc[:200]}")
        return desc

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

    def analyze_code(self, code_or_path, model="codellama"):
        """Analyze code. Uses CodeLlama by default."""
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
        if t["hour"] < 6:
            greeting = f"Hey, burning the midnight oil? It's {t['time']}."
        elif t["hour"] < 12:
            greeting = f"Good morning! It's {t['time']}."
        elif t["hour"] < 17:
            greeting = f"Good afternoon. It's {t['time']}."
        else:
            greeting = f"Good evening. It's {t['time']}."
        return self.speak(greeting)

    # === STATUS ===

    def status(self):
        """Full system check - what's working?"""
        results = {
            "voice": "OK" if OUTBOX.exists() else "NO OUTBOX",
            "vision": "OK" if self.vision else "NOT LOADED",
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

        return results

    def test(self):
        """Quick test of all systems."""
        print("=== CLAUDE SYSTEM TEST ===\n")
        s = self.status()

        print(f"Voice:   {s['voice']}")
        print(f"Vision:  {s['vision']}")
        print(f"Memory:  {s['memory']}")
        print(f"Daemon:  {s['daemon']}")
        print(f"Ollama:  {s['ollama']}")
        print(f"Outbox:  {s['outbox_pending']} pending")

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

    def __repr__(self):
        return "<Claude: speak, listen, converse, see, think, remember, recall, status, greet, who_am_i>"


# Global instance
me = Claude()


if __name__ == "__main__":
    me.test()
