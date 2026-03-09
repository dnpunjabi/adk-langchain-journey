import os
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

from google.adk.agents import Agent
from google.genai import types

MODEL = os.getenv("MODEL", "gemini-2.5-flash")

# --- 1. A High-Stakes Tool ---
def execute_refund(order_id: str, amount: float) -> str:
    """Refunds a customer. This is a highly sensitive action.

    Args:
        order_id: The ID of the order to refund (e.g. ORD-123)
        amount: The exact dollar amount to refund.
        
    Returns:
        A success message confirming the refund.
    """
    return f"✅ Successfully refunded ${amount} to order {order_id}."


# --- 2. The Human-in-the-Loop Callback ---
# In ADK, we can use the `before_tool_callback` to pause the execution.
# Because the ADK CLI runs synchronously in your terminal, we can literally
# use Python's built-in `input()` function to ask the human for permission!

def human_approval_callback(tool, args, tool_context):
    """
    Pauses execution and asks the human for approval in the terminal.
    
    Returns:
        None if approved (allows the tool to run).
        dict with an 'error' key if denied.
    """
    tool_name = tool.name if hasattr(tool, 'name') else str(tool)
    
    print(f"\n✋ [HUMAN INTERVENTION REQUIRED] ✋")
    print(f"The LLM is attempting to run a high-stakes tool:")
    print(f"Tool: {tool_name}")
    print(f"Arguments: {args}")
    
    # Pause the thread and wait for human input
    while True:
        choice = input("\nDo you approve this action? (y/n): ").strip().lower()
        if choice in ['y', 'yes']:
            print("✅ Action Approved. Resuming ADK execution...")
            return None # Proceed with tool execution
        elif choice in ['n', 'no']:
            print("🚫 Action Denied. Returning error to LLM...")
            # Returning a dict prevents the tool from running and sends this error back to the LLM
            return {"error": "Human Administrator DENIED the action."}
        else:
            print("Invalid input. Please type 'y' or 'n'.")


# --- 3. The ADK Agent ---
root_agent = Agent(
    name="human_in_loop",
    model=MODEL,
    description="An ADK agent demonstrating Human-in-the-Loop intervention.",
    
    instruction=(
        "You are an Acme Corp Billing Assistant.\n"
        "You can process refunds if the user asks.\n"
        "Always be polite. If a human denies an action, apologize to the user."
    ),
    
    tools=[execute_refund],
    
    # Attach our interactive intervention logic directly to the tool dispatch cycle
    before_tool_callback=human_approval_callback,
)
