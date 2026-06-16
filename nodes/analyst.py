"""
    Job description analyst node for LangGraph. 
    The correspond agent implementation is located at ./agents/analyst.py

    Things to notice: 
"""

from langgraph.prebuilt import create_react_agent 
from state import LadderState
from tools.file_tools import list_jds, read_jd, save_scored_jds, read_profile

analyst_agent = create_react_agent(
    model="claude-haiku-4-5-20251001",
    tools=[list_jds, read_jd, read_profile, save_scored_jds],
    prompt=(
        "You are a JD analyst. "
        "1. Call list_jds to get all JD file paths. "
        "2. Call read_profile to get the candidate profile. "
        "3. Call read_jd for each path. "
        "4. Score each JD 0-100 for fit against the profile. Include a path and 2-3 sentences of reasoning per JD. "
        "5. Call save_scored_jds with the ranked list sorted by score descending. Then stop."
    )
)

def analyst_node(state: LadderState) -> dict:
    """LangGraph node - scores and ranks all saved JDs against the candidate profile."""
    result = analyst_agent.invoke({
        "messages": [("user", "Analyse and score all saved JDs.")]
    })
    return {"messages": result["messages"]}