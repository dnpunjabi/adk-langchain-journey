"""
Level 12: Advanced Streaming & HITL Comparison — adk_level12_comparison

This script demonstrates how the bare-metal Google Gen AI SDK handles the same 
concepts as LangGraph's Level 12:
1. Streaming Tokens: Natively supported via `.send_message_stream()`.
2. Human-in-the-Loop: Unlike LangGraph, the ADK doesn't have an orchestrator that pauses. 
   Instead, when the LLM returns a `function_call` part, we manually pause our script, 
   ask the user, and then manually submit a `function_response` part back to the chat.
"""

import os
from google import genai
from google.genai import types
from dotenv import load_dotenv
import time

load_dotenv()

# --- 1. A High-Stakes Tool ---
def get_refund_tool():
    """Defines the refund tool schema for the ADK."""
    return types.Tool(
        function_declarations=[
            types.FunctionDeclaration(
                name="refund_customer",
                description="Refunds a customer. This is a HIGH STAKES action.",
                parameters=types.Schema(
                    type=types.Type.OBJECT,
                    properties={
                        "order_id": types.Schema(type=types.Type.STRING),
                        "amount": types.Schema(type=types.Type.NUMBER),
                    },
                    required=["order_id", "amount"],
                ),
            )
        ]
    )

def execute_refund(order_id: str, amount: float) -> str:
    """The actual python function executed after human approval."""
    return f"Successfully refunded ${amount} to order {order_id}."

# --- 2. State Management ---
# Because there is no `MemorySaver` like LangGraph, we must hold the
# `chat` session object in memory manually to preserve the conversation.
class ADKLevel12State:
    def __init__(self):
        self.client = genai.Client()
        self.chat = self.client.chats.create(
            model=os.getenv("MODEL", "gemini-2.5-flash"),
            config=types.GenerateContentConfig(
                tools=[get_refund_tool()],
                system_instruction="You are an Acme Corp Billing Assistant. You can process refunds if the user asks. Always be polite.",
                temperature=0.1
            )
        )
        self.pending_tool_call = None

global_sessions = {}

def get_session(thread_id: str):
    if thread_id not in global_sessions:
        global_sessions[thread_id] = ADKLevel12State()
    return global_sessions[thread_id]


# --- 3. Execution Hooks for Streamlit ---
def stream_agent_response(query: str, thread_id: str):
    session = get_session(thread_id)
    chat = session.chat
    
    # We send the message and stream the response
    response_stream = chat.send_message_stream(query)
    
    full_text = ""
    is_interrupted = False
    requested_tool = None
    
    for chunk in response_stream:
        # Check if the model decided to call a function instead of text
        if chunk.function_calls:
            for fc in chunk.function_calls:
                requested_tool = {
                    "name": fc.name,
                    "args": fc.args
                }
                # Store it in the session so we know what to resume later
                session.pending_tool_call = fc
                is_interrupted = True
            break # We stop streaming because an action is required
            
        if chunk.text:
            full_text += chunk.text
            # Smooth out the visual streaming for Streamlit
            words = chunk.text.split(" ")
            for i, word in enumerate(words):
                if i < len(words) - 1:
                    yield word + " "
                else:
                    yield word
                time.sleep(0.015)
            
    yield {
        "type": "done",
        "full_text": full_text,
        "is_interrupted": is_interrupted,
        "requested_tool": requested_tool
    }

def approve_and_resume(thread_id: str, approved: bool):
    session = get_session(thread_id)
    chat = session.chat
    
    if not session.pending_tool_call:
        return "No pending tool call to resume."
        
    fc = session.pending_tool_call
    
    if approved:
        # Execute the Python function
        result_str = execute_refund(**fc.args)
    else:
        result_str = "Error: Human Administrator DENIED the action."
        
    # We must explicitly tell the LLM what happened when we ran (or denied) the tool
    function_response = types.Part.from_function_response(
        name=fc.name,
        response={"result": result_str}
    )
    
    # Clear the pending call
    session.pending_tool_call = None
    
    # Send the function result BACK to the model so it can resume generating its reply
    agent_reply = chat.send_message(function_response)
    
    return agent_reply.text
