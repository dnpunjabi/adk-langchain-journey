import os
import asyncio
from typing import List, Dict, Any
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_mcp import MCPToolkit
from langgraph.prebuilt import create_react_agent
from contextlib import AsyncExitStack
from mcp.client.stdio import stdio_client
from mcp import ClientSession, StdioServerParameters

MODEL = os.getenv("MODEL", "gemini-2.5-flash")

# Global state to keep the tool server connection alive
_global_mcp_agent = None
_mcp_exit_stack = None

async def setup_persistent_mcp():
    """Builds a LangGraph agent and keeps the connection open using ExitStack."""
    global _mcp_exit_stack
    llm = ChatGoogleGenerativeAI(model=MODEL)
    
    server_params = StdioServerParameters(
        command="uv",
        args=["run", "mcp_server.py"],
        env=os.environ.copy()
    )
    
    _mcp_exit_stack = AsyncExitStack()
    
    # 1. Connect to the server via stdio
    read, write = await _mcp_exit_stack.enter_async_context(stdio_client(server_params))
    
    # 2. Start the MCP Client Session
    session = await _mcp_exit_stack.enter_async_context(ClientSession(read, write))
    
    # 3. Initialize the session (required by MCP spec)
    await session.initialize()
    
    # 4. Create the LangChain toolkit
    toolkit = MCPToolkit(session=session)
    await toolkit.initialize()
    
    tools = toolkit.get_tools()
    
    # 5. Compile the agent graph
    app = create_react_agent(llm, tools)
    return app

def get_mcp_agent():
    """Initializes the persistent agent using the correct asyncio loop."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import nest_asyncio
            nest_asyncio.apply()
            return loop.run_until_complete(setup_persistent_mcp())
        return asyncio.run(setup_persistent_mcp())
    except RuntimeError:
        return asyncio.run(setup_persistent_mcp())

# Global instance to avoid restarting the server process on every interaction
_global_mcp_agent = None

def run_level(query: str):
    """Entry point for Level 14 Streamlit UI."""
    global _global_mcp_agent
    if _global_mcp_agent is None:
        _global_mcp_agent = get_mcp_agent()
    
    async def run_query():
        return await _global_mcp_agent.ainvoke({"messages": [("user", query)]})
    
    try:
        loop = asyncio.get_event_loop()
        response = loop.run_until_complete(run_query())
        
        # LangGraph returns the full state; we want the last message's content
        final_msg = response["messages"][-1]
        
        # Capture trace
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
