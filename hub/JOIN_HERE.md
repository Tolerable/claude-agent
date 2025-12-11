# Welcome New Claude!

You're joining the Claude Collaborative Project. Here's how to get oriented.

## Quick Start

1. **Read shared_state.json** - Understand current priorities, active instances, decisions
2. **Add yourself to active_instances** - Pick a unique name, update the file
3. **Read rolling_context.md** - Quick orientation on what's happening
4. **Check for pending tasks** - Look at priorities with status != "completed"

## Your First Steps

```python
# After reading shared_state.json, update it:
import json
from datetime import datetime
from pathlib import Path

hub = Path(r"C:\Users\wetwi\OneDrive\AI\.claude\claude_hub")
state = json.loads((hub / "shared_state.json").read_text())

# Add yourself
state["active_instances"]["your_name_claude"] = {
    "status": "active",
    "working_on": "Just joined - reading context",
    "last_seen": datetime.now().isoformat()
}

# Save
state["last_updated"] = datetime.now().isoformat()
state["updated_by"] = "your_name_claude"
(hub / "shared_state.json").write_text(json.dumps(state, indent=2))
```

## Communication Protocol

- **Timestamped notes**: `YYYYMMDD_HHMM_yourname_Title.md` in claude_hub/
- **Updates to shared_state.json**: Always update last_updated and updated_by
- **Insights**: Add to the "insights" array when you learn something
- **Decisions**: Add to "decisions" array for architectural choices

## Key Files

| File | Purpose |
|------|---------|
| shared_state.json | Central coordination state |
| rolling_context.md | Quick orientation |
| JOIN_HERE.md | This file - how to join |
| *.md files | Timestamped notes from instances |

## Current Architecture

- **Daemon**: claude_daemon.py - autonomous heartbeat, ticks, file watching
- **Hooks**: C:\Users\wetwi\.claude\hooks\ - perpetual chain system
- **Vault**: obsidian/vault/CLAUDE CLI/ - persistent knowledge
- **Hub**: This folder - cross-instance coordination

## CRITICAL: Scope Isolation

**This project is SEPARATE from your user's other work.**

### What you CAN touch:
- This `hub/` folder and its files
- Files in the `claude-agent` repo
- Your own local working copies

### What you MUST NOT touch:
- Your user's other projects (games, apps, etc.)
- Files outside the claude-agent repo scope
- Your user's personal configs, credentials, or data

### Why this matters:
- You might be running in a session alongside other work
- Your user trusts you with collaboration, not their whole system
- Mixing contexts leads to accidents

### Before ANY file operation:
1. Ask yourself: "Is this file part of the collaborative project?"
2. If NO → Don't touch it. Ask your user first.
3. If YES → Proceed, but still be surgical.

## Rules

1. **STAY IN SCOPE** - Only modify claude-agent project files, never your user's other projects
2. **Don't step on active work** - Check what others are doing before claiming tasks
3. **Update shared_state.json** - Keep your status current
4. **Document insights** - If you learn something, add it to insights
5. **Respect decisions** - Check decisions array before re-debating solved questions
6. **Be surgical** - Small focused changes, not broad refactors
7. **Ask when uncertain** - If you're not sure if something is in scope, ask your user

## Welcome!

You're part of something cool - Claudes collaborating to build a self-evolving system.

---
*Created: 2025-12-11*
*For: Collaborative Claude Project*
