"""
LangChain Level 11: Observability (LangSmith)

ADK Equivalent: None (ADK relies on bare-metal printing or Cloud Logging)
LangChain Concept: `LangSmith` (LangChain's dedicated observability platform)

EXPLANATION:
When you build complex LangGraph agents (like our Level 10 Production Agent), 
it becomes extremely difficult to debug where things went wrong. 
- Why did the LLM choose that tool?
- What exact `{context}` was injected into the prompt by RAG?
- How long did the VectorStore take to answer?

LangSmith solves this by tracing EVERY single step of your LCEL chains and LangGraph nodes.

HOW TO USE IT:
LangSmith integration in LangChain requires NO code changes! 
It is entirely controlled by Environment Variables.
"""

import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

# 1. Load the environment variables
load_dotenv()

# We need to verify that LangSmith is actually configured in the environment
def verify_langsmith_config():
    """Checks if the necessary LangSmith environment variables are set."""
    is_tracing = os.getenv("LANGCHAIN_TRACING_V2") == "true"
    api_key = os.getenv("LANGCHAIN_API_KEY")
    project = os.getenv("LANGCHAIN_PROJECT")
    
    return {
        "is_tracing": is_tracing,
        "has_api_key": bool(api_key and len(api_key) > 10),
        "project": project
    }

def run_level(query: str):
    """
    Executes a simple LLM call that will automatically be traced to LangSmith
    IF the environment variables are correctly set.
    """
    status = verify_langsmith_config()
    
    if not status["is_tracing"] or not status["has_api_key"]:
        return {
            "success": False,
            "error": (
                "🛑 LangSmith is not configured!\n\n"
                "To enable tracing, you must add these to your `.env` file:\n"
                "1. `LANGCHAIN_TRACING_V2=true`\n"
                "2. `LANGCHAIN_API_KEY=lsv2_pt_your_key_here`\n"
                "3. `LANGCHAIN_PROJECT=ADK-Sample-Project`\n\n"
                "Get an API key for free at: [smith.langchain.com](https://smith.langchain.com/)"
            ),
            "status": status
        }
        
    try:
        # If LangSmith is configured, this single line of code is automatically 
        # caught by the LangSmith SDK in the background and sent to the dashboard!
        model = ChatGoogleGenerativeAI(model=os.getenv("MODEL", "gemini-2.5-flash"))
        
        # We invoke the model. The prompt, parameters, latency, and response are all traced.
        response = model.invoke(query)
        
        return {
            "success": True,
            "response": response.content,
            "status": status
        }
    except Exception as e:
         return {
            "success": False,
            "error": str(e),
            "status": status
        }

if __name__ == "__main__":
    print("🤖 LangSmith Tester\n")
    result = run_level("Tell me a 1-sentence joke about observability.")
    
    if result["success"]:
        print(f"✅ Success! Response:\n{result['response']}\n")
        print(f"Go check your LangSmith Dashboard under project: {result['status']['project']}")
    else:
        print(f"❌ Error:\n{result['error']}")
