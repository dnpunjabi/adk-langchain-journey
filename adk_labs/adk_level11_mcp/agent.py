import os
import sys
import asyncio
from google.adk.agents import Agent
from google.genai import types
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

MODEL = os.getenv("MODEL", "gemini-2.5-flash")

# This agent demonstrates connecting to an external MCP Server
# Note: For Streamlit, we manually bridge the tool call because 
# ADK tools are usually synchronous or managed by Runner.

async def call_mcp_tool(tool_name: str, arguments: dict):
    """Bridge function to call the local MCP server."""
    server_params = StdioServerParameters(
        command="uv",
        args=["run", "mcp_server.py"],
        env=os.environ.copy()
    )
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool(tool_name, arguments)
            return result.content[0].text if result.content else "No result"

def search_products_mcp(query: str) -> str:
    """Standardized tool discovered via Model Context Protocol.
    
    Args:
        query: The search term for products.
    """
    # Since ADK tools in this version are blocking, we run the async client in a loop
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
    return loop.run_until_complete(call_mcp_tool("search_products", {"query": query}))

root_agent = Agent(
    name="adk_level11_mcp",
    model=MODEL,
    description="An agent that uses Model Context Protocol (MCP) to access external product data.",
    instruction=(
        "You are an Acme Store Assistant with access to a live Product Server via MCP.\n"
        "- Use the search_products_mcp tool to find product availability, price, and category.\n"
        "- If a user asks about what we sell or specific prices, always search the MCP server first.\n"
        "- Be professional and helpful."
    ),
    tools=[search_products_mcp]
)
