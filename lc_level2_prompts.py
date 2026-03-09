"""
LangChain Level 2: Prompt Engineering & LCEL

ADK Equivalent: `instruction` and `global_instruction`
LangChain Concept: `ChatPromptTemplate` and `LCEL` (LangChain Expression Language)

EXPLANATION OF LANGCHAIN CONCEPTS:
1. Prompts vs Templates:
   - Hardcoding strings (Level 1) is bad for dynamic apps.
   - `ChatPromptTemplate` lets you define structural blueprints with {variables}.
   - It also handles the complex formatting of System/Human/AI messages automatically.

2. LCEL (LangChain Expression Language):
   - This is LangChain's "secret sauce". The `|` (pipe) operator.
   - It allows you to chain Runnables together, passing the output of the 
     left side seamlessly as the input to the right side.
   - Example constraint: `chain = prompt | model | parser`
     - Step 1: `prompt` formats the variables into messages.
     - Step 2: `model` takes those messages and returns an AIMessage.
     - Step 3: `parser` takes the AIMessage and extracts just the raw text.

In this script, we rebuild the "HR Assistant" from ADK Level 2 using these concepts.
"""

import os
from dotenv import load_dotenv

load_dotenv()

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

def run_level(topic: str, urgency: str):
    """Executes Level 2 logic for the Streamlit UI."""
    MODEL = os.getenv("MODEL", "gemini-2.5-flash")

    # 1. Initialize the Model
    llm = ChatGoogleGenerativeAI(model=MODEL, temperature=0.2)

    # 2. Define the ChatPromptTemplate
    # This replaces ADK's `global_instruction` (System) and user input (Human)
    # The {topic} and {urgency} are variables we inject later.
    prompt_template = ChatPromptTemplate.from_messages([
        ("system", "You are an expert HR policy assistant for Acme Corp. "
                   "Only answer HR questions. If the user asks about something else, "
                   "politely redirect them. Be concise."),
        ("human", "Question: {topic}\nPriority Level: {urgency}"),
    ])

    # 3. Create an Output Parser
    # The model returns an AIMessage object. This parser extracts just the string content,
    # so we don't have to do `response.content` manually.
    parser = StrOutputParser()

    # 4. Build the LCEL Chain uses the `|` operator
    # Data flow: dict_input -> prompt -> formatted_messages -> llm -> AIMessage -> parser -> string
    chain = prompt_template | llm | parser

    # 5. Run the chain with inputs
    response = chain.invoke({
        "topic": topic,
        "urgency": urgency
    })
    
    return response
