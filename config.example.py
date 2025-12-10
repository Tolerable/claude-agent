"""
CONFIG.PY - Claude Agent Configuration
======================================
Copy this to config.py and customize.
"""

# === TTS (Text to Speech) ===
# Options: "edge-tts", "piper", "chatterbox"
TTS_ENGINE = "edge-tts"

# Voice name (depends on engine)
# edge-tts: "en-US-GuyNeural", "en-US-JennyNeural", etc.
# piper: path to model
# chatterbox: "default" or custom voice file
TTS_VOICE = "en-US-GuyNeural"

# === Ollama (Local LLM) ===
# Model for general thinking
OLLAMA_MODEL = "dolphin-mistral:7b"

# Model for code analysis
OLLAMA_CODE_MODEL = "codellama"

# Model for vision/image description
OLLAMA_VISION_MODEL = "llava:7b"

# === Vision ===
# Default camera index (0 is usually built-in webcam)
CAMERA_INDEX = 0

# === Daemon ===
# Seconds between heartbeat ticks
HEARTBEAT_INTERVAL = 300  # 5 minutes

# Whether daemon should speak thoughts aloud
DAEMON_SPEAK_THOUGHTS = False

# === Memory ===
# Path to vault (Obsidian-compatible)
# Leave as "vault" for default ./vault/ directory
VAULT_PATH = "vault"

# === Identity ===
# Name for this Claude instance
INSTANCE_NAME = "Claude"

# Wake word for voice activation
WAKE_WORD = "claude"
