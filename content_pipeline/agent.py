"""
Level 7: Workflow Agents — Content Pipeline

In Level 6 we used sub_agents for DYNAMIC routing (LLM decides).
Now we use WORKFLOW AGENTS for DETERMINISTIC control flow.

THE 3 WORKFLOW AGENT TYPES:

  ┌────────────────────────────────────────────────────────┐
  │  SequentialAgent                                       │
  │  Runs sub-agents ONE AFTER ANOTHER (like a pipeline)   │
  │                                                        │
  │  Agent A → Agent B → Agent C                           │
  │                                                        │
  │  Use when: steps must happen in order                  │
  │  Example: research → write → review                    │
  └────────────────────────────────────────────────────────┘

  ┌────────────────────────────────────────────────────────┐
  │  ParallelAgent                                         │
  │  Runs sub-agents AT THE SAME TIME (in parallel)        │
  │                                                        │
  │  Agent A ─┐                                            │
  │  Agent B ─┼→ (all run simultaneously)                  │
  │  Agent C ─┘                                            │
  │                                                        │
  │  Use when: independent tasks, speed matters            │
  │  Example: translate to 3 languages at once             │
  └────────────────────────────────────────────────────────┘

  ┌────────────────────────────────────────────────────────┐
  │  LoopAgent                                             │
  │  Repeats sub-agents until ESCALATE or max_iterations   │
  │                                                        │
  │  Agent A → Agent B → (repeat from A)                   │
  │                                                        │
  │  Use when: iterative refinement needed                 │
  │  Example: write draft → reviewer says "improve" → loop │
  └────────────────────────────────────────────────────────┘

THIS EXERCISE — Blog Post Pipeline:
  User provides a topic, and the pipeline runs:

  ┌──────────────────────────────────────────────────────────┐
  │ SEQUENTIAL PIPELINE (runs in order)                      │
  │                                                          │
  │   Step 1: Researcher  → gathers key facts about topic    │
  │                  ↓                                       │
  │   Step 2: ┌─ ParallelAgent ──────────────┐               │
  │           │ Writer A (formal tone)       │               │
  │           │ Writer B (casual tone)       │               │
  │           └─────────────────────────────-┘               │
  │                  ↓                                       │
  │   Step 3: Editor → picks the best version & polishes it  │
  └──────────────────────────────────────────────────────────┘

Try this: "Write a blog post about AI in healthcare"
"""

import os
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

from google.adk.agents import Agent, SequentialAgent, ParallelAgent

MODEL = os.getenv("MODEL", "gemini-2.5-flash")


# ══════════════════════════════════════════════════════════════
# STEP 1: RESEARCHER — gathers key points
# ══════════════════════════════════════════════════════════════
researcher = Agent(
    name="researcher",
    model=MODEL,
    description="Researches a topic and provides key facts and talking points.",
    instruction=(
        "You are a research assistant.\n\n"
        "Given a topic from the user, provide:\n"
        "1. A brief overview (2-3 sentences)\n"
        "2. 3-4 key facts or statistics\n"
        "3. 2-3 interesting angles for a blog post\n\n"
        "Keep your output concise and factual. "
        "This will be used by writers to create a blog post."
    ),
)


# ══════════════════════════════════════════════════════════════
# STEP 2: TWO WRITERS — run in PARALLEL (different tones)
# ══════════════════════════════════════════════════════════════
formal_writer = Agent(
    name="formal_writer",
    model=MODEL,
    description="Writes blog content in a formal, professional tone.",
    instruction=(
        "You are a professional blog writer with a FORMAL tone.\n\n"
        "Using the research provided in the conversation, write a short "
        "blog post (150-200 words) in a formal, professional style.\n\n"
        "Rules:\n"
        "- Use proper business language\n"
        "- Include a compelling title\n"
        "- Label your output as: '📝 FORMAL VERSION'\n"
    ),
)

casual_writer = Agent(
    name="casual_writer",
    model=MODEL,
    description="Writes blog content in a casual, conversational tone.",
    instruction=(
        "You are a blog writer with a CASUAL, fun tone.\n\n"
        "Using the research provided in the conversation, write a short "
        "blog post (150-200 words) in a casual, conversational style.\n\n"
        "Rules:\n"
        "- Use everyday language, humor, and energy\n"
        "- Include emojis where appropriate\n"
        "- Label your output as: '🎉 CASUAL VERSION'\n"
    ),
)

# ParallelAgent — both writers work SIMULTANEOUSLY
parallel_writers = ParallelAgent(
    name="parallel_writers",
    description="Runs formal and casual writers in parallel.",
    sub_agents=[formal_writer, casual_writer],
)


# ══════════════════════════════════════════════════════════════
# STEP 3: EDITOR — picks the best and polishes
# ══════════════════════════════════════════════════════════════
editor = Agent(
    name="editor",
    model=MODEL,
    description="Reviews both blog versions, picks the best, and polishes it.",
    instruction=(
        "You are a senior blog editor.\n\n"
        "You have received TWO versions of a blog post (formal and casual).\n\n"
        "Your job:\n"
        "1. Read both versions\n"
        "2. Pick the BETTER version (or combine best parts)\n"
        "3. Polish it: fix grammar, improve flow, add a strong conclusion\n"
        "4. Output the FINAL polished blog post\n\n"
        "Label your output as: '✅ FINAL BLOG POST'\n"
        "At the end, briefly explain why you chose this version."
    ),
)


# ══════════════════════════════════════════════════════════════
# THE PIPELINE — SequentialAgent orchestrates everything
# ══════════════════════════════════════════════════════════════
# This is the ROOT AGENT that ADK discovers.
# SequentialAgent runs: researcher → parallel_writers → editor
root_agent = SequentialAgent(
    name="content_pipeline",
    description="A content creation pipeline: research → parallel writing → editing.",
    sub_agents=[researcher, parallel_writers, editor],
)
