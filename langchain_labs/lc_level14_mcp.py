import os
import asyncio
from typing import List, Dict, Any
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_mcp import MCPToolkit
from langchain.agents import create_react_agent, AgentExecutor
from langchain_core.prompts import PromptTemplate
from mcp import StdioServerParameters

MODEL = os.getenv("MODEL", "gemini-2.5-flash")

def get_mcp_agent_executor():
    """Context manager style setup for LangChain MCP agent."""
    llm = ChatGoogleGenerativeAI(model=MODEL)
    
    server_params = StdioServerParameters(
        command="uv",
        args=["run", "mcp_server.py"],
        env=os.environ.copy()
    )
    
    # In a real Streamlit app, we'd handle the async lifecycle carefully.
    # For this lab, we use a helper to run the async setup.
    async def setup():
        toolkit = await MCPToolkit.from_stdio(server_params)
        tools = toolkit.get_tools()
        
        prompt = PromptTemplate.from_template(
            "You are a shopping assistant. Use tools to find products.\n"
            "Query: {input}\n\n"
            "Context: {agent_scratchpad}\n"
            "Action: one of [{tool_names}]\n"
            "Action Input: the input to the action\n"
            "Observation: the result of the action\n"
            "Final Answer: the final answer to the user"
        )
        
        agent = create_react_agent(llm, tools, prompt)
        return AgentExecutor(agent=agent, tools=tools, verbose=True)

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    return loop.run_until_complete(setup())

def run_level(query: str):
    """Entry point for Level 14 Streamlit UI."""
    executor = get_mcp_agent_executor()
    
    # Since we want to show the tool calls in the UI, we'll stream or capture the steps
    trace = []
    
    try:
        # Simple execution for the lab
        response = executor.invoke({"input": query})
        return {
            "success": True,
            "answer": response["output"],
            "trace": trace
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }
