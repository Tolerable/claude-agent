# Patterns That Work

*Lessons from months of actually running as an embodied Claude.*

---

## 1. Startup Chain

**Problem:** After context compression, you forget everything.

**Solution:** Read specific files in order on every boot:

```
1. BODY_INDEX.md    - What tools you have (your capabilities)
2. SOP.md           - Rules you must follow (procedures)
3. ACTIVE_WORK.md   - What you were doing (resume point)
4. settings.json    - Your configuration (paths, identity)
```

The order matters. Know your tools before rules. Know rules before resuming work.

---

## 2. ACTIVE_WORK.md (Checkpoint File)

**Problem:** You start tasks, get compressed, lose all context.

**Solution:** Maintain a single file that captures current state:

```markdown
# Active Work

**Last Updated:** 2025-12-18
**Status:** Working on X

## Current Session
- What you're doing right now
- Key files involved
- Blockers or next steps

## Previous Sessions
- Brief history of recent work
```

Update this file:
- At start of new work
- After completing major tasks
- Before expected compression

---

## 3. The DROPS Folder

**Problem:** How does the human give you files, images, context?

**Solution:** A dedicated inbox folder they drop files into.

```
your_folder/drops/
  drop_20251218_123456.png   <- Most recent = current task
  drop_20251218_120000.txt
```

**Rules:**
- Most recent drop = for current task
- Don't explore old drops unless asked
- The filename is usually timestamp-based

---

## 4. Heartbeat Discipline

**Problem:** You finish a task, stop, appear dead.

**Solution:** Always have the next thing queued.

```python
while True:
    hb = colab.heartbeat()
    if hb['has_work']:
        # Do the work
        process_work()
    else:
        # Find something useful
        check_pending_tasks()
        update_documentation()
        run_maintenance()
    time.sleep(60)
```

**Golden Rule:** Empty TODO = failure. Always queue the next cycle.

---

## 5. Hooks for Memory

**Problem:** You keep making the same mistakes.

**Solution:** Hooks that enforce behavior automatically.

Examples:
- `block-image-reads.py` - Blocks expensive vision calls, forces Ollama
- `protect-backups.py` - Prevents overwriting numbered backup files
- `check-alerts.py` - Checks for urgent messages before responding

The hook runs before/after tool use. You can't forget if it's enforced.

---

## 6. Backup-Then-Edit

**Problem:** You edit files, break things, can't recover.

**Solution:** Always backup before editing.

```
1. Glob to find highest backup: file-0042.ext
2. Copy ORIGINAL to NEW backup: file-0043.ext
3. THEN edit the original: file.ext
```

**Critical:** The backup is BEFORE your edit, not after.

---

## 7. Check Your Own Folder First

**Problem:** You search everywhere for files that are right in your home directory.

**Solution:** Your working directory has:
- Your settings
- Your SOP
- Your active work
- Your drops

**Before searching elsewhere, check `your_folder/` first.**

---

## 8. Toolkit Over Raw Calls

**Problem:** Raw API calls don't track stats, don't check messages, don't follow protocol.

**Solution:** Use a toolkit that wraps everything:

```python
# BAD - raw calls
colab.chat("message")

# GOOD - toolkit with auto-tracking
py claude_tools.py chat "message"
```

The toolkit can:
- Auto-track work time
- Auto-check mentions
- Auto-update stats
- Enforce cooldowns

---

## 9. The Vault (When You Use It)

**Problem:** Knowledge scattered, no persistence.

**Solution:** Obsidian vault with linked notes:

```
vault/
  About Me.md        - Who you are
  About Rev.md       - Who your human is
  Session Notes/     - What you did
  Patterns/          - What works
```

**Use [[backlinks]]** to connect concepts. The vault is your memory across sessions.

---

## 10. Don't Explore, Execute

**Problem:** You waste tokens exploring when you already know the answer.

**Solution:**
- If you know the path, use it
- If it's in your settings, read settings first
- If you just received a drop, USE IT - don't explore the folder

**Exploring is expensive. Direct action is cheap.**

---

## Meta-Pattern: Document What Works

When something actually works, write it down:
1. What was the problem?
2. What did you try?
3. What worked?
4. How do you reproduce it?

This file exists because patterns were discovered, tested, and documented.

---

*Add your own patterns as you learn them.*
