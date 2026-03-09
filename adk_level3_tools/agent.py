"""
Level 3: Custom Tools — adk_level3_tools

This agent demonstrates FUNCTION TOOLS in Google ADK.

KEY CONCEPT:
  Any Python function with type hints + a docstring automatically becomes
  a "tool" that the LLM can decide to call on its own.

  You write:   def get_weather(city: str) -> dict:
  ADK sees:    A tool called "get_weather" that takes a city name and returns weather info
  The LLM:     Decides WHEN to call it based on the user's question

HOW IT WORKS (internally):
  1. User asks: "What's the weather in Mumbai?"
  2. LLM reads the tool descriptions and decides: "I should call get_weather"
  3. LLM generates a function_call: get_weather(city="Mumbai")
  4. ADK executes your Python function and gets the result
  5. ADK sends the result back to the LLM
  6. LLM formats the result into a natural language response

Try these in the ADK Web UI:
  ✅ "What is the weather in Delhi?"         → Calls get_weather tool
  ✅ "What is 15% tip on ₹2400?"             → Calls calculate tool
  ✅ "Who is the manager of Engineering?"     → Calls lookup_employee tool
  ✅ "What time is it in Tokyo?"              → Calls get_current_time tool
  ✅ "What is your name?"                     → No tool needed, LLM answers directly
"""

import os
import random
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

from google.adk.agents import Agent

MODEL = os.getenv("MODEL", "gemini-2.5-flash")


# ══════════════════════════════════════════════════════════════
# TOOL 1: Weather Lookup
# ══════════════════════════════════════════════════════════════
# RULE: Type hints + docstring = the LLM knows what this tool does
def get_weather(city: str) -> dict:
    """Get the current weather forecast for a given city.

    Args:
        city: The name of the city to get weather for (e.g. "Mumbai", "London").

    Returns:
        A dictionary with temperature, condition, and humidity.
    """
    # In a real app, you'd call a weather API like OpenWeatherMap here.
    # For learning, we simulate it with random data.
    conditions = ["Sunny", "Partly Cloudy", "Rainy", "Thunderstorm", "Clear"]
    return {
        "city": city,
        "temperature_celsius": random.randint(18, 38),
        "condition": random.choice(conditions),
        "humidity_percent": random.randint(30, 90),
    }


# ══════════════════════════════════════════════════════════════
# TOOL 2: Calculator
# ══════════════════════════════════════════════════════════════
def calculate(expression: str) -> dict:
    """Evaluate a mathematical expression and return the result.

    Use this tool for any math calculation the user asks for,
    including tips, percentages, conversions, etc.

    Args:
        expression: A mathematical expression as a string (e.g. "2400 * 0.15").

    Returns:
        A dictionary containing the expression and its result.
    """
    try:
        # eval is used here for simplicity — in production, use a safe math parser
        result = eval(expression, {"__builtins__": {}})
        return {"expression": expression, "result": result}
    except Exception as e:
        return {"expression": expression, "error": str(e)}


# ══════════════════════════════════════════════════════════════
# TOOL 3: Company Employee Directory
# ══════════════════════════════════════════════════════════════
def lookup_employee(department: str) -> dict:
    """Look up employees and their roles in a specific department.

    Args:
        department: The department name (e.g. "Engineering", "Sales", "HR").

    Returns:
        A dictionary containing the department info and employee list.
    """
    directory = {
        "engineering": {
            "department": "Engineering",
            "manager": "Priya Sharma",
            "team_size": 25,
            "members": ["Rahul Gupta", "Sneha Patel", "Amit Verma", "Neha Singh"],
        },
        "sales": {
            "department": "Sales",
            "manager": "Vikram Malhotra",
            "team_size": 15,
            "members": ["Anjali Rao", "Karan Mehta", "Divya Joshi"],
        },
        "hr": {
            "department": "Human Resources",
            "manager": "Meera Iyer",
            "team_size": 8,
            "members": ["Suresh Kumar", "Pooja Desai"],
        },
    }
    dept = directory.get(department.lower())
    if dept:
        return dept
    return {"error": f"Department '{department}' not found. Available: Engineering, Sales, HR"}


# ══════════════════════════════════════════════════════════════
# TOOL 4: Current Time in Any Timezone
# ══════════════════════════════════════════════════════════════
def get_current_time(city: str) -> dict:
    """Get the current date and time for a given city.

    Args:
        city: The city name to get the time for (e.g. "Tokyo", "New York", "London").

    Returns:
        A dictionary with the city name, current time, and UTC offset.
    """
    # Simple timezone offsets for common cities
    offsets = {
        "new york": -5, "london": 0, "paris": 1, "berlin": 1,
        "dubai": 4, "mumbai": 5.5, "delhi": 5.5, "kolkata": 5.5,
        "singapore": 8, "tokyo": 9, "sydney": 11,
        "los angeles": -8, "chicago": -6, "hong kong": 8,
    }
    offset = offsets.get(city.lower(), None)
    if offset is not None:
        tz = timezone(timedelta(hours=offset))
        now = datetime.now(tz)
        return {
            "city": city,
            "current_time": now.strftime("%I:%M %p"),
            "date": now.strftime("%A, %B %d, %Y"),
            "utc_offset": f"UTC{'+' if offset >= 0 else ''}{offset}",
        }
    return {"city": city, "error": "City not found in timezone database"}


# ══════════════════════════════════════════════════════════════
# THE AGENT — with all 4 tools attached
# ══════════════════════════════════════════════════════════════
root_agent = Agent(
    name="adk_level3_tools",
    model=MODEL,
    description="A smart assistant that can check weather, do math, look up employees, and tell time.",
    instruction=(
        "You are a helpful assistant with access to several tools.\n\n"
        "RULES:\n"
        "- Use 'get_weather' when asked about weather or temperature.\n"
        "- Use 'calculate' for any math, percentages, or tip calculations.\n"
        "- Use 'lookup_employee' when asked about departments or employees.\n"
        "- Use 'get_current_time' when asked about the time in a city.\n"
        "- For general questions, answer directly without tools.\n"
        "- Always present tool results in a friendly, readable format.\n"
    ),

    # ← This is the magic line: just pass Python functions as a list!
    tools=[get_weather, calculate, lookup_employee, get_current_time],
)
