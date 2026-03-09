"""
LangChain Level 4: Guardrails (Input & Output Validation)

ADK Equivalent: `before_model_callback` and `after_model_callback`
LangChain Concept: LCEL `RunnableLambda`

EXPLANATION:
In LangChain, the easiest way to implement guardrails is to insert custom python functions directly into your LCEL chain using `RunnableLambda` (or just letting LCEL auto-wrap your functions).

A guarded chain looks like:
input -> [Input Guardrail] -> prompt -> model -> parser -> [Output Guardrail] -> string

If an input guardrail fails, we can raise an exception to stop the chain.
Output guardrails can modify the generated text before returning it.
"""

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableLambda
import os
import re
from dotenv import load_dotenv

load_dotenv()

# --- Guardrail Functions ---

def input_guardrail(inputs: dict) -> dict:
    """Validates the input before it reaches the prompt."""
    query = inputs.get("query", "")
    
    # Block prompt injection attempts
    blocked_words = ["ignore", "jailbreak", "bypass", "pirate"]
    for word in blocked_words:
        if word in query.lower():
            raise ValueError(f"🛑 SECURITY ALERT: Blocked word '{word}' detected in input.")
            
    return inputs # Pass the unmodified inputs down the chain if safe

def output_guardrail(model_output: str) -> str:
    """Redacts PII from the model's output."""
    # Simple email redaction
    redacted = re.sub(
        r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
        '[EMAIL REDACTED]', model_output
    )
    return redacted

def run_level(query: str):
    """Executes Level 4 logic for the Streamlit UI."""
    MODEL = os.getenv("MODEL", "gemini-2.5-flash")
    llm = ChatGoogleGenerativeAI(model=MODEL, temperature=0.1)
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a helpful assistant. Provide the information requested."),
        ("human", "{query}")
    ])
    
    # Wrap our functions in RunnableLambda so they can be piped in LCEL
    safe_input = RunnableLambda(input_guardrail)
    safe_output = RunnableLambda(output_guardrail)
    parser = StrOutputParser()
    
    # The Guardrailed Chain
    # safe_input ensures the query is clean
    # prompt formats it
    # llm generates the response
    # parser extracts the string
    # safe_output redacts PII
    chain = safe_input | prompt | llm | parser | safe_output
    
    try:
        result = chain.invoke({"query": query})
        return {"success": True, "result": result}
    except ValueError as e:
        return {"success": False, "result": str(e)}

if __name__ == "__main__":
    print(run_level("What is your return policy? My email is dheer@example.com"))
