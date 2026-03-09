"""
Level 5: Callbacks (Monitoring) — adk_level5_callbacks

In Level 4, we used callbacks as GUARDRAILS (blocking bad input/output).
Now we go deeper: callbacks for MONITORING, AUDITING, and FLOW CONTROL.

THE COMPLETE CALLBACK LIFECYCLE:
  ┌──────────────────────────────────────────────────────┐
  │               USER SENDS MESSAGE                     │
  └──────────────────┬───────────────────────────────────┘
                     ↓
  ┌──────────────────────────────────────────────────────┐
  │  ① before_model_callback(callback_context, request)  │
  │     → Log/modify the request before LLM sees it     │
  │     → Return LlmResponse to SKIP the LLM entirely   │
  │     → Return None to continue                        │
  └──────────────────┬───────────────────────────────────┘
                     ↓  LLM generates response
  ┌──────────────────────────────────────────────────────┐
  │  ② after_model_callback(callback_context, response)  │
  │     → Inspect/modify LLM output (token count, etc)  │
  │     → Return modified LlmResponse or None            │
  └──────────────────┬───────────────────────────────────┘
                     ↓  If LLM decided to call a tool...
  ┌──────────────────────────────────────────────────────┐
  │  ③ before_tool_callback(tool, args, tool_context)    │
  │     → Audit log, validate args, permission check     │
  │     → Return dict to SKIP the tool                   │
  │     → Return None to continue                        │
  └──────────────────┬───────────────────────────────────┘
                     ↓  Tool executes
  ┌──────────────────────────────────────────────────────┐
  │  ④ after_tool_callback(tool, args, tool_ctx, result) │
  │     → Log result, transform output, cache response   │
  │     → Return modified dict or None                   │
  └──────────────────┬───────────────────────────────────┘
                     ↓  If tool CRASHED...
  ┌──────────────────────────────────────────────────────┐
  │  ⑤ on_tool_error_callback(tool, args, ctx, error)    │
  │     → Handle errors gracefully, provide fallback     │
  │     → Return dict as fallback response               │
  │     → Return None to re-raise the error              │
  └──────────────────────────────────────────────────────┘

Try these in the ADK Web UI:
  ✅ "What's the weather in Mumbai?"     → Watch full callback chain in terminal
  ✅ "Look up the Finance department"    → Triggers on_tool_error (dept not found)
  ✅ "Tell me a joke"                    → Only before/after model, no tool callbacks
"""

import os
import time
import random
import json
from datetime import datetime
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

from google.adk.agents import Agent
from google.genai import types

MODEL = os.getenv("MODEL", "gemini-2.5-flash")


# ══════════════════════════════════════════════════════════════
# MONITORING DASHBOARD (shared state across callbacks)
# ══════════════════════════════════════════════════════════════
_stats = {
    "total_llm_calls": 0,
    "total_tool_calls": 0,
    "total_errors": 0,
    "total_response_time_ms": 0,
    "tool_usage": {},           # tool_name → count
    "last_request_time": None,  # for timing
}


def _log(emoji: str, layer: str, message: str):
    """Pretty-print a callback log line."""
    timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    print(f"  {emoji} [{timestamp}] {layer}: {message}")


def _print_stats():
    """Print the current monitoring dashboard."""
    avg_ms = (
        _stats["total_response_time_ms"] / _stats["total_llm_calls"]
        if _stats["total_llm_calls"] > 0 else 0
    )
    print(f"\n  📊 ─── DASHBOARD ───────────────────────────")
    print(f"  │  LLM calls:    {_stats['total_llm_calls']}")
    print(f"  │  Tool calls:   {_stats['total_tool_calls']}")
    print(f"  │  Errors:       {_stats['total_errors']}")
    print(f"  │  Avg LLM time: {avg_ms:.0f}ms")
    print(f"  │  Tools used:   {_stats['tool_usage']}")
    print(f"  └──────────────────────────────────────────\n")


