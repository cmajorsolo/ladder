"""
    Scraper node for LangGraph. The correspond agent implementation is located at ./agents/scraper.py

    Phase 1 used a manual while True ReAct loop with JSON tool schemas. 
    Phase 2 replaces all of that with create_react_agent - LangGraph handles the loop, 
    tool dispatch, and message passing automatically. 

    Things to notice: 
    1. TOOLS are now plain Python functions, not JSON schemas. 
       Line 25: LangGraph inspects the function's type hints and docstring to build the schema. 
       This means your tool functions need clear docstrings — check web_tools.py and file_tools.py and add them if missing.
    2. The node returns only what changed and LangGraph merges it automatically. @line 42
    3. create_react_agent is the while loop. 
       Every iteration of the ReAct loop you wrote manually in agents/scraper.py is now handled internally by create_react_agent.
"""

from langgraph.prebuilt import create_react_agent
from state import LadderState
from tools.web_tools import web_search, scrape_page 
from tools.file_tools import save_jd

# create_react_agent replaces: 
# - the TOOLS list (it reads function signatures instead)
# - the while True loop
# - the if tool_name == "web_search" dispatch block
scraper_agent = create_react_agent(
    model="claude-haiku-4-5-20251001",    
    tools=[web_search, scrape_page, save_jd],
    prompt=(
        "You are a job scraping agent. Your job is: "
        "1. Call web_search once to find job listings. "
        "2. Call scrape_page for each URL to get the full job description. "
        "3. Call save_jd for each job to save the structured data. "
        "4. Once all jobs are saved, stop. Do not repeat any steps."
    )
)

def scraper_node(state: LadderState) -> dict:
    """LangGraph node - takes state, runs the scrapper agent, returns updated state."""
    result = scraper_agent.invoke({
        "messages": [("user", state["search_query"])]
    })
    #  Return only what changed - LangGraph merges this into the full state
    return {"messages": result["messages"]}