"""
LangChain Level 3: Custom Tools

ADK Equivalent: `def my_tool():` + `tools=[my_tool]` inside an Agent
LangChain Concept: `@tool` decorator + `llm.bind_tools()`

EXPLANATION OF LANGCHAIN CONCEPTS:
1. The @tool decorator:
   - In ADK, you just pass a normal Python function to the Agent.
   - In LangChain, you must decorate your function with `@tool`. 
   - This decorator tells LangChain to parse the function's docstring and type hints
     into a JSON Schema that the LLM can understand.
   - The docstring is critical: it becomes the prompt that tells the LLM *when* to use it.

2. bind_tools():
   - To give tools to an LLM in LangChain, you "bind" them.
   - `llm_with_tools = llm.bind_tools([get_weather, calculate])`
   - This creates a new version of the LLM that knows about these specific tools.

3. Tool Calls in Response:
   - When the LLM decides to use a tool, it DOES NOT execute the tool magically.
   - Instead, it returns an `AIMessage` where `response.tool_calls` is populated.
   - You (or an Agent framework like LangGraph) must read those tool calls, 
     execute the Python function, and pass the result *back* to the LLM.

In this script, we rebuild the "Smart Assistant" from ADK Level 3. We will show how
the LLM requests a tool call, and how we manually execute it.
"""

import os
from dotenv import load_dotenv

load_dotenv()

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage

# 1. Define Tools using the @tool decorator
# The docstring and type hints are REQUIRED for the LLM to know how to use it.
@tool
def get_weather(city: str) -> str:
    """Get the current weather for a specific city. 
    Use this whenever the user asks about the weather or temperature."""
    print(f"\n[🔧 EXECUTING TOOL] get_weather(city='{city}')")
    # In a real app, you'd call a weather API here.
    return f"The weather in {city} is sunny and 25°C."

@tool
def calculate(expression: str) -> str:
    """Evaluate a mathematical expression.
    Use this whenever you need to do math, addition, multiplication, etc.
    The expression must be a valid Python math string."""
    print(f"\n[🔧 EXECUTING TOOL] calculate(expression='{expression}')")
    try:
        # DO NOT DO THIS IN PRODUCTION (eval is unsafe). Overly simplistic for demonstration.
        result = eval(expression, {"__builtins__": {}})
        return str(result)
    except Exception as e:
        return f"Error calculating: {str(e)}"

def run_level(prompt: str):
    """Executes Level 3 logic for the Streamlit UI, yielding steps."""
    MODEL = os.getenv("MODEL", "gemini-2.5-flash")
    steps = []

    # 2. Initialize Model
    llm = ChatGoogleGenerativeAI(model=MODEL, temperature=0.0)

    # 3. Bind the tools to the LLM
    # This creates a new runnable that knows about our python functions
    tools = [get_weather, calculate]
    llm_with_tools = llm.bind_tools(tools)

    # 4. Ask a question that requires a tool
    steps.append({"type": "llm_request", "content": prompt})
    
    # Send the message to the tool-bound LLM
    messages = [HumanMessage(content=prompt)]
    response = llm_with_tools.invoke(messages)

    # 5. Check if the LLM decided to call tools
    if response.tool_calls:
        # 6. Execute the tools manually
        for tool_call in response.tool_calls:
            tool_name = tool_call["name"]
            tool_args = tool_call["args"]
            
            steps.append({
                "type": "tool_call", 
                "name": tool_name, 
                "args": tool_args
            })
            
            # Find the actual python function and execute it
            tool_mapping = {"get_weather": get_weather, "calculate": calculate}
            chosen_tool = tool_mapping.get(tool_name)
            
            if chosen_tool:
                # Execute it and get result
                result = chosen_tool.invoke(tool_args)
                steps.append({
                    "type": "tool_result", 
                    "result": result
                })
            else:
                 steps.append({
                    "type": "tool_result", 
                    "result": f"Tool {tool_name} not found."
                })
            
    else:
        steps.append({
            "type": "direct_answer",
            "content": response.content
        })
        
    return steps
