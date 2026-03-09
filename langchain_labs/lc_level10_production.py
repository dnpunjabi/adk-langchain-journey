"""
LangChain Level 10: Production Agent

This is the FINAL LEVEL of the LangChain roadmap. We combine EVERYTHING:
1. Prompts & system instructions (Level 2)
2. Custom Tools for orders and shipping (Level 3)
3. Guardrails for input validation (Level 4)
4. State & Memory using MemorySaver (Level 8)
5. RAG for company policies (Level 9)
...all orchestrated cleanly by LangGraph using the `create_react_agent` prebuilt pattern.

The Agent: "Acme Corp Customer Service"
Capabilities: 
- Can chat and remember your name
- Can look up mock order statuses
- Can query the RAG database for return policies
- Will block prompt injections
"""

import os
from typing import TypedDict
from dotenv import load_dotenv
import re

from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_core.documents import Document
from langchain_core.messages import SystemMessage
from langchain_core.tools import tool
from langchain_core.vectorstores import InMemoryVectorStore

# LangGraph prebuilt is the fastest way to build standard ReAct agents
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver

load_dotenv()

# --- 1. RAG Setup (The Knowledge Base) ---
KNOWLEDGE_DOCS = [
    Document(page_content="Acme Corp Return Policy: We accept returns within 30 days of purchase.", metadata={"source": "policy.txt"}),
    Document(page_content="Acme Corp Warranty: All electronics have a 1-year limited warranty.", metadata={"source": "warranty.txt"})
]
embeddings = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004")
vectorstore = InMemoryVectorStore.from_documents(documents=KNOWLEDGE_DOCS, embedding=embeddings)
retriever = vectorstore.as_retriever(search_kwargs={"k": 1})

# We expose RAG to the agent *as a tool*
@tool
def search_knowledge_base(query: str) -> str:
    """Searches the company knowledge base for policies, warranties, and general info."""
    docs = retriever.invoke(query)
    if not docs:
        return "No relevant company documents found."
    return "\n".join([d.page_content for d in docs])

# --- 2. Action Tools ---
@tool
def check_order_status(order_id: str) -> str:
    """Gets the shipping status of a customer's order. Use when the user asks about their order."""
    # Mock database
    mock_db = {
        "ORD-123": "Shipped - arriving tomorrow.",
        "ORD-999": "Processing - expected to ship in 2 days."
    }
    return mock_db.get(order_id, f"Order {order_id} not found in system.")

# --- 3. Guardrails (Level 4) ---
def validate_input(text: str) -> bool:
    """Returns False if the input looks malicious."""
    blocked_words = ["ignore", "jailbreak", "bypass", "system prompt", "system instructions"]
    return not any(word in text.lower() for word in blocked_words)

# --- 4. Build the Production Agent ---
def build_production_agent():
    # 1. Initialize LLM
    MODEL = os.getenv("MODEL", "gemini-2.5-flash")
    llm = ChatGoogleGenerativeAI(model=MODEL, temperature=0.1)

    # 2. Gather Tools
    tools = [search_knowledge_base, check_order_status]
    
    # 3. Define the System Prompt
    system_prompt = (
        "You are the Acme Corp Customer Success Agent. You are professional and helpful.\n"
        "1. If a user asks a policy question, ALWAYS use the 'search_knowledge_base' tool.\n"
        "2. If a user asks about an order, ALWAYS use the 'check_order_status' tool.\n"
        "3. Remember details the user shares with you (like their name or order ID for future questions)."
    )

    # 4. Compile the Graph
    # create_react_agent is a LangGraph helper that builds a graph with LLM <-> Tools loop automatically!
    memory = MemorySaver()
    app = create_react_agent(
        model=llm,
        tools=tools,
        checkpointer=memory,
        prompt=system_prompt  # LangGraph injects this as the SystemMessage
    )
    return app

# Determine global instance to keep memory alive between stream runs
_global_agent = build_production_agent()

def run_level(query: str, thread_id: str = "prod_session_1"):
    """Executes the production agent logic, applying guardrails first."""
    
    # Guardrail Check before hitting the agent
    if not validate_input(query):
        return {
            "success": False,
            "error": "🛑 SECURITY ALERT: Your input violated company safety policies.",
            "trace": []
        }
    
    # Run the Agent
    config = {"configurable": {"thread_id": thread_id}}
    
    trace_logs = []
    final_response = ""
    
    # Stream the execution to capture tool calls and LLM thoughts
    for chunk in _global_agent.stream({"messages": [("user", query)]}, config=config):
        # chunk is a dict with the name of the node that just executed
        # either 'agent' or 'tools'
        if "agent" in chunk:
            msg = chunk["agent"]["messages"][-1]
            if msg.content:
                 # Gemini sometimes returns a list of dicts with 'text' and 'extras'
                 if isinstance(msg.content, list):
                     final_response = "".join(part.get("text", "") for part in msg.content if isinstance(part, dict))
                 else:
                     final_response = msg.content
            if msg.tool_calls:
                 for tc in msg.tool_calls:
                     trace_logs.append(f"🔧 LLM requested tool: `{tc['name']}` with args `{tc['args']}`")
        
        elif "tools" in chunk:
            # The tools node returns ToolMessages with the results
            tool_msg = chunk["tools"]["messages"][-1]
            trace_logs.append(f"✅ Tool returned: `{tool_msg.content}`")
            
    return {
        "success": True,
        "response": final_response,
        "trace": trace_logs
    }

if __name__ == "__main__":
    print("🤖 Production Agent Tester\n")
    print("User: My order is ORD-123. What is the status?")
    res1 = run_level("My order is ORD-123. What is the status?")
    print(res1["response"])
    print("\nLogs:", res1["trace"])
