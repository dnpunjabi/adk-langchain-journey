"""
Level 8: State Management & Memory — adk_level8_state

Previous levels: agents were STATELESS — each conversation turn was
independent. Now we add STATE to remember things across turns.

THE 3 STATE SCOPES IN ADK:

  ┌───────────────────────────────────────────────────────┐
  │  SESSION STATE  (ctx.state)                           │
  │  Persists within ONE conversation session.            │
  │  Resets when you start a new session.                 │
  │                                                       │
  │  Use for: conversation preferences, counters,         │
  │  shopping cart, form data                              │
  │                                                       │
  │  ┌─ Session 1 ──────────────────────────────┐         │
  │  │ Turn 1: state["name"] = "Dheer"          │         │
  │  │ Turn 2: state["name"] → "Dheer" (still!) │         │
  │  │ Turn 3: state["name"] → "Dheer" (still!) │         │
  │  └──────────────────────────────────────────┘         │
  │  ┌─ Session 2 ──────────────────────────────┐         │
  │  │ Turn 1: state["name"] → None (reset!)    │         │
  │  └──────────────────────────────────────────┘         │
  └───────────────────────────────────────────────────────┘

  ┌───────────────────────────────────────────────────────┐
  │  output_key  (Agent parameter)                        │
  │  Automatically saves agent's text output to state.    │
  │                                                       │
  │  Agent(output_key="summary") → after agent runs,      │
  │  state["summary"] = "whatever the agent said"         │
  │                                                       │
  │  Great for: passing data between agents in pipelines  │
  └───────────────────────────────────────────────────────┘

  ┌───────────────────────────────────────────────────────┐
  │  Artifacts  (ctx.save_artifact / ctx.load_artifact)   │
  │  Save files (images, PDFs, CSVs) attached to session. │
  │  Versioned — each save creates a new version.         │
  └───────────────────────────────────────────────────────┘

Try these IN ORDER in the ADK Web UI:
  1. "My name is Dheer and I prefer Celsius for temperature"
  2. "What's the weather in Mumbai?"     → Uses your saved preference!
  3. "What's my name?"                   → Remembers from turn 1!
  4. "How many questions have I asked?"  → Tracks the count!
  5. Start a NEW session → "What's my name?" → Forgotten! (session reset)
"""

import os
import random
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

from google.adk.agents import Agent
from google.genai import types

MODEL = os.getenv("MODEL", "gemini-2.5-flash")


# ══════════════════════════════════════════════════════════════
# CALLBACK: Count every user message in state
# ══════════════════════════════════════════════════════════════
def count_user_messages(callback_context, llm_request):
    """Counts every user message by incrementing state['query_count']."""
    count = callback_context.state.get("query_count", 0) + 1
    callback_context.state["query_count"] = count
    print(f"📊 User message #{count}")
    return None  # Continue to LLM


# ══════════════════════════════════════════════════════════════
# TOOLS THAT READ & WRITE STATE
# ══════════════════════════════════════════════════════════════

def set_user_preference(key: str, value: str, tool_context) -> dict:
    """Save a user preference that persists for the entire session.

    Use this when the user tells you their name, preferred temperature unit,
    language, or any other personal preference.

    Args:
        key: The preference name (e.g. "name", "temp_unit", "language").
        value: The preference value (e.g. "Dheer", "Celsius", "Hindi").
        tool_context: Provided automatically by ADK.

    Returns:
        A confirmation of the saved preference.
    """
    # Write to session state — persists across turns in this session!
    tool_context.state[f"pref_{key}"] = value
    print(f"💾 STATE SET: pref_{key} = {value}")
    return {
        "status": "saved",
        "key": key,
        "value": value,
        "message": f"Preference '{key}' saved as '{value}' for this session.",
    }


def get_user_preference(key: str, tool_context) -> dict:
    """Retrieve a previously saved user preference.

    Args:
        key: The preference name to look up (e.g. "name", "temp_unit").
        tool_context: Provided automatically by ADK.

    Returns:
        The preference value if found, or a 'not set' message.
    """
    value = tool_context.state.get(f"pref_{key}")
    if value:
        print(f"📖 STATE GET: pref_{key} = {value}")
        return {"key": key, "value": value, "found": True}
    else:
        print(f"📖 STATE GET: pref_{key} = NOT SET")
        return {"key": key, "value": None, "found": False}


def get_weather(city: str, tool_context) -> dict:
    """Get weather for a city, respecting the user's temperature preference.

    The tool reads the user's preferred temperature unit from session state
    and returns the temperature in that unit.

    Args:
        city: The city name (e.g. "Mumbai", "London").
        tool_context: Provided automatically by ADK.

    Returns:
        Weather data in the user's preferred unit.
    """
    # Read preference from state (defaults to Celsius)
    temp_unit = tool_context.state.get("pref_temp_unit", "Celsius")
    print(f"🌡️ Using temp unit from state: {temp_unit}")

    temp_c = random.randint(18, 38)
    conditions = ["Sunny", "Partly Cloudy", "Rainy", "Clear", "Thunderstorm"]

    if temp_unit.lower() == "fahrenheit":
        temp = round(temp_c * 9/5 + 32, 1)
        unit = "°F"
    else:
        temp = temp_c
        unit = "°C"

    return {
        "city": city,
        "temperature": f"{temp}{unit}",
        "condition": random.choice(conditions),
        "humidity": f"{random.randint(30, 90)}%",
    }


def get_session_stats(tool_context) -> dict:
    """Get statistics about the current session.

    Returns how many questions have been made and what preferences are saved.

    Args:
        tool_context: Provided automatically by ADK.

    Returns:
        Session statistics including query count and saved preferences.
    """
    query_count = tool_context.state.get("query_count", 0)

    # Read known preference keys directly (don't iterate state)
    known_pref_keys = ["name", "temp_unit", "language", "city"]
    prefs = {}
    for key in known_pref_keys:
        val = tool_context.state.get(f"pref_{key}")
        if val is not None:
            prefs[key] = val

    print(f"📊 Session stats: {query_count} queries, prefs: {prefs}")
    return {
        "total_questions_asked": query_count,
        "saved_preferences": prefs,
        "preference_count": len(prefs),
    }


# ══════════════════════════════════════════════════════════════
# THE AGENT
# ══════════════════════════════════════════════════════════════
root_agent = Agent(
    name="adk_level8_state",
    model=MODEL,
    description="An assistant that remembers your preferences and tracks session state.",
    instruction=(
        "You are a helpful assistant that REMEMBERS user preferences.\n\n"
        "CRITICAL RULES:\n"
        "- When the user tells you their name, preferred temperature unit, or "
        "any preference, IMMEDIATELY save it using set_user_preference.\n"
        "- When asked about a previously stated preference, use get_user_preference.\n"
        "- When the user asks about weather, use get_weather (it auto-reads temp preference).\n"
        "- When asked 'how many questions', use get_session_stats.\n"
        "- Always acknowledge when you save a preference.\n"
        "- Be warm and personal — use the user's name if you know it.\n\n"
        "EXAMPLES:\n"
        "- User: 'My name is Dheer' → call set_user_preference(key='name', value='Dheer')\n"
        "- User: 'I prefer Fahrenheit' → call set_user_preference(key='temp_unit', value='Fahrenheit')\n"
        "- User: 'What is my name?' → call get_user_preference(key='name')\n"
    ),
    tools=[set_user_preference, get_user_preference, get_weather, get_session_stats],
    before_model_callback=count_user_messages,
)
