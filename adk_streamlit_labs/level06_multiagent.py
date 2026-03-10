import streamlit as st
import asyncio

# --- IMPORT BASE AGENT WITHOUT CHANGING IT ---
from adk_labs.adk_level6_multiagent.agent import root_agent
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from google.genai import types

def render():
    if "adk_basic_service_6" not in st.session_state:
        st.session_state.adk_basic_service_6 = InMemorySessionService()
    st.header("Level 6: Multi-Agent Trees (ADK Native)")
    st.info("Concept: The ADK uses hierarchical routing. A top-level 'Supervisor' agent is given an array of `sub_agents`. It automatically routes user intents to the leaf HR or Sales bots.")
    
    # Provide two buttons to easily test routing
    if "adv_lvl6_query" not in st.session_state:
        st.session_state.adv_lvl6_query = "I want to buy the premium cloud suite."
        
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📝 Use Sales Query"):
            st.session_state.adv_lvl6_query = "I want to buy the premium cloud suite."
    with col2:
        if st.button("👥 Use HR Query"):
            st.session_state.adv_lvl6_query = "How many sick days do I get?"
            
    query = st.text_input("Ask a question for Acme Corp:", key="adv_lvl6_query")

    if st.button("Run Level 6 Multi-Agent Router"):
        with st.spinner("Executing ADK Routing Tree..."):
            try:
                import uuid
                session_id = str(uuid.uuid4())
                runner = Runner(agent=root_agent, app_name="app", session_service=st.session_state.adk_basic_service_6)
                user_msg = types.Content(role="user", parts=[types.Part(text=query)])
                
                async def run_runner():
                    session = await st.session_state.adk_basic_service_6.get_session(app_name="app", user_id="user", session_id=session_id) or \
                              await st.session_state.adk_basic_service_6.create_session(app_name="app", user_id="user", session_id=session_id)
                    
                    final_text = ""
                    async for event in runner.run_async(user_id="user", session_id=session_id, new_message=user_msg):
                        if event.is_final_response() and event.content and event.content.parts:
                            final_text = "".join(p.text for p in event.content.parts if hasattr(p, "text"))
                            
                    history_ui = []
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
                
                st.success("✅ Routing Execution Complete!")
                
                st.markdown("### 🕸️ Call History Trace:")
                # We can inspect the history to see the handoffs
                for step in history:
                    author = step.get("author", "unknown").replace("_", " ").title()
                    parts = step.get('parts', [])
                    for part in parts:
                        if "text" in part:
                            if step.get("author") == "user":
                                st.markdown(f"**🗣️ User:** {part['text']}")
                            else:
                                st.info(f"**🤖 {author}:** {part['text']}")
                
                st.markdown("---")
                st.success(f"**🎯 Final Directed Response:**\n{response_text}")

            except Exception as e:
                st.error(f"Error: {e}")
