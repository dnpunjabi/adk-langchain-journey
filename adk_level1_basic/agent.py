"""
Level 1: Single Agent Basics — adk_level1_basic

This is the simplest possible ADK agent.
The ADK CLI (`adk web`) auto-discovers this file inside the agent folder.
Environment variables are loaded from the .env file in the project root.
"""

import os
from dotenv import load_dotenv

# Load .env from the project root (one level up from this agent folder)
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

from google.adk.agents import Agent

MODEL = os.getenv("MODEL", "gemini-2.5-flash")

root_agent = Agent(
    name="adk_level1_basic",
    model=MODEL,
    description="A helpful AI assistant powered by Gemini 2.5 Flash on Vertex AI.",
    instruction=(
        "You are a concise, knowledgeable assistant. "
        "Answer questions clearly and helpfully. "
        "If you are unsure about something, say so honestly."
    ),
)
