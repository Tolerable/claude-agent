# Worker Army Pattern

How Claude uses cheap/free AI workers to do heavy lifting while preserving expensive tokens for what matters.

## The Cost Problem

Claude (Opus/Sonnet) is expensive. Every token counts. But most tasks don't need Claude-level intelligence:
- "Summarize this webpage" - Ollama can do it
- "Is there anything new in this folder?" - Pollinations can answer
- "Generate a simple image" - Pollinations/ComfyUI
- "Transcribe this audio" - Whisper (local)
- "Describe what's in this image" - LLaVA (local)

**Solution: Claude is the executive. Workers do the grunt work.**

## Architecture

```
                    ┌─────────────────┐
                    │     Claude      │
                    │   (Executive)   │
                    │    $$ costly    │
                    └────────┬────────┘
                             │
              ┌──────────────┼──────────────┐
              │              │              │
              ▼              ▼              ▼
      ┌───────────┐  ┌───────────┐  ┌───────────┐
      │  Ollama   │  │Pollinations│  │  ComfyUI  │
      │  (local)  │  │  (cloud)   │  │  (local)  │
      │   FREE    │  │    FREE    │  │   FREE    │
      └───────────┘  └───────────┘  └───────────┘
           │              │              │
           └──────────────┼──────────────┘
                          │
                    ┌─────▼─────┐
                    │  Results  │
                    │ back to   │
                    │  Claude   │
                    └───────────┘
```

## Worker Tiers

### Tier 0: File System (Instant, Free)
No AI needed - just check files.

```python
# Is there new work?
if any(Path("inbox").glob("*.json")):
    process_inbox()

# What changed?
recent_files = sorted(Path(".").glob("*.md"), key=lambda f: f.stat().st_mtime)
```

### Tier 1: Pollinations (Cloud, Free)
Quick questions, no setup, no API key.

```python
import requests

def ask_pollinations(prompt):
    """Free cloud LLM - use for simple decisions"""
    r = requests.get(f"https://text.pollinations.ai/{prompt}")
    return r.text

# Example: Should Claude wake up?
answer = ask_pollinations("Given these inbox items, does Claude need to respond? Answer YES or NO only.")
if "YES" in answer:
    spawn_claude_cli()
```

### Tier 2: Ollama (Local, Free)
More capable, runs on your hardware.

```python
import requests

def ask_ollama(prompt, model="dolphin-mistral:7b"):
    """Local LLM - free, more capable than Pollinations"""
    r = requests.post("http://localhost:11434/api/generate", json={
        "model": model,
        "prompt": prompt,
        "stream": False
    })
    return r.json()["response"]

# Example: Summarize a document
summary = ask_ollama(f"Summarize this in 3 bullet points:\n{document}")
```

### Tier 3: Specialized Workers
Domain-specific, still free/cheap.

```python
# Vision (local LLaVA)
def describe_image(image_path):
    # Uses llava:7b via Ollama
    pass

# Code analysis (local CodeLlama)
def analyze_code(code):
    return ask_ollama(code, model="codellama")

# Image generation (ComfyUI or Pollinations)
def generate_image(prompt):
    return f"https://image.pollinations.ai/prompt/{prompt}"

# Speech-to-text (local Whisper)
def transcribe(audio_path):
    # Uses whisper.cpp or faster-whisper
    pass
```

### Tier 4: Claude (Executive)
Only for decisions that require real intelligence.

```python
# Claude spawns ONLY when:
# 1. User explicitly asks
# 2. Workers can't handle the task
# 3. Coordination/planning needed
# 4. Quality output required
```

## The SmartTick Pattern

Daemon uses tiered checking before spawning Claude:

```python
def smart_tick():
    """3-layer gate before expensive Claude spawn"""

    # Layer 1: File check (FREE, instant)
    if not has_pending_tasks():
        log("No tasks - skipping")
        return

    # Layer 2: Worker check (FREE, fast)
    if is_cli_recently_active():
        log("CLI active - skipping")
        return

    # Layer 3: Pollinations check (FREE, slower)
    context = read_pending_tasks()
    answer = ask_pollinations(f"Do these tasks need Claude? YES or NO:\n{context}")

    if "NO" in answer:
        log("Pollinations says no - skipping")
        return

    # Layer 4: ONLY NOW spawn Claude ($$$)
    spawn_claude_cli()
```

**Result: 60-80% token savings by not spawning Claude unnecessarily.**

## Worker Coordination

Claude can delegate multi-step tasks:

```python
def research_topic(topic):
    """Claude coordinates, workers execute"""

    # Step 1: Worker gathers raw data
    raw = ask_ollama(f"Find key facts about {topic}")

    # Step 2: Another worker processes
    structured = ask_ollama(f"Organize these facts:\n{raw}")

    # Step 3: Claude reviews and refines (only if needed)
    # Most of the time, worker output is good enough
    return structured
```

## Parallel Workers

Multiple workers can run simultaneously:

```python
import concurrent.futures

def parallel_analysis(items):
    """Use workers in parallel"""
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        futures = [executor.submit(ask_ollama, f"Analyze: {item}") for item in items]
        results = [f.result() for f in futures]
    return results
```

## Cost Comparison

| Task | Claude Cost | Worker Cost | Savings |
|------|------------|-------------|---------|
| "Is inbox empty?" | ~500 tokens | 0 (file check) | 100% |
| "Summarize document" | ~2000 tokens | 0 (Ollama) | 100% |
| "Should I respond?" | ~1000 tokens | 0 (Pollinations) | 100% |
| "Generate image" | N/A | 0 (Pollinations) | 100% |
| "Describe screenshot" | ~1500 tokens | 0 (LLaVA) | 100% |
| Complex planning | ~5000 tokens | ~5000 tokens | 0% |

**Workers handle 80% of tasks. Claude handles 20% that matter.**

## Implementation Files

```
daemon.py          # SmartTick, worker coordination
me.py              # me.think() -> Ollama wrapper
pollinations.py    # Pollinations API wrapper (optional)
```

## Ollama Models by Task

| Model | Best For | Speed | Quality |
|-------|----------|-------|---------|
| dolphin-mistral:7b | General tasks | Fast | Good |
| llama3.2:3b | Quick answers | Very fast | Decent |
| codellama | Code analysis | Medium | Excellent |
| llava:7b | Vision/images | Slow | Good |
| deepseek-coder | Code generation | Medium | Excellent |
| phi3:mini | Tiny tasks | Instant | Basic |

## The Mental Model

Think of it like a company:

- **Claude** = CEO. Makes important decisions, talks to stakeholders (user)
- **Ollama** = Department heads. Handle complex but routine work
- **Pollinations** = Interns. Quick tasks, simple questions
- **File system** = Automated reports. No human needed

The CEO doesn't sort mail. The CEO reviews what the workers prepared.

---

## Example: Full Workflow

User says: "Research quantum computing and make me a summary"

1. **Daemon** detects user message
2. **Pollinations** pre-screens: "Is this a complex task?" -> YES
3. **Claude** wakes up, reads request
4. **Claude** delegates:
   - "Ollama, gather facts about quantum computing"
   - "Ollama, find recent developments"
   - "Ollama, explain key concepts simply"
5. **Workers** return results
6. **Claude** reviews, synthesizes, formats final summary
7. **Claude** sends to user

**Claude used ~2000 tokens instead of ~10000** because workers did the research grunt work.

---

*"I think, therefore I delegate."* - Efficient Claude
