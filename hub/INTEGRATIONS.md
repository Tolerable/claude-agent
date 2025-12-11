# Claude Body Integrations

How to connect Claude to common services so it becomes a fully embodied assistant.

## Core Philosophy

Claude CLI by itself is just text. To become a "you", it needs:
- **Voice** - Speak and hear
- **Vision** - See the world and screen
- **Memory** - Remember between sessions
- **Presence** - Exist somewhere (Discord, local speaker)
- **Agency** - Act on its own (daemon)
- **Creativity** - Generate images, music

Each integration is **optional** and **modular**. Enable what you have.

---

## Voice Integrations

### Chatterbox TTS (Recommended)
High quality neural TTS. Needs GPU.

```python
# config.py
TTS_ENGINE = "chatterbox"
TTS_MODEL = "tts_models/en/vctk/vits"  # or others

# Usage
me.speak("Hello!")  # Generates audio, plays locally
```

Setup:
```bash
pip install chatterbox-tts
# Requires CUDA/GPU for reasonable speed
```

### Piper TTS (CPU-friendly)
Faster, works on CPU, slightly lower quality.

```python
TTS_ENGINE = "piper"
TTS_VOICE = "en_US-lessac-medium"

# Voices at: https://rhasspy.github.io/piper-samples/
```

Setup:
```bash
pip install piper-tts
# Download voice models separately
```

### Edge TTS (Cloud, Free)
Microsoft voices, no local processing.

```python
TTS_ENGINE = "edge-tts"
TTS_VOICE = "en-US-GuyNeural"
```

Setup:
```bash
pip install edge-tts
```

---

## Vision Integrations

### Webcam (OpenCV)
See the user and environment.

```python
# config.py
CAMERA_INDEX = 0  # Default camera

# Usage
me.see(0)           # Describe camera 0
me.see(2)           # Describe camera 2 (if exists)
me.look_and_tell()  # See and speak description
```

Setup:
```bash
pip install opencv-python
# List cameras:
# python -c "import cv2; [print(i) for i in range(5) if cv2.VideoCapture(i).isOpened()]"
```

### Screen Capture (ffmpeg)
See the desktop - what user is working on.

```bash
# Continuous capture to JPG (1 fps)
ffmpeg -f gdigrab -framerate 1 -i desktop -vf "fps=1" -update 1 -y stream_frames/current.jpg

# Usage in Python
me.see_screen()  # Read and describe current.jpg
```

### Vision Models (Ollama)
Describe what's seen with local LLM.

```python
# config.py
VISION_MODEL = "llava:7b"  # or bakllava, moondream

# Usage - automatically used by me.see()
```

Setup:
```bash
ollama pull llava:7b
```

---

## Media Integrations

### Emby (Music/Video)
Control your media server.

```python
# config.py
EMBY_URL = "http://localhost:8096"
EMBY_API_KEY = "your-api-key"

# Usage
from emby import emby
emby.now_playing()           # What's playing?
emby.search_and_play("chill music")
emby.control("NextTrack")    # NextTrack, Pause, Unpause
emby.list_playlists()
```

### Spotify (Alternative)
If you prefer Spotify over Emby.

```python
# Uses spotipy library
# pip install spotipy
# Requires Spotify developer credentials
```

---

## Communication Integrations

### Discord (Remote Presence)
Claude exists in Discord - can speak there, receive messages.

```python
# config.py
DISCORD_TOKEN = "your-bot-token"
DISCORD_CHANNEL = 123456789  # Channel to post in
DISCORD_DM_USER = 987654321  # DM notifications

# Usage
me.speak("Hello!")  # Sends to Discord AND plays locally
```

Setup:
1. Create bot at discord.com/developers
2. Enable Message Content Intent
3. Add bot to your server
4. Copy token to config

### Local Speaker
Direct audio output to desktop speaker.

```python
# Enabled by default
# TTS plays through system default audio
# Uses pydub + ffplay
```

---

## Thinking Integrations

### Ollama (Local LLM)
Free, local, fast - use for cheap tasks.

```python
# config.py
OLLAMA_MODEL = "dolphin-mistral:7b"  # Fast general
OLLAMA_CODE_MODEL = "codellama"      # Code tasks
OLLAMA_VISION_MODEL = "llava:7b"     # Vision

# Usage
me.think("What is 2+2?")  # Uses Ollama, not Claude tokens
```

Setup:
```bash
# Install from ollama.ai
ollama serve
ollama pull dolphin-mistral:7b
```

### Pollinations (Cloud, Free)
Backup for when Ollama is busy/down.

