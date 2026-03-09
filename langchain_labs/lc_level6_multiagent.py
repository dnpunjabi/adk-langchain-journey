"""
LangChain Level 6: Multi-Agent Transfer

ADK Equivalent: `Agent(sub_agents=[sales_agent, hr_agent])`
LangChain Concept: `LangGraph` Supervisor Pattern

EXPLANATION:
In ADK, passing `sub_agents` automatically tells the LLM to route questions to them.
In the LangChain ecosystem, we orchestrate multiple agents using LangGraph.

LangGraph represents your system as a State-Machine (a directed graph):
1. State: The memory passed between agents (usually a list of messages).
2. Nodes: Python functions that do work (like an LLM calling an agent).
3. Edges: Conditional logic that decides which node runs next.

In this script, we recreate the ADK "Company Hub". 
We create a 'supervisor' node that reads the user's question and decides to route it
to the 'sales_agent' node, the 'hr_agent' node, or 'FINISH'.
"""

import os
from typing import Literal
from dotenv import load_dotenv

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import StateGraph, START, END, MessagesState

# Pydantic is used to force the LLM to output a structured destination
from pydantic import BaseModel

load_dotenv()

# --- 1. Define the LLM ---
MODEL = os.getenv("MODEL", "gemini-2.5-flash")
llm = ChatGoogleGenerativeAI(model=MODEL, temperature=0.1)

# --- 2. Define the Routing Schema for the Supervisor ---
class RouteConfig(BaseModel):
    """The supervisor's decision on who should answer next."""
    next_node: Literal["sales_agent", "hr_agent", "FINISH"]

# --- 3. Define the Nodes (The Agents) ---

def supervisor_node(state: MessagesState) -> dict:
    """Decides who should handle the user's request."""
    # We use structured output to guarantee the LLM returns exactly one of our choices
    router_llm = llm.with_structured_output(RouteConfig)
    
    system_prompt = (
        "You are the company receptionist. Read the user's message and route them:\n"
        "- If it's about buying products or prices -> sales_agent\n"
        "- If it's about leave policies or hiring -> hr_agent\n"
        "- Otherwise -> FINISH"
    )
    
    messages = [SystemMessage(content=system_prompt)] + state["messages"]
    
    # Force the LLM to pick a route
    decision: RouteConfig = router_llm.invoke(messages)
    
    # Tell LangGraph where to go next by storing it in a custom state key,
    # or we can just return a marker message. Here we append an AI message with the routing intent.
    # Actually, the purest way is to just let a conditional edge read the decision.
    # But for simplicity, we will just return a message that the conditional edge can read.
    return {"messages": [SystemMessage(content=f"ROUTING_DECISION: {decision.next_node}")]}

def sales_agent_node(state: MessagesState) -> dict:
    system_prompt = "You are the Sales Agent. Answer questions enthusiastically about Acme Corp's products (₹999/mo)."
    messages = [SystemMessage(content=system_prompt)] + state["messages"]
    response = llm.invoke(messages)
    return {"messages": [response]}

def hr_agent_node(state: MessagesState) -> dict:
    system_prompt = "You are the HR Agent. Answer questions professionally about Acme Corp's 20-day leave policy."
    messages = [SystemMessage(content=system_prompt)] + state["messages"]
    response = llm.invoke(messages)
    return {"messages": [response]}

# --- 4. Define the Edge Logic ---
def route_from_supervisor(state: MessagesState) -> str:
    """Reads the supervisor's routing decision from the last message."""
    last_message = state["messages"][-1].content
    if "ROUTING_DECISION: sales_agent" in last_message:
        return "sales_agent"
    elif "ROUTING_DECISION: hr_agent" in last_message:
        return "hr_agent"
    else:
        return END

# --- 5. Build the Graph ---
def build_graph():
    # We use MessagesState, a built-in LangGraph state that just tracks a list of messages
    builder = StateGraph(MessagesState)

    # Add the nodes (the distinct agents)
    builder.add_node("supervisor", supervisor_node)
    builder.add_node("sales_agent", sales_agent_node)
    builder.add_node("hr_agent", hr_agent_node)

    # Define the flow
    builder.add_edge(START, "supervisor")
    
    # Conditional edge: after supervisor runs, call `route_from_supervisor` to decide where to go
    builder.add_conditional_edges(
        "supervisor", 
        route_from_supervisor,
        {"sales_agent": "sales_agent", "hr_agent": "hr_agent", END: END}
    )
    
    # Once a specialist finishes, the conversation ends for this turn
    builder.add_edge("sales_agent", END)
    builder.add_edge("hr_agent", END)

    # Compile into a runnable application
    return builder.compile()

# --- Streamlit Execution Hook ---
def run_level(query: str):
    """Executes Level 6 logic and returns the graph execution trace."""
    app = build_graph()
    
    # Execute the graph
    steps = []
    
    # stream() yields the output of each node as it runs
    for output in app.stream({"messages": [HumanMessage(content=query)]}):
        # output is a dict like {"node_name": {"messages": [...]}}
        for node_name, state_update in output.items():
            last_msg = state_update["messages"][-1].content
            steps.append({
                "node": node_name,
                "content": last_msg
            })
            
    return steps

if __name__ == "__main__":
    print("\nTest 1: Sales Routing")
    for step in run_level("I want to buy the premium cloud suite."):
         print(f"[{step['node']}] {step['content'][:60]}...")
         
    print("\nTest 2: HR Routing")
    for step in run_level("How many sick days do I get?"):
         print(f"[{step['node']}] {step['content'][:60]}...")
