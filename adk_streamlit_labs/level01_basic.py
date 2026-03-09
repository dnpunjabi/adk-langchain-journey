import streamlit as st
import asyncio

# --- IMPORT BASE AGENT WITHOUT CHANGING IT ---
from adk_labs.adk_level1_basic.agent import root_agent
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from google.genai import types

if "adk_basic_service" not in st.session_state:
    st.session_state.adk_basic_service = InMemorySessionService()

def render():
    st.header("Level 1: Single Agent Basics")
    st.info("Concept: Connecting to Gemini using ADK `Agent` and a Session runner.")
    
    prompt = st.text_input("Enter a prompt:", value="Explain quantum computing in one simple sentence.")
    if st.button("Run Level 1 Agent"):
        with st.spinner("Invoking ADK LLM..."):
            try:
                # 1. Create a Runner
                runner = Runner(agent=root_agent, app_name="app", session_service=st.session_state.adk_basic_service)
                
                # 2. Build the User Content object
                user_msg = types.Content(role="user", parts=[types.Part(text=prompt)])
                
                # 3. Stream the events natively using runner.run() block
                async def run_runner():
                    # Get session first
                    await st.session_state.adk_basic_service.get_session(app_name="app", user_id="user", session_id="level1_thread") or \
                    await st.session_state.adk_basic_service.create_session(app_name="app", user_id="user", session_id="level1_thread")
                    
                    final_text = ""
                    async for event in runner.run_async(user_id="user", session_id="level1_thread", new_message=user_msg):
                        if event.is_final_response() and event.content and event.content.parts:
                            final_text = "".join(p.text for p in event.content.parts if hasattr(p, "text"))
                    return final_text

                try:
                    loop = asyncio.get_running_loop()
                except RuntimeError:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)

                response_text = loop.run_until_complete(run_runner())
                
                st.success("Success!")
                st.markdown("### Response:")
                st.write(response_text)
            except Exception as e:
                st.error(f"Error: {e}")
