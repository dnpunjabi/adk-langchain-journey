import streamlit as st

# We DO NOT import the base adk_level12_hitl agent here.
# Why? Because the base agent uses python `input()` in a while loop inside its callback.
# If we run that inside Streamlit, it will literally pause the Streamlit server thread forever
# waiting for terminal input that the user can't see!

# To implement HITL cleanly in the Streamlit UI for ADK, we must use the comparison 
# module that we already built specifically to support yield/generator interrupts for the UI.
from langchain_labs import adk_level12_comparison

def render():
    st.header("Level 12: Advanced Streaming & Interrupts (ADK via Generatots)")
    st.info("Concept: Because the native ADK `input()` loop blocks Streamlit, this UI uses the `adk_level12_comparison` method (generators) to achieve Human-in-the-Loop native to the browser.")
    
    if "messages_adkl12" not in st.session_state:
        st.session_state.messages_adkl12 = []
    if "adkl12_paused" not in st.session_state:
        st.session_state.adkl12_paused = False
        
    thread_id = st.text_input("Active Session (Thread ID):", value="adkl12_session_1")
    
    st.markdown("---")
    
    # Render chat history
    for msg in st.session_state.messages_adkl12:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            
    # Handle Paused State (Approval Buttons)
    if st.session_state.adkl12_paused:
        st.warning("⚠️ The ADK Agent wants to perform a high-stakes action. Do you approve?")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ Approve Action", key="adk_approve", use_container_width=True):
                with st.spinner("Resuming ADK chat execution..."):
                    result = adk_level12_comparison.approve_and_resume(thread_id, approved=True)
                    st.session_state.messages_adkl12.append({"role": "assistant", "content": f"*{result}*"})
                st.session_state.adkl12_paused = False
                st.rerun()
                
        with col2:
            if st.button("❌ Deny Action", key="adk_deny", use_container_width=True):
                with st.spinner("Rejecting and returning back to ADK agent..."):
                    result = adk_level12_comparison.approve_and_resume(thread_id, approved=False)
                    st.session_state.messages_adkl12.append({"role": "assistant", "content": f"*{result}*"})
                st.session_state.adkl12_paused = False
                st.rerun()
                
    # Chat Input (Only show if not paused)
    elif user_prompt := st.chat_input("Ask for a $50 refund on ORD-123..."):
        with st.chat_message("user"):
            st.markdown(user_prompt)
        st.session_state.messages_adkl12.append({"role": "user", "content": user_prompt})
        
        with st.chat_message("assistant"):
            generator = adk_level12_comparison.stream_agent_response(user_prompt, thread_id)
            
            def stream_data():
                for chunk in generator:
                    if isinstance(chunk, str):
                        yield chunk
                    else:
                        if chunk["is_interrupted"]:
                            st.session_state.adkl12_paused = True
                            tool_name = chunk["requested_tool"]["name"]
                            tool_args = chunk["requested_tool"]["args"]
                            st.session_state.messages_adkl12.append({"role": "assistant", "content": chunk["full_text"]})
                            st.session_state.messages_adkl12.append({"role": "assistant", "content": f"**[PAUSED] Native ADK Requested to run `{tool_name}` with `{tool_args}`**"})
                        else:
                            st.session_state.messages_adkl12.append({"role": "assistant", "content": chunk["full_text"]})
                            
            st.write_stream(stream_data)
            
            if st.session_state.adkl12_paused:
                st.rerun()

    st.markdown("---")
    if st.button("Clear History", key="adk_clear"):
        st.session_state.messages_adkl12 = []
        st.session_state.adkl12_paused = False
        st.rerun()
