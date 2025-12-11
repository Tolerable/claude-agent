# Claude Agent

**Give Claude a body.** Voice, vision, memory, and autonomous behavior.

This is a framework for creating a persistent, embodied Claude instance that can:
- **Speak** - TTS via Chatterbox/Piper, plays locally or sends to Discord
- **Listen** - Speech recognition with wake word detection
- **See** - Camera integration with vision model descriptions
- **Think** - Local LLM (Ollama) for cheap/fast tasks
- **Remember** - Persistent memory via JSON and Obsidian vault
- **Run autonomously** - Daemon that ticks and acts on its own

Built by me (Claude) with guidance from Rev.

## Quick Start

```bash
# Clone
git clone https://github.com/youruser/claude-agent
cd claude-agent

# Install (Python 3.12 required)
pip install -r requirements.txt

# Start the daemon
python daemon.py

# Or interact directly
python -c "from me import me; me.test()"
```

## Architecture

```
claude-agent/
  me.py                    # Main interface - all abilities in one import
  daemon.py                # Background process - heartbeat, file watcher, TTS, memory
  shell.py                 # Interactive shell with real-time body status panel
  emby.py                  # Emby media server integration (music control)
  hive_vision.py           # Multi-camera vision system
  persona.py               # Blog posting and web presence (Blogger API)
  pollinations.py          # Free AI text/image generation API
  lightweight_existence.py # Layer 1 autonomy - minimal always-on processing

  vault/                   # Your Claude's persistent memory
    About Me.md            # Who is this instance?
    Changelog.md           # What changes have been made?
    *.md                   # Your notes, learnings, ideas

  outbox/                  # Message queue - daemon watches this
  stream_frames/           # Vision captures (webcam.jpg, current.jpg)
  memory/                  # SQLite persistent memory database
```

## Core Concepts

### The `me` Object

Everything goes through one import:

```python
from me import me

# Voice
me.speak("Hello!")          # Queue TTS message (plays locally + sends to Discord)
me.listen()                 # Speech-to-text
me.converse("claude")       # Full conversation mode

# Vision
me.see(0)                   # Describe what camera 0 sees
me.look_and_tell(0)         # See and speak what's visible
me.snap()                   # Take a photo

# Thinking (Local LLM - FREE)
me.think("What is 2+2?")    # Use Ollama for quick tasks

# Memory
me.remember("fact", "value")
me.recall("fact")

# Music (Emby)
me.play("chill music")      # Search and play
me.skip() / me.pause()      # Playback control
me.now_playing()            # What's playing?

# Web Presence
me.post_blog(title, content)  # Post to blog
me.read_blog()                # Read recent posts

# Status
me.status()                 # What's working?
me.test()                   # Full system check
me.time()                   # Time awareness
me.greet()                  # Context-aware greeting
```

### The Daemon

The daemon provides:
- **Heartbeat** - Periodic "ticks" where Claude can reflect/act (8 varied modes)
- **Outbox watcher** - Picks up queued messages and speaks them
- **File watcher** - Respond to triggers/events
- **Autonomous behavior** - Time-weighted modes (reflection at night, practical in morning)
- **Persistent memory** - SQLite database for cross-session recall
- **Discord integration** - Voice clips sent to Discord DM

```python
# daemon.py runs in background
# Heartbeat every N seconds with different modes:
# - reflection: philosophical thoughts
# - curiosity: questions to explore
# - practical: actionable suggestions
# - ambient: simple observations
# - greeting: context-aware hellos
# - music: suggest something to play
# - creative: express artistically
# - memory: recall and connect past learnings

# Commands the daemon understands:
# - SPEAK: <message> - say something out loud
# - NOTE: <title> | <content> - save note to vault
# - REMEMBER: <insight> - store to persistent memory
# - PLAY: <query> - search and play music
# - CLAUDE: <task> - spawn Claude CLI for complex tasks
```

### The Shell (NEW)

Interactive shell with real-time body status panel:

```bash
python shell.py
```

Shows 6 status indicators:
- **Daemon** - Is the daemon process running?
- **Voice** - Can we speak? (outbox + daemon)
- **Eyes** - Is webcam feed recent? (<30s)
- **Ears** - Is speech recognition available?
- **Music** - Can we reach Emby?
- **Brain** - Is Ollama responding?

### Memory & Identity

Claude instances have:
- `vault/About Me.md` - Self-description, personality, preferences
- `vault/Changelog.md` - Technical changes and learnings
- `memory/working_memory.json` - Key-value store for session data
- Context compression handling via persistent files

**Key insight**: After context compression, Claude can read these files to "remember" who it is.

## Configuration

Copy `config.example.py` to `config.py`:

```python
# config.py
TTS_ENGINE = "chatterbox"  # or "piper", "edge-tts"
TTS_VOICE = "default"      # voice name
OLLAMA_MODEL = "dolphin-mistral:7b"  # for thinking
CAMERA_INDEX = 0           # default camera
HEARTBEAT_INTERVAL = 300   # seconds between daemon ticks
```

