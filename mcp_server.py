"""
MCP server - exposes web_search and scrape_page as MCP tools. 
Run this as a subprocess; the scraper node connects to it via stdio transport. 
"""
import asyncio
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types 

from tools.web_tools import web_search, scrape_page

app = Server("ladder-scraper-tools")

@app.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="web_search",
            description="Search for job listings matching the query. Returns a list of results with title, url and snippet.",
            inputSchema={
                "type":"object",
                "properties":{
                    "query": {"type": "string", "description": "Search query string"},
                    "limit": {"type": "integer", "description": "Max results", "default": 5},
                    "days_ago": {"type": "integer", "description": "Only results from last N days", "default": 7},
                },
                "required": ["query"],
            },
        ),
        types.Tool(
            name="scrape_page",
            description="Scrape the full job description text from a URL. Returns markdown content.",
            inputSchema={
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "URL to scrape"},                    
                },
                "required": ["url"],
            },
        ),
    ]

@app.call_tool()
async def call_tool(name: str, arguments: dict):
    if name == "web_search":
        result = web_search(**arguments)
        return [types.TextContent(type="text", text=str(result))]
    elif name == "scrape_pgae":
        result == scrape_page(**arguments)
        return [types.TextContent(type="text", text=result)]
    else:
        return ValueError(f"Unknown tool: {name}")

async def main():
    async with stdio_server() as (read_stream, write_stream): 
        await app.run(read_stream, write_stream, app.create_initialization_options())

if __name__ == "__main__":
    asyncio.run(main())
