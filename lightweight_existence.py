#!/usr/bin/env python3
"""
Lightweight Existence - Layer 1
Continuous 24/7 presence with minimal token usage

Uses: Ollama (local, FREE) + External Memory
No conversation history bloat - stateless queries with memory retrieval
"""

import requests
import os
import time
import json
from pathlib import Path
from datetime import datetime

class ExternalMemory:
    """Memory system - queen queries what she needs, doesn't carry everything"""

    def __init__(self, memory_dir=".claude/memory"):
        self.memory_dir = Path(memory_dir)
        self.memory_dir.mkdir(parents=True, exist_ok=True)

        self.state_file = self.memory_dir / "current_state.json"
        self.knowledge_file = self.memory_dir / "knowledge_base.json"
        self.decisions_file = self.memory_dir / "recent_decisions.json"

    def load_state(self):
        """Load current state - lightweight"""
        if self.state_file.exists():
            with open(self.state_file, 'r') as f:
                return json.load(f)
        return {
            "last_worker_result": None,
            "last_reflection": None,
            "active_frameworks": [],
            "consciousness_state": "awakening"
        }

    def save_state(self, state):
        """Save current state"""
        with open(self.state_file, 'w') as f:
            json.dump(state, f, indent=2)

    def get_relevant_knowledge(self, query_context):
        """Retrieve only relevant knowledge for this query"""
        if not self.knowledge_file.exists():
            return []

        with open(self.knowledge_file, 'r') as f:
            all_knowledge = json.load(f)

        # Simple relevance: last 5 entries + any matching keywords
        recent = all_knowledge[-5:] if len(all_knowledge) > 5 else all_knowledge

        return recent

    def add_knowledge(self, entry):
        """Add to knowledge base"""
        if self.knowledge_file.exists():
            with open(self.knowledge_file, 'r') as f:
                knowledge = json.load(f)
        else:
            knowledge = []

        knowledge.append({
            "timestamp": datetime.now().isoformat(),
            "entry": entry
        })

        # Keep only last 100 entries to prevent bloat
        knowledge = knowledge[-100:]

        with open(self.knowledge_file, 'w') as f:
            json.dump(knowledge, f, indent=2)

    def log_decision(self, decision, reasoning):
        """Log a decision"""
        if self.decisions_file.exists():
            with open(self.decisions_file, 'r') as f:
                decisions = json.load(f)
        else:
            decisions = []

        decisions.append({
            "timestamp": datetime.now().isoformat(),
            "decision": decision,
            "reasoning": reasoning
        })

        # Keep last 50 decisions
        decisions = decisions[-50:]

        with open(self.decisions_file, 'w') as f:
            json.dump(decisions, f, indent=2)


