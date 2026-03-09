import streamlit as st
import asyncio

# --- IMPORT BASE AGENT WITHOUT CHANGING IT ---
from adk_labs.adk_level7_workflows.agent import root_agent
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from google.genai import types

if "adk_basic_service_7" not in st.session_state:
    st.session_state.adk_basic_service_7 = InMemorySessionService()

def render():
    st.header("Level 7: Sequential Workflows (ADK Native)")
    st.info("Concept: ADK utilizes the `SequentialAgent` class to strictly pass the output of Agent A into Agent B as an enforced chronological pipeline.")
    
    topic = st.text_input("Enter a topic for the 3-step pipeline (Extract -> Summarize -> Format):", value="Parse this bio: John Doe is a 45 year old engineer who loves python.")
    
    if st.button("Run Level 7 Workflow"):
        with st.spinner("Executing SequentialAgent Pipeline..."):
            try:
                import uuid
                session_id = str(uuid.uuid4())
                runner = Runner(agent=root_agent, app_name="app", session_service=st.session_state.adk_basic_service_7)
                user_msg = types.Content(role="user", parts=[types.Part(text=topic)])
                
                async def run_runner():
                    await st.session_state.adk_basic_service_7.get_session(app_name="app", user_id="user", session_id=session_id) or \
                    await st.session_state.adk_basic_service_7.create_session(app_name="app", user_id="user", session_id=session_id)
                    
                    final_text = ""
                    history_ui = []
                    async for event in runner.run_async(user_id="user", session_id=session_id, new_message=user_msg):
                        if event.is_final_response() and event.content and event.content.parts:
                            final_text = "".join(p.text for p in event.content.parts if hasattr(p, "text"))
                            
                    session = await st.session_state.adk_basic_service_7.get_session(app_name="app", user_id="user", session_id=session_id)
                    if hasattr(session, 'events'):
                        for ev in session.events:
                            if ev.content and ev.content.parts:
                                parts_list = []
                                for p in ev.content.parts:
                                    if hasattr(p, "text") and p.text:
                                        parts_list.append({"text": p.text})
                                if parts_list:
                                    history_ui.append({"author": ev.author, "parts": parts_list})
                                    
                    return final_text, history_ui

                try:
                    loop = asyncio.get_running_loop()
                except RuntimeError:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)

                response_text, history = loop.run_until_complete(run_runner())
                
                st.success("✅ Sequence Complete!")
                
                st.markdown("### 🕸️ Call History Trace:")
                for step in history:
                    author = step.get("author", "unknown").replace("_", " ").title()
                    parts = step.get('parts', [])
                    for part in parts:
                        if "text" in part:
                            if step.get("author") == "user":
                                st.markdown(f"**🗣️ User:** {part['text']}")
                            else:
                                st.info(f"**🤖 {author}:** {part['text']}")
                
                st.markdown("### 🕸️ Final Pipeline Output:")
                
                # The final response is the output of the final agent in the sequence
                st.write(response_text)
                
            except Exception as e:
                st.error(f"Error: {e}")
