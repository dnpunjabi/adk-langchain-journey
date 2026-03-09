import streamlit as st
import asyncio

# --- IMPORT BASE AGENT WITHOUT CHANGING IT ---
from adk_labs.adk_level2_prompts.agent import root_agent
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from google.genai import types

if "adk_basic_service_2" not in st.session_state:
    st.session_state.adk_basic_service_2 = InMemorySessionService()

def render():
    st.header("Level 2: Prompt Engineering")
    st.info("Concept: Setting the `instruction` property on an ADK Agent as a Developer/System prompt.")
    
    st.markdown("**Agent Instructions (System Prompt):**")
    st.code(root_agent.instruction, language="text")
    
    prompt = st.text_input("Talk to the agent:", value="How many vacation days do I get in my first year?")
    if st.button("Run Level 2 Agent"):
        with st.spinner("Invoking ADK LLM..."):
            try:
                runner = Runner(agent=root_agent, app_name="app", session_service=st.session_state.adk_basic_service_2)
                user_msg = types.Content(role="user", parts=[types.Part(text=prompt)])
                
                async def run_runner():
                    await st.session_state.adk_basic_service_2.get_session(app_name="app", user_id="user", session_id="level2_thread") or \
                    await st.session_state.adk_basic_service_2.create_session(app_name="app", user_id="user", session_id="level2_thread")
                    
                    final_text = ""
                    async for event in runner.run_async(user_id="user", session_id="level2_thread", new_message=user_msg):
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
