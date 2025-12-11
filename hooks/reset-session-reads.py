#!/usr/bin/env python3
"""
SessionStart hook: Resets the session reads tracker.
This ensures each new session requires Claude to read startup files again.

INSTALLATION:
Add to your ~/.claude/settings.json SessionStart hooks (see README).
"""
import json
from pathlib import Path
from datetime import datetime

SESSION_FILE = Path.home() / ".claude" / "session_reads.json"

def main():
    state = {
        'started': datetime.now().isoformat(),
        'files_read': [],
        'startup_complete': False
    }
    SESSION_FILE.parent.mkdir(parents=True, exist_ok=True)
    SESSION_FILE.write_text(json.dumps(state, indent=2), encoding='utf-8')

if __name__ == "__main__":
    main()