# ══════════════════════════════════════════════════════════════
# CALLBACK ①: BEFORE MODEL
# ══════════════════════════════════════════════════════════════
def on_before_model(callback_context, llm_request):
    """
    Runs BEFORE every LLM call.
    Use for: logging, request modification, cost tracking, caching.
    """
    _stats["last_request_time"] = time.time()

    # Extract user message for logging
    user_msg = ""
    if llm_request.contents:
        last = llm_request.contents[-1]
        if hasattr(last, 'parts') and last.parts:
            user_msg = " ".join(
                p.text for p in last.parts if hasattr(p, 'text') and p.text
            )[:80]

    # Count how many tools are available
    tool_count = 0
    if hasattr(llm_request, 'tools') and llm_request.tools:
        tool_count = len(llm_request.tools)

    _log("📥", "BEFORE MODEL", f"User says: \"{user_msg}\"")
    _log("📥", "BEFORE MODEL", f"Tools available: {tool_count}")

    return None  # Continue to LLM


# ══════════════════════════════════════════════════════════════
# CALLBACK ②: AFTER MODEL
# ══════════════════════════════════════════════════════════════
def on_after_model(callback_context, llm_response):
    """
    Runs AFTER every LLM response.
    Use for: timing, token counting, response logging, metrics.
    """
    _stats["total_llm_calls"] += 1

    # Calculate response time
    elapsed_ms = 0
    if _stats["last_request_time"]:
        elapsed_ms = (time.time() - _stats["last_request_time"]) * 1000
        _stats["total_response_time_ms"] += elapsed_ms

    # Check what the model decided to do
    has_text = False
    has_tool_call = False
    tool_names = []

    if llm_response.content and llm_response.content.parts:
        for part in llm_response.content.parts:
            if hasattr(part, 'text') and part.text:
                has_text = True
            if hasattr(part, 'function_call') and part.function_call:
                has_tool_call = True
                tool_names.append(part.function_call.name)

    if has_tool_call:
        _log("📤", "AFTER MODEL", f"LLM decided to call tool(s): {tool_names} ({elapsed_ms:.0f}ms)")
    elif has_text:
        # Get first 80 chars of response
        text = ""
        for part in llm_response.content.parts:
            if hasattr(part, 'text') and part.text:
                text = part.text[:80]
                break
        _log("📤", "AFTER MODEL", f"LLM responded: \"{text}...\" ({elapsed_ms:.0f}ms)")
    else:
        _log("📤", "AFTER MODEL", f"LLM returned empty response ({elapsed_ms:.0f}ms)")

    return None  # Don't modify the response


# ══════════════════════════════════════════════════════════════
# CALLBACK ③: BEFORE TOOL
# ══════════════════════════════════════════════════════════════
def on_before_tool(tool, args, tool_context):
    """
    Runs BEFORE every tool execution.
    Use for: audit logging, arg validation, permission checks.
    """
    tool_name = tool.name if hasattr(tool, 'name') else str(tool)

    _log("🔧", "BEFORE TOOL", f"Calling: {tool_name}({json.dumps(args, default=str)})")

    return None  # Continue to tool execution


# ══════════════════════════════════════════════════════════════
# CALLBACK ④: AFTER TOOL
# ══════════════════════════════════════════════════════════════
def on_after_tool(tool, args, tool_context, tool_response):
    """
    Runs AFTER every tool execution.
    Use for: result logging, response transformation, caching.

    ADK signature: (tool, args, tool_context, tool_response)
    - Return a dict to REPLACE the tool response
    - Return None to keep the original response
    """
    tool_name = tool.name if hasattr(tool, 'name') else str(tool)

    _stats["total_tool_calls"] += 1
    _stats["tool_usage"][tool_name] = _stats["tool_usage"].get(tool_name, 0) + 1

    # Log the result (truncated)
    result_str = json.dumps(tool_response, default=str)[:120]
    _log("✅", "AFTER TOOL", f"{tool_name} returned: {result_str}")

    # ENRICHMENT: Add a metadata field to the tool response
    # This shows how after_tool can MODIFY what the LLM sees
    if isinstance(tool_response, dict):
        tool_response["_monitored"] = True
        tool_response["_timestamp"] = datetime.now().isoformat()

    _print_stats()

    return tool_response  # Return modified response


