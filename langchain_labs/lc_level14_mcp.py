import os
import asyncio
from typing import List, Dict, Any
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_mcp import MCPToolkit
from langgraph.prebuilt import create_react_agent
from mcp import StdioServerParameters

MODEL = os.getenv("MODEL", "gemini-2.5-flash")

def get_mcp_agent():
    """Builds a LangGraph agent that can connect to the MCP server."""
    llm = ChatGoogleGenerativeAI(model=MODEL)
    
    server_params = StdioServerParameters(
        command="uv",
        args=["run", "mcp_server.py"],
        env=os.environ.copy()
    )
    
    # In a real Streamlit app, we'd handle the async lifecycle carefully.
    async def setup():
        toolkit = await MCPToolkit.from_stdio(server_params)
        tools = toolkit.get_tools()
        
        # We use the same pattern as Level 10 and Level 12
        app = create_react_agent(llm, tools)
        return app

    # Use a fresh event loop for the bridge
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import nest_asyncio
            nest_asyncio.apply()
            return loop.run_until_complete(setup())
        return asyncio.run(setup())
    except RuntimeError:
        return asyncio.run(setup())

# Global instance to avoid restarting the server process on every interaction
_global_mcp_agent = None

def run_level(query: str):
    """Entry point for Level 14 Streamlit UI."""
    global _global_mcp_agent
    if _global_mcp_agent is None:
        _global_mcp_agent = get_mcp_agent()
    
    try:
        response = _global_mcp_agent.invoke({"messages": [("user", query)]})
        # LangGraph returns the full state; we want the last message's content
        final_msg = response["messages"][-1]
        
        # Capture trace (simplified)
        trace = []
        for msg in response["messages"]:
             if hasattr(msg, "tool_calls") and msg.tool_calls:
                 for tc in msg.tool_calls:
                     trace.append(f"🔧 Tool Call: {tc['name']} with {tc['args']}")
        
        return {
            "success": True,
            "answer": final_msg.content,
            "trace": trace
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }
