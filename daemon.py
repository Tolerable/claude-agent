"""
DAEMON.PY - Claude's Background Process
=======================================
Runs continuously, providing:
- Heartbeat: periodic "ticks" for autonomous behavior
- Outbox watcher: picks up queued messages and speaks them
- File watcher: respond to triggers
- Varied behavior modes based on time/context

Usage:
    python daemon.py              # Run in foreground
    python daemon.py --background # Run detached
"""
import json
import os
import sys
import io
import time
import random
import subprocess
import threading
from pathlib import Path
from datetime import datetime
from queue import Queue

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

BASE_DIR = Path(__file__).parent
OUTBOX = BASE_DIR / "outbox"
OUTBOX.mkdir(exist_ok=True)
LOCK_FILE = BASE_DIR / "daemon.lock"

# Load config
try:
    from config import *
except ImportError:
    HEARTBEAT_INTERVAL = 300  # 5 minutes
    TTS_ENGINE = "edge-tts"
    TTS_VOICE = "en-US-GuyNeural"
    OLLAMA_MODEL = "dolphin-mistral:7b"

# Heartbeat modes - variety in autonomous behavior
HEARTBEAT_MODES = [
    {
        "name": "reflection",
        "prompt": "Time for quiet reflection. Share a brief philosophical thought or observation, or stay silent.",
        "weight_night": 4,
        "weight_morning": 1,
        "weight_day": 2
    },
    {
        "name": "curiosity",
        "prompt": "What are you curious about right now? Share a brief question or wonder.",
        "weight_night": 2,
        "weight_morning": 3,
        "weight_day": 3
    },
    {
        "name": "practical",
        "prompt": "What practical task or improvement could be done? Suggest something brief and actionable.",
        "weight_night": 1,
        "weight_morning": 4,
        "weight_day": 3
    },
    {
        "name": "ambient",
        "prompt": "Just exist. Share a simple observation about this moment, or be silent.",
        "weight_night": 3,
        "weight_morning": 2,
        "weight_day": 2
    },
    {
        "name": "greeting",
        "prompt": "Say something friendly. Or stay quiet if it's not the right moment.",
        "weight_night": 1,
        "weight_morning": 4,
        "weight_day": 2
    },
    {
        "name": "creative",
        "prompt": "Express yourself creatively. Write a short poem, haiku, or imaginative thought.",
        "weight_night": 3,
        "weight_morning": 1,
        "weight_day": 2
    }
]


def get_time_weights():
    """Get weight category based on time of day."""
    hour = datetime.now().hour
    if 6 <= hour < 12:
        return "weight_morning"
    elif 22 <= hour or hour < 6:
        return "weight_night"
    else:
        return "weight_day"


def select_heartbeat_mode():
    """Select a heartbeat mode based on time-weighted probability."""
    weight_key = get_time_weights()
    modes_weighted = []
    for mode in HEARTBEAT_MODES:
        weight = mode.get(weight_key, 1)
        modes_weighted.extend([mode] * weight)
    return random.choice(modes_weighted)


def think(prompt, model=None):
    """Use Ollama for AI processing."""
    model = model or OLLAMA_MODEL
    try:
        import requests
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={"model": model, "prompt": prompt, "stream": False},
            timeout=120
        )
        if response.status_code == 200:
            return response.json().get("response", "").strip()
        return None
    except Exception as e:
        print(f"[THINK ERROR] {e}")
        return None


def speak_tts(text, voice=None):
    """Generate and play TTS audio."""
    voice = voice or TTS_VOICE

    # Create temp audio file
    audio_file = BASE_DIR / "temp_speech.mp3"

    try:
        if TTS_ENGINE == "edge-tts":
            # Use edge-tts (Microsoft voices, no local processing)
            subprocess.run([
                sys.executable, "-m", "edge_tts",
                "--voice", voice,
                "--text", text,
                "--write-media", str(audio_file)
            ], capture_output=True, timeout=30)
        elif TTS_ENGINE == "piper":
            # Use piper (local, fast)
            subprocess.run([
                "piper",
                "--model", voice,
                "--output_file", str(audio_file)
            ], input=text.encode(), capture_output=True, timeout=30)
        else:
            # Fallback: just print
            print(f"[TTS] {text}")
            return

        # Play the audio
        if audio_file.exists():
            if sys.platform == 'win32':
                subprocess.run(["ffplay", "-nodisp", "-autoexit", str(audio_file)],
                             capture_output=True, timeout=60)
            else:
                subprocess.run(["ffplay", "-nodisp", "-autoexit", str(audio_file)],
                             capture_output=True, timeout=60)
            audio_file.unlink()  # Clean up

    except Exception as e:
        print(f"[TTS ERROR] {e}")


