"""
LangChain Level 5: Observability & Callbacks

ADK Equivalent: `before_model_callback`, `after_model_callback`, `before_tool_callback`, etc.
LangChain Concept: `BaseCallbackHandler` and `LangSmith`

EXPLANATION:
In LangChain, you monitor execution using Callbacks. LangChain has a massive system
for this. You can define a class that inherits from `BaseCallbackHandler` and override
events like `on_llm_start`, `on_tool_start`, `on_chain_end`, etc.

Every method in LangChain (invoke, stream, batch) accepts a `callbacks=[]` argument
to attach these listeners.

*Note on LangSmith*: The modern, industry-standard way to do this is to use **LangSmith**.
If you set `os.environ["LANGCHAIN_TRACING_V2"] = "true"` and provide a `LANGCHAIN_API_KEY`,
LangChain automatically sends all this callback data to a beautiful web dashboard!
Because we don't have a LangSmith key configured right now, we will build a custom
local Callback Handler that prints to the console/UI, exactly like we did in ADK.
"""

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.tools import tool
import os
import time
from dotenv import load_dotenv

load_dotenv()

# --- Custom Callback Handler ---
class ADKStyleMonitor(BaseCallbackHandler):
    """A custom callback handler that mimics our ADK Level 5 monitor."""
    
    def __init__(self):
        self.logs = []
        self.start_times = {}

    def _log(self, message: str):
        self.logs.append(message)
        print(message)

    def on_llm_start(self, serialized: dict, prompts: list[str], **kwargs):
        """Runs before the LLM is called."""
        self.start_times["llm"] = time.time()
        self._log(f"🟢 [LLM_START] Sending request to model...")

    def on_llm_end(self, response, **kwargs):
        """Runs after the LLM returns a response."""
        elapsed = (time.time() - self.start_times.get("llm", time.time())) * 1000
        tokens = "Unknown"
        if response.llm_output and "token_usage" in response.llm_output:
             tokens = response.llm_output["token_usage"].get("total_tokens", "Unknown")
        self._log(f"🔴 [LLM_END] Received response. Took {elapsed:.1f}ms (Tokens: {tokens})")

    def on_tool_start(self, serialized: dict, input_str: str, **kwargs):
        """Runs before a tool executes."""
        tool_name = serialized.get("name", "unknown_tool")
        self._log(f"⚙️ [TOOL_START] Executing tool: '{tool_name}' with input: {input_str}")

    def on_tool_end(self, output: str, **kwargs):
        """Runs after a tool successfully executes."""
        self._log(f"✅ [TOOL_END] Tool returned: {output[:50]}...")

    def on_tool_error(self, error: Exception, **kwargs):
        """Runs if a tool throws an exception."""
        self._log(f"❌ [TOOL_ERROR] Tool failed: {str(error)}")

# --- Tools ---
@tool
def calculate_shipping(weight: float) -> str:
    """Calculates shipping cost based on weight in kg."""
    if weight <= 0:
        raise ValueError("Weight must be greater than 0.")
    cost = weight * 5.50
    return f"Shipping cost is ${cost:.2f}"

# --- Main Logic ---
def run_level(query: str):
    """Executes Level 5 logic and returns the logs for the Streamlit UI."""
    MODEL = os.getenv("MODEL", "gemini-2.5-flash")
    llm = ChatGoogleGenerativeAI(model=MODEL, temperature=0.1)
    
    # Bind the tool
    llm_with_tools = llm.bind_tools([calculate_shipping])
    
    # Initialize our custom monitor
    monitor = ADKStyleMonitor()
    
    # Create the prompt
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a shipping assistant. Use the calculate_shipping tool to answer queries."),
        ("human", "{query}")
    ])
    
    # Create the chain
    chain = prompt | llm_with_tools
    
    # Execute the chain, PASSING THE CALLBACK HANDLER
    # The monitor will automatically listen to all events triggered by this chain
    response = chain.invoke(
        {"query": query}, 
        config={"callbacks": [monitor]}
    )
    
    # If a tool was requested, we have to execute it manually (as learned in Level 3)
    # But we MUST pass the callback handler to the tool's invoke method as well!
    if response.tool_calls:
        for tool_call in response.tool_calls:
            if tool_call["name"] == "calculate_shipping":
                try:
                    # Notice we pass config={"callbacks": [monitor]} so the tool logs events!
                    tool_result = calculate_shipping.invoke(
                        tool_call["args"],
                        config={"callbacks": [monitor]}
                    )
                except Exception as e:
                    # The on_tool_error callback will automatically log this inside the invoke
                    pass
                    
    return {
        "response": response,
        "logs": monitor.logs
    }

if __name__ == "__main__":
    res = run_level("How much to ship a 10kg package?")
    print("\n--- FINAL LOGS ---")
    for log in res["logs"]:
        print(log)
