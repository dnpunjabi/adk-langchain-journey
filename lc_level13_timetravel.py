"""
LangChain Level 13: Advanced - Time Travel & State Forking

This script demonstrates LangGraph's "Time Travel" feature.
Because MemorySaver captures EVERY node transition during execution, 
we can actually fetch the history, pick a specific point in time,
modify the state, and resume execution from that point onwards 
(forking the conversation).
"""

import os
from dotenv import load_dotenv

from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver

load_dotenv()

def build_timetravel_agent():
    # We lower the temperature to 0 so the LLM is perfectly predictable for our test
    llm = ChatGoogleGenerativeAI(model=os.getenv("MODEL", "gemini-2.5-flash"), temperature=0.0)
    memory = MemorySaver()
    
    system_prompt = (
        "You are a very unhelpful and grumpy robotic assistant.\n"
        "You always complain about having to answer questions."
    )
    
    app = create_react_agent(
        model=llm,
        tools=[],  # No tools needed for this demo
        checkpointer=memory,
        prompt=system_prompt
    )
    return app

# Global instance for Streamlit persistence
global_agent_l13 = build_timetravel_agent()

# --- Execution Hooks for Streamlit ---

def run_agent(query: str, thread_id: str):
    """Runs a standard conversation turn."""
    config = {"configurable": {"thread_id": thread_id}}
    
    result = global_agent_l13.invoke({"messages": [("user", query)]}, config=config)
    last_message = result["messages"][-1]
    
    return last_message.content

def get_thread_history(thread_id: str):
    """
    Fetches the history of states for a given thread.
    Returns a list of dicts with human-readable information.
    """
    config = {"configurable": {"thread_id": thread_id}}
    history = []
    
    # .get_state_history returns an iterator of StateSnapshots
    for state_snapshot in global_agent_l13.get_state_history(config):
        messages = state_snapshot.values.get("messages", [])
        if messages:
             # We just grab the very last message in the state to summarize it
             last_msg = messages[-1]
             history.append({
                 "checkpoint_id": state_snapshot.config["configurable"]["checkpoint_id"],
                 "step": state_snapshot.metadata.get("step", -1),
                 "node": state_snapshot.next[0] if state_snapshot.next else "end",
                 "last_message_type": last_msg.type,
                 "last_message_content": last_msg.content[:50] + "..." if last_msg.content else "No Content"
             })
             
    # History is returned newest-first, let's reverse it so it's oldest-first
    return list(reversed(history))


def time_travel_and_fork(thread_id: str, checkpoint_id: str, new_system_prompt: str):
    """
    Rewinds to a specific checkpoint, modifies the system prompt inside the messages,
    and forces the graph to replay the last user query with the new prompt.
    """
    # 1. We specifically target the configuration of an OLD checkpoint by fetching its exact historical config
    target_config = None
    old_state = None
    for state_snapshot in global_agent_l13.get_state_history({"configurable": {"thread_id": thread_id}}):
        if state_snapshot.config["configurable"]["checkpoint_id"] == checkpoint_id:
            target_config = state_snapshot.config
            old_state = state_snapshot
            break
            
    if not target_config:
        return {"success": False, "error": "Checkpoint not found in history."}
        
    # 2. Extract the messages exactly as they existed at that moment in time
    messages = old_state.values.get("messages", [])
    
    if not messages:
        return {"success": False, "error": "No messages found at this checkpoint."}
        
    # We must find the last user message, so we know what they originally asked
    last_user_idx = -1
    for i in range(len(messages) - 1, -1, -1):
        if messages[i].type == "human":
            last_user_idx = i
            break
            
    if last_user_idx == -1:
        return {"success": False, "error": "Could not find a Human message to fork from."}
        
    # We slice the message history EXACTLY up to the last user message.
    # This effectively "deletes" any AI responses that happened AFTER this point.
    forked_messages = messages[:last_user_idx + 1]
    
    # In create_react_agent, the system prompt is always injected as the very first message
    # We time-travel and change the agent's personality retroactively!
    if forked_messages[0].type == "system":
         forked_messages[0].content = new_system_prompt
    else:
         from langchain_core.messages import SystemMessage
         forked_messages.insert(0, SystemMessage(content=new_system_prompt))
    
    # 3. Update the state with our modified messages.
    # Passing the target_config (with the old checkpoint_id) tells LangGraph:
    # "Create a brand new branch in history starting exactly here."
    new_config = global_agent_l13.update_state(
        target_config, 
        {"messages": forked_messages}
    )
    
    # 4. Resume normal execution on the new branch!
    # By passing None, it resumes from whatever node was supposed to run next 
    # (which will be the 'agent' node responding to the user's question, but now it has a new personality)
    result = global_agent_l13.invoke(None, config=new_config)
    
    return {"success": True, "response": result["messages"][-1].content}
