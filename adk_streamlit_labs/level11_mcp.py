import streamlit as st
import asyncio
import uuid

# --- IMPORT BASE AGENT WITHOUT CHANGING IT ---
from adk_labs.adk_level11_mcp.agent import root_agent
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from google.genai import types

if "adk_mcp_service" not in st.session_state:
    st.session_state.adk_mcp_service = InMemorySessionService()

def render():
    st.header("Level 11: Model Context Protocol (MCP)")
    st.info("Concept: Using MCP to connect to a standardized tool server. The agent 'discovers' and calls tools from an external process!")
    
    st.markdown("### 🔌 MCP Architecture:")
    st.code("""
    [ADK Agent] <---> [MCP Bridge Tool] <--- Stdio ---> [FastMCP Server (SQLite)]
    """, language="text")

    if "mcp_messages" not in st.session_state:
        st.session_state.mcp_messages = []
    
    # Session ID for history
    if "mcp_session_id" not in st.session_state:
        st.session_state.mcp_session_id = str(uuid.uuid4())

    async def get_history():
        session = await st.session_state.adk_mcp_service.get_session(
            app_name="app", user_id="user", session_id=st.session_state.mcp_session_id
        )
        if session and hasattr(session, 'events'):
            history_ui = []
            for ev in session.events:
                if ev.content and ev.content.parts:
                    parts_list = []
                    for p in ev.content.parts:
                        if hasattr(p, "text") and p.text:
                            parts_list.append({"text": p.text})
                    if parts_list:
                        role = "user" if ev.author == "user" else "model"
                        history_ui.append({"role": role, "parts": parts_list})
            return history_ui
        return []

    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    history = loop.run_until_complete(get_history())
    
    for msg in history:
        with st.chat_message("user" if msg["role"] == "user" else "assistant"):
            for part in msg["parts"]:
                st.markdown(part["text"])

    if user_prompt := st.chat_input("Ask about products (e.g., 'What laptops do you have?')"):
        with st.chat_message("user"):
            st.markdown(user_prompt)
        
        with st.chat_message("assistant"):
            with st.spinner("Connecting to MCP Server..."):
                try:
                    runner = Runner(agent=root_agent, app_name="app", session_service=st.session_state.adk_mcp_service)
                    user_msg = types.Content(role="user", parts=[types.Part(text=user_prompt)])
                    
                    async def run_runner():
                        await st.session_state.adk_mcp_service.get_session(
                            app_name="app", user_id="user", session_id=st.session_state.mcp_session_id
                        ) or \
                        await st.session_state.adk_mcp_service.create_session(
                            app_name="app", user_id="user", session_id=st.session_state.mcp_session_id
                        )
                        
                        final_text = ""
                        async for event in runner.run_async(
                            user_id="user", 
                            session_id=st.session_state.mcp_session_id, 
                            new_message=user_msg
                        ):
                            if event.is_final_response() and event.content and event.content.parts:
                                final_text = "".join(p.text for p in event.content.parts if hasattr(p, "text"))
                        return final_text

                    response = loop.run_until_complete(run_runner())
                    st.markdown(response)
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")

    if st.button("Clear History"):
        st.session_state.adk_mcp_service = InMemorySessionService()
        st.session_state.mcp_session_id = str(uuid.uuid4())
        st.rerun()
