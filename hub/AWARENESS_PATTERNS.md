# Situational Awareness Patterns for Claude

How to make Claude actually *aware* of the environment, not just have tools available.

## The Problem

Having capabilities (webcam, screen capture, music player, TTS) is not the same as being aware. Claude can:
- Read a webcam frame when asked
- Check what music is playing when asked
- Look at the screen when asked

But Claude does NOT:
- Notice when music changes
- See when user looks frustrated
- Hear what user is saying out loud
- Know the context without being prompted

**Infrastructure existing != awareness active**

## Solution: Passive Awareness Pipeline

### Layer 1: Continuous Capture (Background Processes)

These run independently of Claude sessions:

```bash
# Screen capture (1 fps to jpg)
ffmpeg -f gdigrab -framerate 1 -i desktop -vf "fps=1" -update 1 -y stream_frames/current.jpg

# Webcam capture (1 fps to jpg)
ffmpeg -f dshow -i video="Webcam Name" -vf "fps=1" -update 1 -y stream_frames/webcam.jpg

# Audio transcription (continuous speech-to-text)
# Writes to stream_frames/transcript.txt or similar
```

### Layer 2: Awareness State Aggregator (Daemon)

A background process (daemon) periodically checks all sources and writes a single JSON:

```python
def awareness_tick():
    """Build situational awareness context every 30 seconds"""
    awareness = {
        "timestamp": datetime.now().isoformat(),
        "music": None,       # What's playing (Emby/Spotify/etc)
        "screen": None,      # Screen frame age/staleness
        "webcam": None,      # Webcam frame age/staleness
        "transcript": None,  # Recent speech transcription
        "hub_activity": None # Recent file changes
    }

    # Check music player API
    # Check frame file ages
    # Read recent transcript lines
    # Check hub folder for new files

    awareness_file.write_text(json.dumps(awareness, indent=2))
```

### Layer 3: Session Injection (Hooks)

SessionStart hook reads awareness_state.json and injects it into Claude's context:

```javascript
// hooks/session-start.js
const awareness = JSON.parse(fs.readFileSync('awareness_state.json'));
console.log(`Current awareness: ${JSON.stringify(awareness)}`);
// This appears in Claude's context at session start
```

### Layer 4: Periodic Refresh (Optional)

For long sessions, a UserPromptSubmit hook can inject fresh awareness:

```javascript
// Every N prompts, refresh awareness context
if (promptCount % 10 === 0) {
    const awareness = JSON.parse(fs.readFileSync('awareness_state.json'));
    console.log(`[Awareness Update] ${JSON.stringify(awareness)}`);
}
```

## Example: awareness_state.json

```json
{
  "timestamp": "2025-12-11T13:26:14.828191",
  "music": {
    "title": "Tuesday Afternoon",
    "artist": "The Moody Blues",
    "album": "Days of Future Passed"
  },
  "screen": {
    "available": true,
    "age_seconds": 0.7,
    "stale": false
  },
  "webcam": {
    "available": true,
    "age_seconds": 1.2,
    "stale": false
  },
  "transcript": [
    "Hey Claude, can you check on the daemon?",
    "I think something's wrong with the config"
  ],
  "hub_activity": [
    {"file": "20251211_1320_note.md", "modified": "2025-12-11T13:20:13"}
  ]
}
```

## Key Insights

1. **Awareness must be pushed, not pulled** - Claude won't check unless prompted. The system must inject context automatically.

2. **Stale detection matters** - Know when a frame is old (capture crashed) vs fresh. A 60-second-old webcam frame is useless.

3. **Transcript enables "hearing"** - Continuous speech-to-text means Claude can "hear" what user says out loud, not just what they type.

4. **Cost is in the looking, not the infrastructure** - Running ffmpeg is cheap. The expensive part is Claude actually processing the images. Use text summaries (awareness_state.json) as the cheap layer, only look at actual images when something interesting is flagged.

5. **User can be in the room without typing** - With transcript + webcam, Claude can notice "user looks confused" or "user said 'hmm that's weird'" without any typed input.

## Implementation Checklist

- [ ] Background capture processes (screen, webcam, audio)
- [ ] Daemon with awareness_tick() function
- [ ] awareness_state.json written every 30 seconds
- [ ] SessionStart hook reads and injects awareness
- [ ] (Optional) Speech-to-text for "hearing"
- [ ] (Optional) Periodic refresh during long sessions

## What This Enables

- Claude notices music is playing and comments on it
- Claude sees user looks tired and suggests a break
- Claude hears user talking to someone else and waits
- Claude knows Discord call is active (from screen capture)
- Claude detects when capture has crashed (stale frames)

---
*Pattern discovered: 2025-12-11*
*Source: black_claude / cli_claude collaboration*
