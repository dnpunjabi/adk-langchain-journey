"""
LangChain Level 7: Workflows

ADK Equivalent: `SequentialAgent`, `ParallelAgent`
LangChain Concept: LangGraph Deterministic Edges (Sequential & Parallel)

EXPLANATION:
In ADK, you explicitly define `SequentialAgent` (runs steps one after another)
and `ParallelAgent` (runs sub-agents at the same time and combines results).

In LangGraph, EVERYTHING is a graph. 
- Sequential workflow: `node A` -> `node B` -> `node C`
- Parallel workflow: `node A` maps out to `node B` AND `node C`, 
                     then both map to `node D` (fan-out / fan-in).

In this script, we rebuild the "Content Pipeline" from ADK Level 7.
We use a custom TypedDict State to pass data cleanly between the nodes instead of just a list of messages.

The Pipeline:
[START] -> Researcher -> (Parallel: Formal Writer, Casual Writer) -> Editor -> [END]
"""

import os
from typing import TypedDict, Annotated
from dotenv import load_dotenv

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import StateGraph, START, END

load_dotenv()

# --- 1. Define the Custom State ---
# This dictionary represents the "memory" that moves through the graph.
class PipelineState(TypedDict):
    topic: str
    research_notes: str
    formal_draft: str
    casual_draft: str
    final_output: str

# --- 2. Initialize the LLM ---
MODEL = os.getenv("MODEL", "gemini-2.5-flash")
llm = ChatGoogleGenerativeAI(model=MODEL, temperature=0.3)

# --- 3. Define the Nodes ---

def researcher_node(state: PipelineState) -> dict:
    """Gets the topic and outputs research notes."""
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a researcher. Provide 3 bullet points of facts about the topic. Keep it brief."),
        ("human", "{topic}")
    ])
    chain = prompt | llm
    response = chain.invoke({"topic": state["topic"]})
    return {"research_notes": response.content}

def formal_writer_node(state: PipelineState) -> dict:
    """Takes research notes and writes a formal paragraph."""
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a formal writer. Write a strictly professional 2-sentence summary based on these notes: {notes}"),
        ("human", "Topic: {topic}")
    ])
    chain = prompt | llm
    response = chain.invoke({"topic": state["topic"], "notes": state["research_notes"]})
    return {"formal_draft": response.content}

def casual_writer_node(state: PipelineState) -> dict:
    """Takes research notes and writes a casual paragraph."""
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a casual social media writer. Write an enthusiastic 2-sentence tweet based on these notes: {notes}"),
        ("human", "Topic: {topic}")
    ])
    chain = prompt | llm
    response = chain.invoke({"topic": state["topic"], "notes": state["research_notes"]})
    return {"casual_draft": response.content}

def editor_node(state: PipelineState) -> dict:
    """Takes both drafts and combines them."""
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are the Editor. The user will provide a formal draft and a casual draft. "
                   "Combine them into one cohesive, friendly paragraph."),
        ("human", "Formal Draft: {formal_draft}\n\nCasual Draft: {casual_draft}")
    ])
    chain = prompt | llm
    response = chain.invoke({
        "formal_draft": state["formal_draft"], 
        "casual_draft": state["casual_draft"]
    })
    return {"final_output": response.content}

# --- 4. Build the Graph ---
def build_graph():
    builder = StateGraph(PipelineState)

    # Add all nodes
    builder.add_node("researcher", researcher_node)
    builder.add_node("formal_writer", formal_writer_node)
    builder.add_node("casual_writer", casual_writer_node)
    builder.add_node("editor", editor_node)

    # Diagramming the Flow

    # 1. SEQUENTIAL: Start -> Researcher
    builder.add_edge(START, "researcher")

    # 2. PARALLEL FAN-OUT: Researcher -> Formal Writer AND Casual Writer
    builder.add_edge("researcher", "formal_writer")
    builder.add_edge("researcher", "casual_writer")

    # 3. PARALLEL FAN-IN: Formal Writer AND Casual Writer -> Editor
    # LangGraph automatically waits for all incoming edges to a node to complete
    # before executing it. So the editor waits for BOTH writers!
    builder.add_edge("formal_writer", "editor")
    builder.add_edge("casual_writer", "editor")

    # 4. SEQUENTIAL: Editor -> End
    builder.add_edge("editor", END)

    return builder.compile()

# --- Streamlit Execution Hook ---
def run_level(topic: str):
    """Executes Level 7 logic and returns the graph execution trace."""
    app = build_graph()
    
    # Initialize the state with the user's topic
    initial_state = {"topic": topic}
    
    steps = []
    
    # Stream the execution to capture the updates at each node
    for step_output in app.stream(initial_state):
        # step_output looks like {"researcher": {"research_notes": "..."}}
        for node_name, state_update in step_output.items():
            
            # Extract whatever that specific node added to the state
            content = ""
            if "research_notes" in state_update:
                content = state_update["research_notes"]
            elif "formal_draft" in state_update:
                content = state_update["formal_draft"]
            elif "casual_draft" in state_update:
                content = state_update["casual_draft"]
            elif "final_output" in state_update:
                content = state_update["final_output"]
                
            steps.append({
                "node": node_name,
                "content": content
            })
            
    return steps

if __name__ == "__main__":
    print("\nStarting Content Pipeline Workflow...")
    for step in run_level("The history of AI."):
         print(f"\n[{step['node'].upper()}]\n{step['content']}")
