import streamlit as st
import asyncio

# --- IMPORT BASE AGENT WITHOUT CHANGING IT ---
from adk_labs.adk_level5_callbacks.agent import root_agent
from adk_labs.adk_level5_callbacks.agent import _stats
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from google.genai import types

if "adk_basic_service_5" not in st.session_state:
    st.session_state.adk_basic_service_5 = InMemorySessionService()

def render():
    st.header("Level 5: Observability & Callbacks")
    st.info("Concept: Attaching native hook functions to `after_model_callback` and others to listen to the execution lifecycle.")
    
    query = st.text_input("Ask a shipping question:", value="What is the weather in Mumbai?")
    
    if st.button("Run Level 5 with Callbacks"):
        with st.spinner("Invoking ADK agent and collecting callback stats..."):
            try:
                runner = Runner(agent=root_agent, app_name="app", session_service=st.session_state.adk_basic_service_5)
                user_msg = types.Content(role="user", parts=[types.Part(text=query)])
                
                async def run_runner():
                    await st.session_state.adk_basic_service_5.get_session(app_name="app", user_id="user", session_id="level5_thread") or \
                    await st.session_state.adk_basic_service_5.create_session(app_name="app", user_id="user", session_id="level5_thread")
                    
                    final_text = ""
                    async for event in runner.run_async(user_id="user", session_id="level5_thread", new_message=user_msg):
                        if event.is_final_response() and event.content and event.content.parts:
                            final_text = "".join(p.text for p in event.content.parts if hasattr(p, "text"))
                    return final_text

                try:
                    loop = asyncio.get_running_loop()
                except RuntimeError:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)

                response_text = loop.run_until_complete(run_runner())
                
                st.success("✅ Execution Complete!")
                
                st.markdown("### 📝 Attached Metadata / Callbacks:")
                st.write("ADK native hooks intercept the ModelResponse object to log usage:")
                
                # We pull the actual _stats dictionary that the native level 5 agent populates!
                st.json(_stats)
                    
                st.markdown("### 🤖 Final Response:")
                st.write(response_text)
                
            except Exception as e:
                st.error(f"Error: {e}")
