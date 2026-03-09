"""
LangChain Level 12: Advanced - Streaming & Human-in-the-Loop

This script demonstrates two very powerful LangGraph concepts:
1. Streaming Tokens: We don't just wait for the final answer. We stream it word-by-word.
2. Human-in-the-Loop (Interrupts): We pause the graph execution BEFORE it runs a tool, 
                                   asking for human approval, and then resuming it.
"""

import time
import os
from dotenv import load_dotenv

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver

load_dotenv()

# --- 1. A High-Stakes Tool ---
# We want to ask the human before running this tool.
@tool
def refund_customer(order_id: str, amount: float) -> str:
    """Refunds a customer. This is a HIGH STAKES action."""
    # In real life, this hits a Stripe API
    return f"Successfully refunded ${amount} to order {order_id}."

# --- 2. Build the Agent ---
def build_advanced_agent():
    llm = ChatGoogleGenerativeAI(model=os.getenv("MODEL", "gemini-2.5-flash"), temperature=0.1)
    tools = [refund_customer]
    memory = MemorySaver()
    
    system_prompt = (
        "You are an Acme Corp Billing Assistant.\n"
        "You can process refunds if the user asks.\n"
        "Always be polite."
    )
    
    # Notice we add `interrupt_before=["tools"]`
    # This tells LangGraph: "If the LLM decides to use a tool, PAUSE everything."
    app = create_react_agent(
        model=llm,
        tools=tools,
        checkpointer=memory,
        prompt=system_prompt,
        interrupt_before=["tools"]
    )
    return app

# We need a global instance so memory persists across the interruption pause
global_agent_l12 = build_advanced_agent()

# --- 3. Execution Hooks for Streamlit ---

def stream_agent_response(query: str, thread_id: str):
    """
    Runs the agent synchronously to stream tokens word-by-word.
    If it hits a tool, it pauses and waits.
    """
    config = {"configurable": {"thread_id": thread_id}}
    
    full_text = ""
    is_interrupted = False
    requested_tool = None
    
    # We use stream(stream_mode="messages") to catch token-by-token chunks
    for msg_chunk, metadata in global_agent_l12.stream({"messages": [("user", query)]}, config=config, stream_mode="messages"):
        # We only care about chunks coming from the 'agent' node predicting text
        if metadata.get("langgraph_node") == "agent":
            if msg_chunk.content:
                chunk_str = msg_chunk.content
                if isinstance(chunk_str, list):
                     chunk_str = "".join(part.get("text", "") for part in chunk_str if isinstance(part, dict))
                elif not isinstance(chunk_str, str):
                     chunk_str = str(chunk_str)
                     
                if chunk_str:
                    full_text += chunk_str
                    # Streamlit st.write_stream expects a generator yielding strings
                    # Because Gemini models return large chunks natively, we split them by word 
                    # and add a tiny delay to ensure the UI visually streams like ChatGPT.
                    words = chunk_str.split(" ")
                    for i, word in enumerate(words):
                        if i < len(words) - 1:
                            yield word + " "
                        else:
                            yield word
                        time.sleep(0.015)
                
    # After the stream finishes (or pauses), check the state
    state = global_agent_l12.get_state(config)
    
    # LangGraph sets the `next` attribute if the graph is paused
    if state.next:
        is_interrupted = True
        
        # Look at the last message to see what tool the LLM tried to call
        last_message = state.values["messages"][-1]
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            requested_tool = last_message.tool_calls[0]
            
    # Yield a final dictionary holding the state info so the UI knows if it paused
    yield {
        "type": "done", 
        "full_text": full_text, 
        "is_interrupted": is_interrupted,
        "requested_tool": requested_tool
    }

def approve_and_resume(thread_id: str, approved: bool):
    """Resumes the paused graph execution."""
    config = {"configurable": {"thread_id": thread_id}}
    state = global_agent_l12.get_state(config)
    
    if not state.next:
        return "Graph is not paused."
        
    if approved:
        # If approved, we just pass None, and it resumes exactly where it left off 
        # (which is executing the `tools` node)
        response_stream = global_agent_l12.stream(None, config=config, stream_mode="values")
    else:
        # If denied, we must manually inject a ToolMessage saying it was denied,
        # then resume the graph so the LLM knows what happened.
        from langchain_core.messages import ToolMessage
        last_message = state.values["messages"][-1]
        tool_call_id = last_message.tool_calls[0]["id"]
        
        denial_message = ToolMessage(
            tool_call_id=tool_call_id,
            content="Error: Human Administrator DENIED the action.",
            name=last_message.tool_calls[0]["name"]
        )
        
        # We update the state manually, forcing it to skip the `tools` node 
        # and go back to the `agent` node to respond to the denial.
        global_agent_l12.update_state(config, {"messages": [denial_message]}, as_node="tools")
        response_stream = global_agent_l12.stream(None, config=config, stream_mode="values")
        
    # Gather the final response after resuming
    final_text = ""
    for state_update in response_stream:
        # stream_mode="values" yields the FULL state dict at every step
        last_msg = state_update["messages"][-1]
        if last_msg.content:
            final_text = last_msg.content
            if isinstance(final_text, list):
                 final_text = "".join(part.get("text", "") for part in final_text if isinstance(part, dict))
                
    return final_text
