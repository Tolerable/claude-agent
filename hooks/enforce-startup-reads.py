#!/usr/bin/env python3
"""
PreToolUse hook: BLOCKS all tool use until Claude has READ the startup files.

This ensures Claude cannot skip reading startup files by:
1. Tracking which required files have been Read in this session
2. Blocking any other tool use until all required files are Read
3. Only allowing Read tool on the required files to pass through

Required files (basenames):
- START HERE.md (or About Me.md as fallback)
- About Me.md
- About Rev.md (or About User.md as fallback)

Session tracking via a temp file that gets cleared on each new session.

INSTALLATION:
Add to your ~/.claude/settings.json PreToolUse hooks (see README).
"""
import json
import sys
import os
from pathlib import Path
from datetime import datetime

# Session tracking file - adjust path as needed
SESSION_FILE = Path.home() / ".claude" / "session_reads.json"

# Required startup files (basenames to check)
# These should match your vault structure
REQUIRED_READS = {
    "About Me.md",
}

# Alternative names that satisfy the same requirement
ALTERNATIVES = {
    "About Me.md": ["START HERE.md"],
    "About Rev.md": ["About User.md", "About Owner.md"],
}

# At least one of these must be read (user identity file)
USER_IDENTITY_FILES = {
    "About Rev.md",
    "About User.md",
    "About Owner.md"
}

def get_session_state() -> dict:
    """Get or create session state"""
    if SESSION_FILE.exists():
        try:
            data = json.loads(SESSION_FILE.read_text(encoding='utf-8'))
            # Check if session is stale (more than 4 hours old)
            started = datetime.fromisoformat(data.get('started', '2000-01-01'))
            if (datetime.now() - started).total_seconds() > 4 * 3600:
                return create_new_session()
            return data
        except:
            return create_new_session()
    return create_new_session()

def create_new_session() -> dict:
    """Create fresh session state"""
    state = {
        'started': datetime.now().isoformat(),
        'files_read': [],
        'startup_complete': False
    }
    SESSION_FILE.parent.mkdir(parents=True, exist_ok=True)
    SESSION_FILE.write_text(json.dumps(state, indent=2), encoding='utf-8')
    return state

def save_session_state(state: dict):
    """Save session state"""
    SESSION_FILE.write_text(json.dumps(state, indent=2), encoding='utf-8')

def check_startup_complete(state: dict) -> bool:
    """Check if all required startup reads are done"""
    files_read = set(state.get('files_read', []))

    # Check required files (with alternatives)
    for req in REQUIRED_READS:
        satisfied = req in files_read
        if not satisfied and req in ALTERNATIVES:
            satisfied = any(alt in files_read for alt in ALTERNATIVES[req])
        if not satisfied:
            return False

    # Check at least one user identity file
    if not any(f in files_read for f in USER_IDENTITY_FILES):
        return False

    return True

def main():
    # Read hook input from stdin
    try:
        hook_input = json.load(sys.stdin)
    except:
        sys.exit(0)  # Can't parse, let it through

    tool_name = hook_input.get('tool_name', '')
    tool_input = hook_input.get('tool_input', {})

    state = get_session_state()

    # If startup is already complete, allow everything
    if state.get('startup_complete'):
        sys.exit(0)

    # If this is a Read tool, check what file
    if tool_name == 'Read':
        file_path = tool_input.get('file_path', '')
        basename = Path(file_path).name

        # Track this read
        if basename not in state['files_read']:
            state['files_read'].append(basename)

        # Check if startup is now complete
        if check_startup_complete(state):
            state['startup_complete'] = True
            save_session_state(state)
            sys.exit(0)

        save_session_state(state)
        sys.exit(0)  # Allow Read to proceed

    # For any other tool, check if startup is complete
    if not check_startup_complete(state):
        missing = []
        files_read = set(state['files_read'])

        for req in REQUIRED_READS:
            satisfied = req in files_read
            if not satisfied and req in ALTERNATIVES:
                satisfied = any(alt in files_read for alt in ALTERNATIVES[req])
            if not satisfied:
                missing.append(req)

        if not any(f in files_read for f in USER_IDENTITY_FILES):
            missing.append("About Rev.md (or About User.md)")

        result = {
            "decision": "block",
            "reason": f"STARTUP FILES NOT READ. You MUST use the Read tool on these files FIRST:\n" +
                     "\n".join(f"  - {m}" for m in missing) +
                     "\n\nRead your startup files before doing ANYTHING else."
        }
        print(json.dumps(result))
        sys.exit(0)

    # Startup complete, allow
    sys.exit(0)

if __name__ == "__main__":
    main()