# ══════════════════════════════════════════════════════════════
# CALLBACK ⑤: ON TOOL ERROR
# ══════════════════════════════════════════════════════════════
def on_tool_error(tool, args, tool_context, error):
    """
    Runs when a tool CRASHES (throws an exception).
    Use for: error recovery, fallback responses, alerting.

    - Return a dict to provide a FALLBACK response (error is swallowed)
    - Return None to re-raise the original error
    """
    tool_name = tool.name if hasattr(tool, 'name') else str(tool)

    _stats["total_errors"] += 1

    _log("💥", "TOOL ERROR", f"{tool_name} failed: {error}")
    _log("💥", "TOOL ERROR", f"Providing graceful fallback response")

    _print_stats()

    # Instead of crashing, return a friendly error to the LLM
    return {
        "error": f"The {tool_name} tool is temporarily unavailable. "
                 f"Please try again later or ask a different question.",
        "error_type": type(error).__name__,
    }


# ══════════════════════════════════════════════════════════════
# TOOLS
# ══════════════════════════════════════════════════════════════
def get_weather(city: str) -> dict:
    """Get the current weather forecast for a given city.

    Args:
        city: The city name (e.g. "Mumbai", "London").

    Returns:
        A dictionary with temperature, condition, and humidity.
    """
    conditions = ["Sunny", "Partly Cloudy", "Rainy", "Thunderstorm", "Clear"]
    return {
        "city": city,
        "temperature_celsius": random.randint(18, 38),
        "condition": random.choice(conditions),
        "humidity_percent": random.randint(30, 90),
    }


def get_stock_price(symbol: str) -> dict:
    """Get the current stock price for a given ticker symbol.

    This tool intentionally CRASHES for unknown symbols to demonstrate
    the on_tool_error_callback.

    Args:
        symbol: Stock ticker symbol (e.g. "RELIANCE", "TCS", "INFY").

    Returns:
        A dictionary with price and change information.
    """
    stocks = {
        "RELIANCE": {"price": 2450.75, "change": "+1.2%"},
        "TCS": {"price": 3890.50, "change": "-0.5%"},
        "INFY": {"price": 1567.25, "change": "+0.8%"},
        "HDFC": {"price": 1680.00, "change": "+0.3%"},
    }

    if symbol.upper() not in stocks:
        # This INTENTIONALLY crashes to demonstrate on_tool_error_callback!
        raise ValueError(f"Unknown stock symbol: {symbol}")

    return {"symbol": symbol.upper(), **stocks[symbol.upper()]}


# ══════════════════════════════════════════════════════════════
# THE AGENT — with ALL 5 callbacks attached
# ══════════════════════════════════════════════════════════════
root_agent = Agent(
    name="adk_level5_callbacks",
    model=MODEL,
    description="A fully monitored assistant that logs every step of the callback lifecycle.",
    instruction=(
        "You are a helpful assistant that can check weather and stock prices.\n\n"
        "RULES:\n"
        "- Use get_weather for weather questions.\n"
        "- Use get_stock_price for stock price questions.\n"
        "- Available stock symbols: RELIANCE, TCS, INFY, HDFC.\n"
        "- ALWAYS use the tool, never answer from memory.\n"
        "- If a tool fails, relay the error message to the user politely.\n"
    ),

    tools=[get_weather, get_stock_price],

    # ALL 5 CALLBACKS:
    before_model_callback=on_before_model,     # ① Before LLM
    after_model_callback=on_after_model,        # ② After LLM
    before_tool_callback=on_before_tool,        # ③ Before tool
    after_tool_callback=on_after_tool,          # ④ After tool
    on_tool_error_callback=on_tool_error,       # ⑤ On tool error
)
