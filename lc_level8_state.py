"""
LangChain Level 8: State & Memory

ADK Equivalent: `SessionHistory` (built-in automatic memory)
LangChain Concept: LangGraph `MemorySaver` (Checkpointers)

EXPLANATION:
In ADK, when you chat with an agent, it automatically remembers your previous messages
in that session. 

In pure LangChain, LLMs are stateless. If you want them to remember, you must:
1. Define a State that holds all messages (e.g. `MessagesState`).
2. Attach a Checkpointer (like `MemorySaver`) when compiling the graph.
3. Pass a `thread_id` in the config when invoking the graph.

The graph will automatically save the state after every node executes, 
and reload it when the same `thread_id` connects again!
"""

import os
from dotenv import load_dotenv

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import StateGraph, START, END, MessagesState

# This is the magic checkpointer that saves state to memory (RAM)
from langgraph.checkpoint.memory import MemorySaver

load_dotenv()

# --- 1. Define the LLM ---
MODEL = os.getenv("MODEL", "gemini-2.5-flash")
llm = ChatGoogleGenerativeAI(model=MODEL, temperature=0.7)

# --- 2. Define the Node ---
def chat_node(state: MessagesState) -> dict:
    """A simple chat node that responds to the user's messages."""
    
    # We want to prepend a system prompt, but we shouldn't save it to the state permanently.
    # So we just construct a temporary list of messages for the LLM invocation.
    system_prompt = SystemMessage(content="You are a helpful assistant with a great memory. Keep answers brief.")
    
    messages_to_send = [system_prompt] + state["messages"]
    
    # Generate the response
    response = llm.invoke(messages_to_send)
    
    # LangGraph will automatically APPEND this new message to the existing MessagesState
    return {"messages": [response]}

# --- 3. Build & Compile with Memory ---
def build_graph():
    # 1. Create the graph
    builder = StateGraph(MessagesState)
    builder.add_node("assistant", chat_node)
    builder.add_edge(START, "assistant")
    builder.add_edge("assistant", END)

    # 2. Create the memory saver
    memory = MemorySaver()

    # 3. CRITICAL: Compile the graph and attach the memory
    # Without checkpointer=memory, the graph forgets everything instantly.
    app = builder.compile(checkpointer=memory)
    return app

# --- Streamlit / CLI Execution Hook ---
# We keep the app instance ALIVE globally so the MemorySaver persists in RAM
_global_app = build_graph()

def run_level(query: str, thread_id: str = "thread_1"):
    """
    Executes Level 8 logic. 
    Notice we pass a `thread_id` so the Checkpointer knows which memory to load!
    """
    config = {"configurable": {"thread_id": thread_id}}
    
    # Stream the execution to get the final message
    response_content = ""
    
    # We pass the HumanMessage wrapped in a list, as expected by MessagesState reducer
    for step_output in _global_app.stream({"messages": [HumanMessage(content=query)]}, config=config):
        for node_name, state_update in step_output.items():
            if "messages" in state_update:
                response_content = state_update["messages"][-1].content
                
    return response_content

if __name__ == "__main__":
    print("🤖 LangGraph Memory Tester (Level 8)\n")
    
    # Turn 1
    print("User: Hi, my name is Dheer and my favorite color is Blue.")
    res1 = run_level("Hi, my name is Dheer and my favorite color is Blue.", thread_id="test_session")
    print(f"AI:   {res1}\n")
    
    # Turn 2 - Testing Memory
    print("User: What is my name and favorite color?")
    res2 = run_level("What is my name and favorite color?", thread_id="test_session")
    print(f"AI:   {res2}\n")
    
    # Turn 3 - Testing a DIFFERENT thread
    print("User (New Thread): What is my name?")
    res3 = run_level("What is my name?", thread_id="different_session")
    print(f"AI:   {res3}\n")