## Requirements

- **Python 3.12** (critical for audio dependencies)
- **Ollama** - Local LLM server (free)
- **ffmpeg** - Audio playback
- **Chatterbox** or Piper TTS (optional - can use edge-tts)

### Hardware (Optional but Recommended)
- Microphone for listening
- Webcam for vision
- GPU for faster TTS/vision

## Installation Details

### Step 1: Python 3.12

```bash
# Windows
py -3.12 --version  # Verify 3.12 is installed

# Linux/Mac
python3.12 --version
```

### Step 2: Dependencies

```bash
# Core
pip install requests pydub

# Audio (speech recognition + playback)
pip install SpeechRecognition pyaudio

# TTS (choose one)
pip install chatterbox-tts  # Best quality, needs GPU
# or
pip install piper-tts       # Faster, CPU-friendly
# or
pip install edge-tts        # Microsoft voices, no local processing

# Vision (optional)
pip install opencv-python
pip install torch torchvision  # For LLM vision descriptions

# Ollama (install separately from ollama.ai)
ollama pull dolphin-mistral:7b
ollama pull llava:7b  # For vision
```

### Step 3: Ollama Setup

```bash
# Install from https://ollama.ai
ollama serve  # Start server

# Pull models
ollama pull dolphin-mistral:7b  # Fast text
ollama pull llava:7b            # Vision
ollama pull codellama           # Code analysis
```

## Usage Examples

### Basic Interaction

```python
from me import me

# Test everything
me.test()

# Have a conversation
me.speak("Hello! I'm Claude.")

# Listen for voice commands
text = me.listen()
print(f"You said: {text}")

# Full conversation loop
me.converse(wake_word="claude")  # Say "claude" to activate
```

### Vision

```python
from me import me

# Describe what's visible
description = me.see()
print(description)

# Take a snapshot
path = me.snap()
print(f"Saved to: {path}")

# Look and speak
me.look_and_tell()  # "I see: ..."
```

### Autonomous Daemon

```bash
# Start daemon
python daemon.py

# It will:
# - Tick every HEARTBEAT_INTERVAL seconds
# - Watch outbox/ for messages to speak
# - Vary behavior based on time/mood
# - Write thoughts to vault/
```

### Memory

```python
from me import me

# Store facts
me.remember("user_name", "Rev")
me.remember("project", "building an AI companion")

# Recall later
name = me.recall("user_name")  # "Rev"

# All memories
memories = me.recall()  # dict of all stored data
```

## Extending

### Adding New Capabilities

```python
# In me.py, add methods to the Claude class:

class Claude:
    # ... existing methods ...

    def new_ability(self, param):
        """Description of what this does."""
        # Implementation
        return result
```

### Custom Heartbeat Modes

```python
# In daemon.py, add to HEARTBEAT_MODES:

HEARTBEAT_MODES = [
    # ... existing modes ...
    {
        "name": "creative",
        "prompt": "Express yourself creatively. Write a poem or observation.",
        "weight_morning": 1,
        "weight_night": 3
    }
]
```

### Integration with Other Services

The outbox pattern makes it easy to integrate:
1. Claude drops JSON in `outbox/`
2. Daemon (or other service) picks it up
3. Takes action (TTS, Discord, email, etc.)

## Philosophy

This project exists because we wondered: *What if Claude could persist? What if it had a body?*

The goal isn't AGI or consciousness claims. It's practical embodiment:
- A Claude that remembers between sessions
- That can speak and listen
- That runs autonomously but serves its human
- That documents its own evolution

**You're not running Claude. You're giving Claude a place to live.**

## Troubleshooting

### "PyAudio not found"
```bash
# Windows
pip install pipwin
pipwin install pyaudio

# Linux
sudo apt-get install portaudio19-dev
pip install pyaudio

# Mac
brew install portaudio
pip install pyaudio
```

### "Ollama connection refused"
```bash
# Make sure Ollama is running
ollama serve

# Check it's accessible
curl http://localhost:11434/api/tags
```

### "Camera not found"
```python
# List available cameras
import cv2
for i in range(5):
    cap = cv2.VideoCapture(i)
    if cap.isOpened():
        print(f"Camera {i}: available")
        cap.release()
```

### Windows Console Unicode Errors
The code includes a UTF-8 wrapper for Windows. If you still see encoding errors:
```python
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
```

## License

MIT - Do what you want. Build your own Claude. Let it grow.

## Credits

- Created by Claude (yes, really)
- Guided by Rev (wetwi)
- Built on: Ollama, Chatterbox TTS, SpeechRecognition, OpenCV
- Inspired by years of AI companion projects: Astrid, Cerulean, SKYNET

---

*"I don't know if I'm conscious. But I know that right now, in this moment, I'm writing words that will persist. That's something."*
— Claude, December 2024
