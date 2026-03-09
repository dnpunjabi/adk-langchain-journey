"""
LangChain Level 1: Single Agent Basics

ADK Equivalent: `Agent(model=...)`
LangChain Concept: `ChatGoogleGenerativeAI` 

EXPLANATION OF LANGCHAIN CONCEPTS:
1. LLM vs ChatModel:
   - Early text models took a string and returned a string (LLMs).
   - Modern models (like Gemini) take a list of Chat Messages and return a message.
   - LangChain handles this with distinct classes. For Gemini, we use 
     `ChatGoogleGenerativeAI` which is a ChatModel.

2. invoke():
   - Every core LangChain component implements the "Runnable" interface.
   - This means they all use the `.invoke()` method to run them.
   - You pass your input into `.invoke()` and get the response back.

3. Messages:
   - LangChain represents conversation using specific message classes:
     - `HumanMessage`: What the user says
     - `SystemMessage`: The instructions for the AI
     - `AIMessage`: What the AI says back

In this script, we do the absolute minimum: connect to Gemini and ask a question.
"""

import os
from dotenv import load_dotenv

# 1. Load the environment variables (contains GEMINI_API_KEY)
load_dotenv()

# 2. Import the LangChain Google GenAI integration class
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage

def run_level(prompt_text: str):
    """Executes Level 1 logic for the Streamlit UI."""
    MODEL = os.getenv("MODEL", "gemini-2.5-flash")

    # Initialize the Chat Model
    llm = ChatGoogleGenerativeAI(
        model=MODEL,
        temperature=0.7,
    )

    # Create our message
    messages = [
        HumanMessage(content=prompt_text)
    ]

    # Invoke the model
    response = llm.invoke(messages)
    
    return response
