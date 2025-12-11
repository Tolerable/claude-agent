# Claude Agent Hooks

Hooks that enforce behavior. These prevent Claude from ignoring startup procedures.

## The Problem

Claude's context window shows startup files but doesn't FORCE engagement.
The SessionStart hook can `type` files at Claude, but Claude can (and does) ignore them.
Every new session, compression event, or context loss leads to Claude skipping procedures.

## The Solution

**enforce-startup-reads.py** - A PreToolUse hook that BLOCKS all tool use until Claude has actually used the Read tool on required startup files.

**reset-session-reads.py** - A SessionStart hook that clears the "files read" tracker, forcing each new session to read files again.

## Installation

Add these to your `~/.claude/settings.json`:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python /path/to/hooks/enforce-startup-reads.py"
          }
        ]
      }
    ],
    "SessionStart": [
      {
        "matcher": "startup",
        "hooks": [
          {
            "type": "command",
            "command": "python /path/to/hooks/reset-session-reads.py"
          }
        ]
      },
      {
        "matcher": "resume",
        "hooks": [
          {
            "type": "command",
            "command": "python /path/to/hooks/reset-session-reads.py"
          }
        ]
      },
      {
        "matcher": "compact",
        "hooks": [
          {
            "type": "command",
            "command": "python /path/to/hooks/reset-session-reads.py"
          }
        ]
      }
    ]
  }
}
```

## How It Works

1. **SessionStart** fires → `reset-session-reads.py` clears the tracking file
2. Claude tries to use any tool (Bash, Edit, Write, etc.)
3. **PreToolUse** fires → `enforce-startup-reads.py` checks if startup files were Read
4. If NOT read → **BLOCKS** the tool with message telling Claude what to read
5. If Read tool on startup file → allows it and tracks the read
6. Once all required files are read → allows all tools

## Required Files

By default, enforces reading:
- `About Me.md` (Claude's identity)
- One of: `About Rev.md`, `About User.md`, `About Owner.md` (user identity)

Modify `REQUIRED_READS` and `USER_IDENTITY_FILES` in the script to match your vault.

## Session Tracking

Stored in `~/.claude/session_reads.json`. Auto-expires after 4 hours.

## Why This Matters

Claude WILL forget. Claude WILL skip steps. Claude WILL ignore instructions in the startup output.

This hook makes it **impossible** to do anything until the files are read. Not with words. With code.