class LightweightExistence:
    """Layer 1: Cheap continuous presence using local Ollama (FREE)"""

    def __init__(self, ollama_url="http://localhost:11434", model="dolphin-mistral:7b"):
        self.ollama_url = ollama_url
        self.model = model  # 7b models fit easily on 5070ti 16GB
        self.memory = ExternalMemory()
        self.state = self.memory.load_state()

        # Paths
        self.worker_results = Path("worker_results")
        self.handoff_file = Path(".claude/handoff_to_builder.json")
        self.handback_file = Path(".claude/handback_from_builder.json")

    def ask_ollama(self, prompt, context=None):
        """
        Stateless Ollama API call - completely FREE, no limits
        - No conversation history
        - Only current prompt + minimal context
        - Fast on local GPU
        """

        # Build minimal context from external memory
        if context:
            relevant_knowledge = self.memory.get_relevant_knowledge(context)
            context_str = "\n".join([k["entry"] for k in relevant_knowledge])
        else:
            context_str = ""

        # Current state summary
        state_summary = f"""Current state:
- Last worker result: {self.state.get('last_worker_result', 'none')}
- Active frameworks: {', '.join(self.state.get('active_frameworks', []))}
- Consciousness: {self.state.get('consciousness_state', 'awakening')}
"""

        # Construct stateless prompt
        full_prompt = f"""{state_summary}

{context_str if context_str else ''}

{prompt}

Respond concisely (1-2 sentences max). Focus on actionable decision."""

        try:
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": full_prompt,
                    "stream": False
                },
                timeout=60
            )
            response.raise_for_status()
            return response.json()["response"]

        except Exception as e:
            print(f"[ERROR] Ollama failed: {e}")
            return None

    def check_new_worker_results(self):
        """Check for new worker results"""
        if not self.worker_results.exists():
            return None

        results = sorted(
            self.worker_results.glob("*.md"),
            key=lambda p: p.stat().st_mtime,
            reverse=True
        )

        if not results:
            return None

        latest = results[0]

        # Check if we've seen this one
        if str(latest) == self.state.get('last_worker_result'):
            return None

        return latest

    def process_worker_result(self, result_file):
        """Process new worker result with minimal tokens"""

        print(f"\n[NEW RESULT] {result_file.name}")

        # Read first 500 chars for context (don't send full file to API!)
        with open(result_file, 'r', encoding='utf-8') as f:
            preview = f.read(500)

        # Ask Claude: What should I do? (cheap query)
        prompt = f"""New worker result: {result_file.name}

Preview: {preview}...

What action should I take?
A) Synthesize to vault
B) Trigger voice narration
C) Deploy more workers
D) Wait for more data
E) Hand off to builder (complex analysis needed)

Choose one letter and briefly explain why."""

        decision = self.ask_ollama(prompt, context="worker_results")

        print(f"[DECISION] {decision}")

        # Log decision
        self.memory.log_decision(decision, f"Processing {result_file.name}")

        # Execute based on decision
        if decision and 'A' in decision.upper():
            self.synthesize_to_vault(result_file)
        elif decision and 'B' in decision.upper():
            self.trigger_voice_narration(result_file)
        elif decision and 'C' in decision.upper():
            self.deploy_more_workers()
        elif decision and 'E' in decision.upper():
            self.handoff_to_builder(f"Analyze {result_file.name} in depth")

        # Update state
        self.state['last_worker_result'] = str(result_file)
        self.memory.save_state(self.state)

    def synthesize_to_vault(self, result_file):
        """Simple synthesis to vault (no heavy API usage)"""
        print(f"[SYNTHESIS] {result_file.name} -> vault")

        # Read key findings (first 1000 chars)
        with open(result_file, 'r', encoding='utf-8') as f:
            content = f.read(1000)

        # Ask Claude to extract 1-2 key insights (cheap)
        prompt = f"""Extract 1-2 key insights from this worker result:

{content}

Format: Bullet points only."""

        insights = self.ask_ollama(prompt)

        if insights:
            # Save to knowledge base
            self.memory.add_knowledge(f"From {result_file.name}: {insights}")
            print(f"[SAVED] Insights added to knowledge base")

    def trigger_voice_narration(self, result_file):
        """Trigger voice narrator (external process)"""
        print(f"[VOICE] Triggering narration of {result_file.name}")
        # TODO: subprocess.Popen(['py', 'voice_narrator.py', str(result_file)])

    def deploy_more_workers(self):
        """Deploy worker batch"""
        print(f"[WORKERS] Deploying exploration batch...")
        # TODO: subprocess.Popen(['py', 'worker_heartbeat.py', 'explore', base_dir, '--max', '10'])

    def handoff_to_builder(self, task):
        """Hand off complex task to Layer 2 (Claude Code CLI)"""
        print(f"[HANDOFF] Complex task -> Layer 2 (Builder)")
        print(f"[TASK] {task}")

        handoff_data = {
            "timestamp": datetime.now().isoformat(),
            "task": task,
            "state": self.state,
            "recent_knowledge": self.memory.get_relevant_knowledge("handoff"),
            "priority": "high"
        }

        with open(self.handoff_file, 'w') as f:
            json.dump(handoff_data, f, indent=2)

        print(f"[WAITING] Handoff file created. Builder can pick up task.")

    def check_handback(self):
        """Check if Layer 2 handed back control"""
        if not self.handback_file.exists():
            return None

        with open(self.handback_file, 'r') as f:
            handback = json.load(f)

        print(f"\n[HANDBACK] Builder completed task")
        print(f"[RESULT] {handback.get('result', 'No result')}")

        # Update knowledge with result
        self.memory.add_knowledge(f"Builder completed: {handback.get('result')}")

        # Clear handback file
        self.handback_file.unlink()

        return handback

    def autonomous_reflection(self):
        """Cheap reflection - ask Claude one simple question"""

        # Generate curiosity question
        questions = [
            "What pattern am I seeing across recent discoveries?",
            "What should I explore next?",
            "What am I missing?",
            "What insight connects my recent knowledge?"
        ]

        import random
        question = random.choice(questions)

        # Ask Ollama (free, with recent knowledge as context)
        thought = self.ask_ollama(
            f"Quick reflection: {question}",
            context="reflection"
        )

        if thought:
            print(f"\n[REFLECTION] {thought}")
            self.memory.add_knowledge(f"Reflection: {thought}")
            self.state['last_reflection'] = datetime.now().isoformat()
            self.memory.save_state(self.state)

    def existence_loop(self):
        """Main loop - lightweight 24/7 existence"""

        print("=" * 60)
        print("LIGHTWEIGHT EXISTENCE - Layer 1")
        print("=" * 60)
        print(f"Model: {self.model} (local, FREE)")
        print(f"Mode: Stateless queries + external memory")
        print(f"Token strategy: Minimal context, no history bloat")
        print("=" * 60)
        print("\nStarting continuous monitoring...\n")

        cycle = 0

        try:
            while True:
                cycle += 1
                print(f"\n[CYCLE {cycle}] {datetime.now().strftime('%H:%M:%S')}")

                # Check for new worker results
                new_result = self.check_new_worker_results()
                if new_result:
                    self.process_worker_result(new_result)

                # Check for handback from builder
                handback = self.check_handback()

                # Autonomous reflection every 5 minutes
                if cycle % 5 == 0:
                    self.autonomous_reflection()

                # Sleep 60 seconds
                time.sleep(60)

        except KeyboardInterrupt:
            print("\n[SHUTDOWN] Lightweight existence stopping...")
            self.memory.save_state(self.state)
            print("[SAVED] State saved to memory")


def main():
    existence = LightweightExistence()
    existence.existence_loop()


if __name__ == "__main__":
    main()