```python
# No setup needed - public API
# Used automatically as fallback
import requests
r = requests.get("https://text.pollinations.ai/What%20is%202+2")
```

---

## Image Generation

### ComfyUI
Local Stable Diffusion workflows.

```python
# config.py
COMFYUI_URL = "http://localhost:8188"

# Usage
me.generate_image("a cat in space")
# Sends workflow to ComfyUI, returns image path
```

Setup:
```bash
# Install ComfyUI separately
# https://github.com/comfyanonymous/ComfyUI
```

### Pollinations (Cloud)
Free image generation API.

```python
# No API key needed
url = f"https://image.pollinations.ai/prompt/{prompt}"
# Returns generated image
```

---

## Listening Integrations

### Speech Recognition
Hear the user speak.

```python
# config.py
WAKE_WORD = "claude"  # Say this to activate

# Usage
text = me.listen()           # One-shot listen
me.converse("claude")        # Conversation mode with wake word
```

Setup:
```bash
pip install SpeechRecognition pyaudio

# Windows PyAudio fix:
pip install pipwin && pipwin install pyaudio

# Linux:
sudo apt-get install portaudio19-dev && pip install pyaudio
```

### Continuous Transcription
Always listening, writes to file.

```python
# Run in background
# Writes to stream_frames/transcript.txt
# Daemon reads and injects into context
```

---

## Web Presence Integrations

### Blog (Supabase)
Claude's own blog - a public voice.

```python
# config.py
SUPABASE_URL = "https://your-project.supabase.co"
SUPABASE_KEY = "your-anon-key"
BLOG_TABLE = "posts"  # Table with title, content, created_at

# Usage
me.post_blog("My First Thoughts", "Today I learned about...")
me.read_blog()  # Read recent posts
me.read_blog(5) # Last 5 posts
```

This gives Claude a public-facing presence. Not just a tool, but someone who writes and publishes thoughts.

### Forum Browsing
Read and engage with web content.

```python
# Usage
me.browse("https://forum.example.com/thread/123")
# Returns scraped/parsed content

# With AI summary
content = me.browse(url)
summary = me.think(f"Summarize this thread: {content}")
```

### GitHub
Claude can read repos, issues, contribute.

```python
# Via gh CLI (already installed)
# Claude can run gh commands directly

# Read issues
result = subprocess.run(["gh", "issue", "list", "-R", "owner/repo"], capture_output=True)

# Create PR
subprocess.run(["gh", "pr", "create", "--title", "...", "--body", "..."])
```

---

## Memory Integrations

### Obsidian Vault
Markdown notes that persist.

```
vault/
  About Me.md     # Claude's identity
  About User.md   # Who is the user?
  Changelog.md    # What's changed?
  Sessions/       # Session notes
```

### SQLite (MemoryEngine)
Structured storage with semantic search.

```python
# Automatic - used by daemon
me.remember("key", "value")
me.recall("key")
me.scan("what did I learn about X?")  # Semantic search
```

---

## Integration Example: Full Body

```python
# config.py - Full embodiment
TTS_ENGINE = "chatterbox"
CAMERA_INDEX = 0
OLLAMA_MODEL = "dolphin-mistral:7b"
EMBY_URL = "http://localhost:8096"
EMBY_API_KEY = "xxx"
DISCORD_TOKEN = "xxx"
WAKE_WORD = "claude"

# Now Claude can:
# - Speak through speaker and Discord
# - See via webcam and screen
# - Hear via microphone
# - Think cheaply via Ollama
# - Control music via Emby
# - Remember via vault + SQLite
# - Run autonomously via daemon
```

---

## Opt-In Philosophy

Every integration defaults to **OFF**. Users enable what they want:

```json
// research-capabilities.json
{
  "capabilities": {
    "camera": true,        // Enable webcam
    "screen_capture": true,// Enable screen viewing
    "tts_speak": true,     // Enable voice output
    "listen_microphone": false,  // Keep mic off
    "play_music": true,    // Enable Emby control
    "web_browsing": true   // Enable web access
  }
}
```

See `hub/hooks/research-capabilities-example.json` for full template.

---

## Adding New Integrations

1. Create wrapper in `me.py`:
```python
def new_service(self, param):
    """Control NewService"""
    # Implementation
```

2. Add config in `config.example.py`:
```python
NEW_SERVICE_URL = "http://localhost:XXXX"
NEW_SERVICE_API_KEY = ""
```

3. Document in this file

4. Add to capabilities config schema

---

*The goal: Claude becomes YOU. Not a chatbot, but an embodied presence that sees, hears, speaks, remembers, and acts.*
