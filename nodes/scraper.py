"""
    Scraper node - Phase 2 with MCP.
    Tools are now served from mcp_server.py via the MCP studio transport, 
    instead of being imported directly from tools/web_search.py
"""

import asyncio
import sys
import os
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent
from state import LadderState
from tools.file_tools import save_jd # save_jd stays as a direct tool

async def _run_scraper(search_query: str) -> dict:
    python = sys.executable # use the same venv Python
    server_path = os.path.join(os.path.dirname(__file__), "..", "mcp_server.py")

    client = MultiServerMCPClient(
        {
            "scraper-tools": {
                "command": python,
                "args": [server_path],
                "transport": "stdio",
            }
        }
    )
    mcp_tools = await client.get_tools()  # returns LangChain-compatible tool objects

    agent = create_react_agent(
        model="claude-haiku-4-5-20251001",
        tools=[*mcp_tools, save_jd],  # MCP tools + local save_jd tool
        prompt=(
            "You are a job scraping agent. Your job is:"
            "1. Call web_search once to find job listings."
            "2. Call scrape_page for each URL to get the full job description."
            "3. Call save_jd for each job to save the structured data."
            "4. Once all jobs are saved, stop. Do not repeat any steps."
        ),
    )
    result = await agent.ainvoke({
        "messages": [("user", search_query)]
    })
    return {"messages": result["messages"]}

def scraper_node(state: LadderState) -> dict: 
    """LangGraph node - spawns MCP server, runs scraper agent via MCP tools."""
    return asyncio.run(_run_scraper(state["search_query"]))