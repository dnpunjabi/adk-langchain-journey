import streamlit as st
import asyncio

# --- IMPORT BASE AGENT WITHOUT CHANGING IT ---
from adk_labs.adk_level3_tools.agent import root_agent
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from google.genai import types

if "adk_basic_service_3" not in st.session_state:
    st.session_state.adk_basic_service_3 = InMemorySessionService()

def render():
    st.header("Level 3: Custom Tools")
    st.info("Concept: Providing Python functions to the `tools` array. ADK automatically executes them in a native loop!")
    
    prompt = st.text_input("Ask a question requiring a tool (weather or math):", 
                          value="What is the weather in Mumbai? Also, what is 15 * 12?")
    
    if st.button("Run Level 3 Agent with Tools"):
        with st.spinner("Invoking ADK Agent (Auto-Looping)..."):
            try:
                import uuid
                session_id = str(uuid.uuid4())
                runner = Runner(agent=root_agent, app_name="app", session_service=st.session_state.adk_basic_service_3)
                user_msg = types.Content(role="user", parts=[types.Part(text=prompt)])

                async def run_runner():
                    session = await st.session_state.adk_basic_service_3.get_session(app_name="app", user_id="user", session_id=session_id) or \
                              await st.session_state.adk_basic_service_3.create_session(app_name="app", user_id="user", session_id=session_id)
                    
                    async for event in runner.run_async(user_id="user", session_id=session_id, new_message=user_msg):
                        pass
                    
                    # fetch updated history from session
                    session = await st.session_state.adk_basic_service_3.get_session(app_name="app", user_id="user", session_id=session_id)
                    history_ui = []
                    if hasattr(session, 'events'):
                        for ev in session.events:
                            if ev.content and ev.content.parts:
                                parts_list = []
                                for p in ev.content.parts:
                                    if hasattr(p, "text") and p.text:
                                        parts_list.append({"text": p.text})
                                    elif hasattr(p, "function_call") and p.function_call:
                                        parts_list.append({"functionCall": {"name": p.function_call.name, "args": getattr(p.function_call, "args", {})}})
                                    elif hasattr(p, "function_response") and p.function_response:
                                        parts_list.append({"functionResponse": {"response": getattr(p.function_response, "response", {})}})
                                if parts_list:
                                    history_ui.append({"author": ev.author, "parts": parts_list})
                    return history_ui

                try:
                    loop = asyncio.get_running_loop()
                except RuntimeError:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)

                history = loop.run_until_complete(run_runner())
                
                # ADK abstracts the loop, but we can access history!
                st.success("ADK Execution Complete!")
                
                st.markdown("### 🕸️ ADK History Trace:")
                for step in history:
                    author = step.get("author", "unknown").replace("_", " ").title()
                    parts = step.get('parts', [])
                    for part in parts:
                        if "text" in part:
                            if step.get("author") == "user":
                                st.markdown(f"**🗣️ User:** {part['text']}")
                            else:
                                st.success(f"**🤖 {author}:** {part['text']}")
                        elif "functionCall" in part:
                            fc = part["functionCall"]
                            st.warning(f"**🔧 LLM Requested Tool:** `{fc.get('name', 'unknown')}` with args `{fc.get('args', {})}`")
                        elif "functionResponse" in part:
                            fr = part["functionResponse"]
                            result = fr.get('response', {}).get('result', str(fr))
                            st.info(f"**✅ Auto-Executed Tool:** Returned `{result}`")
                            
            except Exception as e:
                st.error(f"Error: {e}")