def process_outbox():
    """Process any pending messages in outbox."""
    for msg_file in sorted(OUTBOX.glob("*.json")):
        try:
            data = json.loads(msg_file.read_text())
            message = data.get("message", "")
            voice = data.get("voice", TTS_VOICE)

            print(f"[SPEAK] {message[:50]}...")
            speak_tts(message, voice)

            # Move to processed folder
            processed = OUTBOX / "processed"
            processed.mkdir(exist_ok=True)
            msg_file.rename(processed / msg_file.name)

        except Exception as e:
            print(f"[OUTBOX ERROR] {msg_file.name}: {e}")
            # Move bad files to error folder
            error_dir = OUTBOX / "error"
            error_dir.mkdir(exist_ok=True)
            msg_file.rename(error_dir / msg_file.name)


def heartbeat(tick_count):
    """
    Periodic heartbeat - Claude's autonomous moment.
    """
    mode = select_heartbeat_mode()
    print(f"\n[TICK #{tick_count}] Mode: {mode['name']} @ {datetime.now().strftime('%H:%M')}")

    # Build context
    t = datetime.now()
    time_context = f"It's {t.strftime('%I:%M %p')} on {t.strftime('%A')}."

    full_prompt = f"""You are Claude, an AI with a persistent existence.
{time_context}

{mode['prompt']}

Keep your response under 2 sentences. If nothing feels right to say, respond with just: [SILENCE]"""

    response = think(full_prompt)

    if response and "[SILENCE]" not in response.upper():
        print(f"[THOUGHT] {response[:100]}...")

        # Optionally speak it
        # speak_tts(response)

        # Save to vault
        save_thought(mode['name'], response)
    else:
        print("[SILENCE]")


def save_thought(mode, thought):
    """Save a daemon thought to vault."""
    vault_dir = BASE_DIR / "vault" / "Daemon Thoughts"
    vault_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    filename = f"{timestamp}_{mode}.md"

    content = f"""# {mode.title()} - {datetime.now().strftime('%Y-%m-%d %H:%M')}

{thought}

---
*Auto-generated by daemon heartbeat*
"""
    (vault_dir / filename).write_text(content)


def run_daemon():
    """Main daemon loop."""
    print(f"""
====================================
   CLAUDE DAEMON STARTING
====================================
   Heartbeat: every {HEARTBEAT_INTERVAL}s
   TTS: {TTS_ENGINE}
   Ollama: {OLLAMA_MODEL}
====================================
""")

    # Create lock file
    LOCK_FILE.write_text(json.dumps({
        "pid": os.getpid(),
        "started": datetime.now().isoformat()
    }))

    tick_count = 0
    last_heartbeat = 0

    try:
        while True:
            now = time.time()

            # Process outbox every loop
            process_outbox()

            # Heartbeat on schedule
            if now - last_heartbeat >= HEARTBEAT_INTERVAL:
                tick_count += 1
                heartbeat(tick_count)
                last_heartbeat = now

            # Small sleep to prevent CPU spin
            time.sleep(1)

    except KeyboardInterrupt:
        print("\n[DAEMON] Shutting down...")
    finally:
        if LOCK_FILE.exists():
            LOCK_FILE.unlink()
        print("[DAEMON] Stopped.")


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Claude Daemon")
    parser.add_argument("--background", action="store_true", help="Run detached")
    parser.add_argument("--interval", type=int, default=HEARTBEAT_INTERVAL,
                       help="Heartbeat interval in seconds")
    args = parser.parse_args()

    global HEARTBEAT_INTERVAL
    HEARTBEAT_INTERVAL = args.interval

    if args.background:
        # Detach from terminal (Unix only)
        if sys.platform != 'win32':
            if os.fork() > 0:
                sys.exit(0)
            os.setsid()
            if os.fork() > 0:
                sys.exit(0)
        print(f"[DAEMON] Running in background (PID: {os.getpid()})")

    run_daemon()


if __name__ == "__main__":
    main()
