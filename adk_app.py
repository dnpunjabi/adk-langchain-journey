import streamlit as st
import os
from dotenv import load_dotenv

# Import modular UI wrappers
from adk_streamlit_labs import level01_basic
from adk_streamlit_labs import level02_prompts
from adk_streamlit_labs import level03_tools
from adk_streamlit_labs import level04_guardrails
from adk_streamlit_labs import level05_callbacks
from adk_streamlit_labs import level06_multiagent
from adk_streamlit_labs import level07_workflows
from adk_streamlit_labs import level08_state
from adk_streamlit_labs import level09_rag
from adk_streamlit_labs import level10_production
from adk_streamlit_labs import level12_hitl

load_dotenv()

st.set_page_config(page_title="Google ADK Learning Lab", layout="wide", page_icon="🤖")

st.title("🤖 Google ADK Ecosystem Lab")
st.markdown("Test each level of the native Google Agent Development Kit roadmap directly in the UI!")

# Sidebar navigation
st.sidebar.title("Navigation")
level = st.sidebar.radio(
    "Select a Level to Test:",
    [
        "Level 1: Single Agent Basics",
        "Level 2: Prompt Engineering",
        "Level 3: Custom Tools",
        "Level 4: Guardrails",
        "Level 5: Observability & Callbacks",
        "Level 6: Multi-Agent Trees",
        "Level 7: Sequential Workflows",
        "Level 8: State & Memory",
        "Level 9: Retrieval Augmented Generation (RAG)",
        "Level 10: Full Production Agent",
        "Level 12: Advanced Streaming & Interrupts"
    ]
)

st.sidebar.markdown("---")
st.sidebar.markdown("**Current Model:** " + os.getenv("MODEL", "gemini-2.5-flash"))

# --- Routing ---
if level == "Level 1: Single Agent Basics":
    level01_basic.render()
elif level == "Level 2: Prompt Engineering":
    level02_prompts.render()
elif level == "Level 3: Custom Tools":
    level03_tools.render()
elif level == "Level 4: Guardrails":
    level04_guardrails.render()
elif level == "Level 5: Observability & Callbacks":
    level05_callbacks.render()
elif level == "Level 6: Multi-Agent Trees":
    level06_multiagent.render()
elif level == "Level 7: Sequential Workflows":
    level07_workflows.render()
elif level == "Level 8: State & Memory":
    level08_state.render()
elif level == "Level 9: Retrieval Augmented Generation (RAG)":
    level09_rag.render()
elif level == "Level 10: Full Production Agent":
    level10_production.render()
elif level == "Level 12: Advanced Streaming & Interrupts":
    level12_hitl.render()
else:
    st.warning("This level is not yet implemented.")
