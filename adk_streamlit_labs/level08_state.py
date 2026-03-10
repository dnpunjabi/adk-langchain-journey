import streamlit as st
import asyncio

# --- IMPORT BASE AGENT WITHOUT CHANGING IT ---
from adk_labs.adk_level8_state.agent import root_agent
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from google.genai import types

# Initialize the ADK Session Service in Streamlit's global state so memory persists across reruns
def render():
    if "adk_session_service" not in st.session_state:
        st.session_state.adk_session_service = InMemorySessionService()
    st.header("Level 8: State & Memory (ADK Native)")
    st.info("Concept: ADK uses an `InMemorySessionService` to attach history and a state dictionary to a specific session ID, allowing data to persist across turns.")
    
    # Session management
    thread_id = st.text_input("Active Session (Thread ID):", value="adk_state_session_1")
    
    st.markdown("---")
    
    # We must fetch the session asynchronously to get history
    async def get_session_history():
        session = await st.session_state.adk_session_service.get_session(
            app_name="app", user_id="user", session_id=thread_id
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

    # Streamlit requires a sync context, so we run the async fetcher
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
    history = loop.run_until_complete(get_session_history())
    
    # Render chat history natively from ADK
    for step in history:
        role = step.get('role', 'unknown')
        if role == 'user':
            parts = step.get('parts', [])
            for part in parts:
                if 'text' in part:
                    with st.chat_message("user"):
                        st.markdown(part['text'])
        elif role == 'model':
            parts = step.get('parts', [])
            for part in parts:
                if 'text' in part:
                    with st.chat_message("assistant"):
                        st.markdown(part['text'])

    # Chat Input
    if user_prompt := st.chat_input("Say 'My name is Bob', then later ask 'What is my name?'"):
        with st.chat_message("user"):
            st.markdown(user_prompt)
            
        with st.chat_message("assistant"):
            with st.spinner("Agent is thinking..."):
                try:
                    # We create or load the session wrapping the agent
                    runner = Runner(agent=root_agent, app_name="app", session_service=st.session_state.adk_session_service)
                    user_msg = types.Content(role="user", parts=[types.Part(text=user_prompt)])
                    
                    async def run_runner():
                        await st.session_state.adk_session_service.get_session(app_name="app", user_id="user", session_id=thread_id) or \
                        await st.session_state.adk_session_service.create_session(app_name="app", user_id="user", session_id=thread_id)
                        
                        final_text = ""
                        async for event in runner.run_async(user_id="user", session_id=thread_id, new_message=user_msg):
                            if event.is_final_response() and event.content and event.content.parts:
                                final_text = "".join(p.text for p in event.content.parts if hasattr(p, "text"))
                        return final_text

                    response_text = loop.run_until_complete(run_runner())
                    st.markdown(response_text)
                    
                    # Force rerun to update history UI
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")

    st.markdown("---")
    if st.button("Clear History"):
        # Just create a new random session ID or clear the cache
        st.session_state.adk_session_service = InMemorySessionService()
        st.rerun()
